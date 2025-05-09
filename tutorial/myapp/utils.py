from datetime import datetime
from io import BytesIO
import json
import os
import re
import collections
import shutil
import zipfile

from .models import ZippedFolder
from django.core.files.base import ContentFile

# Unterstützte Datentypen in SQLite
DATATYPE_MAP = {
    'int': 'INTEGER',
    'integer': 'INTEGER',
    'string': 'TEXT',
    'float': 'REAL',
    'double': 'REAL',
    'bool': 'BOOLEAN',
    # Weitere Typen können bei Bedarf ergänzt werden
}

def parse_attribute(attr_str):
    """Zerlegt ein Attribut in Spaltenname und Datentyp"""
    if ':' in attr_str:
        name, dtype = [s.strip() for s in attr_str.split(':', 1)]
    else:
        parts = attr_str.strip().split(' ', 1)
        dtype, name = parts if len(parts) == 2 else (parts[0], parts[0])
    return name, DATATYPE_MAP.get(dtype.lower(), dtype.upper())


def extract_tables(data):
    elements = data["model"]["elements"]
    relationships = data["model"]["relationships"]

    # Filter for Class (tables) and ClassAttribute
    class_elements = {k: v for k, v in elements.items() if v["type"] == "Class"}
    attributes = {k: v for k, v in elements.items() if v["type"] == "ClassAttribute"}

    # Gather unidirectional relationships: source -> [(role, target)]
    foreign_keys_map = {}
    for rel in relationships.values():
        if rel["type"] == "ClassUnidirectional":
            source = rel["source"]["element"]
            target = rel["target"]["element"]
            role = rel["target"]["role"] + rel["source"]["role"]
            foreign_keys_map.setdefault(source, []).append((role, target))

        if rel["type"] == "ClassBidirectional":
            source = rel["source"]["element"]
            target = rel["target"]["element"]
            role = rel["target"]["role"] + rel["source"]["role"]

            class_elements[role+"_mn"] = {
                "id": role+"_mn",
                "name": role,
                "type": "Class",
                "attributes": []
            }
            
            foreign_keys_map.setdefault(role+"_mn", []).append((class_elements[target]["name"].lower()+'_id', target))
            foreign_keys_map.setdefault(role+"_mn", []).append((class_elements[source]["name"].lower()+'_id', source))

    # Identify each class's PK from its first attribute
    pk_map = {}
    for class_id, class_data in class_elements.items():
        attr_ids = class_data.get("attributes", [])
        if attr_ids:
            first_attr = attributes[attr_ids[0]]
            pk_name, pk_type = parse_attribute(first_attr["name"])
            pk_map[class_id] = (pk_name, pk_type)
        elif class_id.endswith("_mn"):
            pk1 = foreign_keys_map[class_id][0][0]
            pk2 = foreign_keys_map[class_id][1][0]
            pk_name = pk1 + "," + pk2
            pk_map[class_id] = (pk_name, "")

    # Build adjacency list for topological sort, so references come after the referenced tables
    # Edge: if A references B, then A depends on B
    adjacency_list = collections.defaultdict(list)
    in_degree = {cid: 0 for cid in class_elements}

    for cid, fk_list in foreign_keys_map.items():
        for _, target_id in fk_list:
            adjacency_list[target_id].append(cid)
            in_degree[cid] += 1

    # Topological sort
    queue = collections.deque(cid for cid, deg in in_degree.items() if deg == 0)
    sorted_ids = []
    while queue:
        node = queue.popleft()
        sorted_ids.append(node)
        for neighbor in adjacency_list[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Generate SQL in topological order
    sql_statements = []
    for class_id in sorted_ids:
        class_data = class_elements[class_id]
        class_name = class_data["name"]
        attr_ids = class_data.get("attributes", [])
        attr_defs = []

        # Regular columns (including PK)
        for i, attr_id in enumerate(attr_ids):
            attr = attributes[attr_id]
            col_name, col_type = parse_attribute(attr["name"])
            attr_defs.append((col_name, col_type))

        # Foreign-key columns with the same type as the referenced table's PK
        fk_list = foreign_keys_map.get(class_id, [])
        fk_constraints = []
        for role, target_id in fk_list:
            target_pk_name, target_pk_type = pk_map.get(target_id, ("id", "INTEGER"))
            attr_defs.append((role, target_pk_type))
            target_name = class_elements[target_id]["name"]
            fk_constraints.append(
                f'FOREIGN KEY("{role}") REFERENCES "{target_name}"("{target_pk_name}") '
                f'ON UPDATE CASCADE ON DELETE SET NULL'
            )

        # Build CREATE TABLE statement
        lines = [f'CREATE TABLE "{class_name}" (']
        for col_name, col_type in attr_defs:
            lines.append(f'  "{col_name}" {col_type},')
        
            
        pk_name, pk_type = pk_map.get(class_id, (None, None))
        
        # Add foreign-key constraints
        for constraint in fk_constraints:
            lines.append(f'  {constraint},')
        if pk_name:
            lines.append("  PRIMARY KEY(\"" + pk_name.replace(",", '","') + "\"),")
        if lines[-1].endswith(','):
            lines[-1] = lines[-1][:-1]
        lines.append(');')
        sql_statements.append('\n'.join(lines))

    return '\n'.join(sql_statements)


def format_sql(sql: str) -> str:
    # Normalize whitespace
    sql = re.sub(r'\s+', ' ', sql).strip()

    # Keywords that should start on a new line (with optional indentation)
    newline_keywords = [
        r'\bSELECT\b', r'\bFROM\b', r'\bWHERE\b', r'\bGROUP BY\b', r'\bHAVING\b',
        r'\bORDER BY\b', r'\bLIMIT\b', r'\bOFFSET\b', r'\bJOIN\b', r'\bINNER JOIN\b',
        r'\bLEFT JOIN\b', r'\bRIGHT JOIN\b', r'\bFULL JOIN\b', r'\bOUTER JOIN\b',
        r'\bON\b', r'\bUNION\b', r'\bVALUES\b', r'\bSET\b', r'\bAND\b', r'\bOR\b',
        r'\bCREATE\b',r'\bFOREIGN\b',r'\bPRIMARY\b'
    ]

    # Keywords that should be followed by a tab indentation
    indent_keywords = [r'\bAND\b', r'\bOR\b', r'\bON\b']

    # Add line breaks before main keywords
    for kw in newline_keywords:
        sql = re.sub(f'(?i) {kw} ', lambda m: f'\n{m.group(0).strip()} ', sql)

    # Add tabs before indented keywords
    for kw in indent_keywords:
        sql = re.sub(f'(?i)^({kw})', r'\t\1', sql, flags=re.MULTILINE)

    return sql.strip()



def get_user_directory(username):
    if username.endswith('_admin'):
        username = username[:-6]
    return f"user_databases/{username}/"



def zip_and_save_directory(directory_path:str, delete:bool=True, storeToDB:bool=False):
    # Create a zip file in memory
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                abs_path = os.path.join(root, file)
                relative_path = os.path.relpath(abs_path, start=directory_path)
                zipf.write(abs_path, arcname=relative_path)
    memory_file.seek(0)

    # Save to model
    if(storeToDB):
        zipped = ZippedFolder(name=directory_path)
        zipped.zip_file.save(f"{directory_path}export.zip", ContentFile(memory_file.read()))
        zipped.save()

    if delete:
        try:
            if os.path.exists(directory_path):
                shutil.rmtree(directory_path) 
        except Exception as e:
            print(f"Error removing directory: {e}")
    
    return ContentFile(memory_file.read())

def restore_zip_to_directory(target_directory):
    try:
        # Fetch the zip entry from the DB
        zipped = ZippedFolder.objects.get(pk=target_directory)
        zip_path = zipped.zip_file.path

        if os.path.exists(target_directory):
            shutil.rmtree(target_directory)  # Remove existing directory if it exists

        # Ensure target directory exists
        os.makedirs(target_directory, exist_ok=True)

        # Extract zip contents
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_directory)
        os.remove(zip_path)  # Remove the zip file after extraction

        return True
    except ZippedFolder.DoesNotExist:
        print("Zip record not found in database.")
        return False
    except Exception as e:
        print(f"Error during restoration: {e}")
        return False
    

def get_directory_tree_with_sizes(directory):
    tree = []

    sum_size = 0
    last = ''

    for root, dirs, files in os.walk(directory):
        #dirs.append(directory)
        for name in dirs:
            dir_path = os.path.join(root, name)
            size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, _, filenames in os.walk(dir_path)
                for filename in filenames
            )
            sum_size += size
            last_edited = datetime.fromtimestamp(os.path.getmtime(dir_path)).strftime('%Y-%m-%d %H:%M')
            if last_edited > last:
                last = last_edited
            size_kb = str(round(size / 1000, 1)) +' kB' 
            tree.append({'type': 'directory', 'name': name, 'size': size_kb, 'last_modified': last_edited})
    
    tree.insert(0,{'type': 'directory', 'name': 'SUMME', 'size': str(round(sum_size / 1000000, 1))+' MB', 'last_modified': last})
    #tree.sort()
        #for name in files:
        #    file_path = os.path.join(root, name)
        #    size = os.path.getsize(file_path)
        #    last_edited = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        #    size_kb = round(size / 1024, 2)
        #    tree.append({'type': 'file', 'name': name, 'size': size_kb, 'last_modified': last_edited})
    return tree