import collections

# Unterstützte Datentypen in SQLite
DATATYPE_MAP = {
    'int': 'INTEGER',
    'integer': 'INTEGER',
    'ganzzahl': 'INTEGER',
    'text': 'TEXT',
    'zeichenkette': 'TEXT',
    'varchar': 'TEXT',
    'string': 'TEXT',
    'float': 'REAL',
    'kommazahl': 'REAL',
    'double': 'REAL',
    'bool': 'BOOLEAN',
    'boolean': 'BOOLEAN',
    'wahrheitswert': 'BOOLEAN',
    # Weitere Typen können bei Bedarf ergänzt werden
}


class ModelAnalyzer:
    """Analyzes and organizes model data for SQL generation."""

    def __init__(self, data: dict):
        """Parse the model data structure."""
        self.class_elements, self.attributes, self.foreign_keys_map, self.pk_map = self._parse_model(data)

    def _parse_model(self, data: dict) -> tuple:
        """Extract classes, attributes, relationships, and primary keys from model data."""
        if "model" in data:
            data = data["model"]

        class_elements = {}
        attributes = {}

        for element in data["nodes"]:
            if element["type"].lower() == "class":
                class_elements[element["id"]] = element
                attrs = element['data']['attributes']
                for attr in attrs:
                    attributes[attr['id']] = attr

        foreign_keys_map, class_elements = self._build_relationships(data, class_elements)
        pk_map = self._extract_primary_keys(class_elements, attributes, foreign_keys_map)

        return class_elements, attributes, foreign_keys_map, pk_map

    def _build_relationships(self, data: dict, class_elements: dict) -> tuple:
        """Process all relationships (uni and bidirectional)."""
        foreign_keys_map = {}
        try:
            for rel in data["edges"]:
                try:
                    if rel["type"] == "ClassUnidirectional":
                        foreign_keys_map = self._process_uni_rel(rel, foreign_keys_map)
                    elif rel["type"] == "ClassBidirectional":
                        foreign_keys_map, class_elements = self._process_bi_rel(rel, foreign_keys_map, class_elements)
                except Exception as e:
                    print(f"Error in relationship processing: {e}")
        except Exception as e:
            print(f"Error in _build_relationships: {e}")
        return foreign_keys_map, class_elements

    def _process_uni_rel(self, relation: dict, foreign_keys_map: dict) -> dict:
        """Process unidirectional relationship."""
        try:
            source = relation["source"]
            target = relation["target"]
            role = self._extract_role(relation)
            foreign_keys_map.setdefault(source, []).append((role, target))
        except Exception as e:
            print(f"Error in _process_uni_rel: {e}")
        return foreign_keys_map

    def _process_bi_rel(self, relation: dict, foreign_keys_map: dict, class_elements: dict) -> tuple:
        """Process bidirectional relationship by creating junction table."""
        try:
            source = relation["source"]
            target = relation["target"]
            role = self._extract_role(relation)

            # Create junction table
            mn_id = role + "_mn"
            class_elements[mn_id] = {
                "id": mn_id,
                "name": role,
                "type": "Class",
                "data": {
                    "name": role,
                    "attributes": [],
                },
            }
            foreign_keys_map.setdefault(mn_id, []).append(
                (class_elements[target]['data']["name"].lower() + '_id', target)
            )
            foreign_keys_map.setdefault(mn_id, []).append(
                (class_elements[source]['data']["name"].lower() + '_id', source)
            )
        except Exception as e:
            print(f"Error in _process_bi_rel: {e}")

        return foreign_keys_map, class_elements

    @staticmethod
    def _extract_role(relation: dict) -> str:
        """Extract role name from relationship."""
        role = ''
        if 'targetRole' in relation['data']:
            role += relation["data"]["targetRole"]
        if 'sourceRole' in relation['data']:
            role += relation["data"]["sourceRole"]
        return role

    def _extract_primary_keys(self, class_elements: dict, attributes: dict, foreign_keys_map: dict) -> dict:
        """Identify primary keys for each class."""
        pk_map = {}
        errors = []

        for class_id, class_data in class_elements.items():
            try:
                attr_list = class_data.get("data", {}).get("attributes", [])

                if attr_list:
                    first_attr = self._get_attribute(attr_list[0], attributes)
                    if first_attr:
                        pk_name, pk_type = parse_attribute(first_attr.get("name", "id"))
                        pk_map[class_id] = (pk_name, pk_type)
                elif class_id.endswith("_mn"):
                    # Junction table: composite primary key
                    pk1 = foreign_keys_map[class_id][0][0]
                    pk2 = foreign_keys_map[class_id][1][0]
                    pk_map[class_id] = (f"{pk1},{pk2}", "")
            except Exception as e:
                errors.append(f"class_id={class_id}: {e}")

        if errors:
            raise ValueError(
                "Errors encountered during primary key extraction: " + "; ".join(errors)
            )
        return pk_map

    @staticmethod
    def _get_attribute(attr_entry, attributes: dict) -> dict:
        """Get attribute dict from entry or lookup."""

        if isinstance(attr_entry, dict):
            return attr_entry
        elif attributes.get(attr_entry):
            return attributes[attr_entry]
        else: 
            return {}
class SQLGenerator:
    """Generates SQL CREATE TABLE statements from model data."""

    def __init__(self, analyzer: ModelAnalyzer):
        """Initialize with parsed model data."""
        self.class_elements = analyzer.class_elements
        self.attributes = analyzer.attributes
        self.foreign_keys_map = analyzer.foreign_keys_map
        self.pk_map = analyzer.pk_map

    def generate(self) -> str:
        """Generate complete SQL schema with proper table ordering."""
        sorted_ids = self._topological_sort()
        sql_statements = self._build_create_statements(sorted_ids)
        return '\n'.join(sql_statements)

    def _topological_sort(self) -> list:
        """Order tables by dependency (dependencies first)."""
        adjacency_list = collections.defaultdict(list)
        in_degree = dict.fromkeys(self.class_elements, 0)

        for cid, fk_list in self.foreign_keys_map.items():
            for _, target_id in fk_list:
                try:
                    adjacency_list[target_id].append(cid)
                    in_degree[cid] += 1
                except Exception as e:
                    print(f"Error building adjacency list: {e}")

        return self._kahn_sort(in_degree, adjacency_list)

    @staticmethod
    def _kahn_sort(in_degree: dict, adjacency_list: dict) -> list:
        """Kahn's algorithm for topological sorting."""
        queue = collections.deque(cid for cid, deg in in_degree.items() if deg == 0)
        sorted_ids = []
        
        while queue:
            node = queue.popleft()
            sorted_ids.append(node)
            for neighbor in adjacency_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        return sorted_ids

    def _build_create_statements(self, sorted_ids: list) -> list:
        """Build CREATE TABLE statements for all classes in order."""
        statements = []
        for class_id in sorted_ids:
            try:
                class_name, attr_defs = self._gather_attributes(class_id)
                fk_constraints = self._gather_fk_constraints(class_id, attr_defs)
                statement = self._compose_create_table(class_name, attr_defs, fk_constraints, class_id)
                statements.append(statement)
            except Exception as e:
                print(f"Error building statement for {class_id}: {e}")
        return statements

    def _gather_attributes(self, class_id: str) -> tuple:
        """Collect class name and attribute definitions."""
        try:
            class_data = self.class_elements[class_id]['data']
            class_name = class_data["name"]
            attr_ids = class_data.get("attributes", [])
            attr_defs = []

            for attr_id in attr_ids:
                attr = attr_id if isinstance(attr_id, dict) else self.attributes.get(attr_id)
                if attr:
                    col_name, col_type = parse_attribute(attr.get("name", ""))
                    attr_defs.append((col_name, col_type))
        except Exception as e:
            print(f"Error gathering attributes: {e}")
            class_name, attr_defs = "", []

        return class_name, attr_defs

    def _gather_fk_constraints(self, class_id: str, attr_defs: list) -> list:
        """Build foreign key constraint statements."""
        fk_list = self.foreign_keys_map.get(class_id, [])
        constraints = []

        for role, target_id in fk_list:
            try:
                target_pk_name, target_pk_type = self.pk_map.get(target_id, ("id", "INTEGER"))
                attr_defs.append((role, target_pk_type))
                target_name = self.class_elements[target_id]['data']["name"]
                constraints.append(
                    f'FOREIGN KEY("{role}") REFERENCES "{target_name}"("{target_pk_name}") '
                    f'ON UPDATE CASCADE ON DELETE SET NULL'
                )
            except Exception as e:
                print(f"Error building FK constraint: {e}")
        return constraints

    def _compose_create_table(self, class_name: str, attr_defs: list, fk_constraints: list, class_id: str) -> str:
        """Compose complete CREATE TABLE statement."""
        safe_name = class_name.replace(" ", "")
        lines = [f'CREATE TABLE "{safe_name}" (']

        pk_name, pk_type = self.pk_map.get(class_id, (None, None))

        for col_name, col_type in attr_defs:
            try:
                safe_col = col_name.replace(" ", "")
                if pk_name and col_name == pk_name:
                    if pk_type.lower() == 'auto':
                        lines.append(f'  "{safe_col}" INTEGER PRIMARY KEY AUTOINCREMENT,')
                    else:
                        lines.append(f'  "{safe_col}" {col_type} PRIMARY KEY,')
                else:
                    lines.append(f'  "{safe_col}" {col_type},')
            except Exception as e:
                print(f"Error composing column: {e}")

        for constraint in fk_constraints:
            lines.append(f'  {constraint},')

        if lines[-1].endswith(','):
            lines[-1] = lines[-1][:-1]
        lines.append(');')

        return '\n'.join(lines)


def extract_tables(data: dict) -> str:
    """Convert JSON model to SQL CREATE TABLE statements."""
    try:
        analyzer = ModelAnalyzer(data)
        generator = SQLGenerator(analyzer)
        return generator.generate()
    except Exception as e:
        print(f"Error in extract_tables: {e}")
        raise


def parse_attribute(attr_str: str) -> tuple:
    """
    Parse attribute string into column name and SQL data type.
    
    Supports formats: "name:type" or "type name"
    """
    if ':' in attr_str:
        name, dtype = [s.strip() for s in attr_str.split(':', 1)]
    else:
        parts = attr_str.strip().split(' ', 1)
        dtype, name = parts if len(parts) == 2 else (parts[0], parts[0])
    return name, DATATYPE_MAP.get(dtype.lower(), dtype.upper())
