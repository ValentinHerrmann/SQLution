import json
import re

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

    class_elements = {
        k: v for k, v in elements.items() if v["type"] == "Class"
    }
    attributes = {
        k: v for k, v in elements.items() if v["type"] == "ClassAttribute"
    }

    # Beziehungen analysieren
    foreign_keys = {}
    for rel in relationships.values():
        if rel["type"] == "ClassUnidirectional":
            source = rel["source"]["element"]
            target = rel["target"]["element"]
            role = rel["target"]["role"]
            foreign_keys.setdefault(source, []).append((role, target))

    sql_statements = []

    for class_id, class_data in class_elements.items():
        class_name = class_data["name"]
        attr_ids = class_data.get("attributes", [])
        attr_defs = []
        pk = None

        for i, attr_id in enumerate(attr_ids):
            attr = attributes[attr_id]
            col_name, col_type = parse_attribute(attr["name"])
            if i == 0:
                pk = col_name
            attr_defs.append((col_name, col_type))

        lines = [f'CREATE TABLE "{class_name}" (']
        for col_name, col_type in attr_defs:
            lines.append(f'\t"{col_name}"\t{col_type},')

        # Fremdschlüssel
        for role, target_id in foreign_keys.get(class_id, []):
            target_class = class_elements[target_id]["name"]
            lines.append(f'\tFOREIGN KEY("{role}") REFERENCES "{target_class}"("id"),')

        lines.append(f'\tPRIMARY KEY("{pk}")')
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
        r'\bON\b', r'\bUNION\b', r'\bVALUES\b', r'\bSET\b', r'\bAND\b', r'\bOR\b'
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