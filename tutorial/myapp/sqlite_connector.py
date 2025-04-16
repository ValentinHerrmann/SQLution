import sqlite3
import os
from .models import DatabaseModel
import re
from html import escape

def delete_db(username:str):
    dbname = get_db_name(username)
    if os.path.exists(dbname):
        os.remove(dbname)
        print(f"Database {dbname} deleted.")
    else:
        print(f"Database {dbname} does not exist.")

def get_db_name(username:str):
    if username is None or username == '':
        username = 'anonymous'
    os.makedirs('user_databases', exist_ok=True)
    dbname = "user_databases/" + username + ".db"
    print(dbname)
    return dbname

def create_db(sql:str, username:str):
    dbname = get_db_name(username)
    delete_db(username)  # Delete the old database if it exists

    with sqlite3.connect(dbname) as con:
        cur = con.cursor()
        for s in sql.split(';'):
            if s.strip() == '':
                continue
            try:
                cur.execute(s)
            except sqlite3.Error as e:
                print(f"SQL error: {e}")
        con.commit()
    with open(dbname, 'rb') as file:
        binary_data = file.read()
        return binary_data
    return None

def runSql(sql:str, username:str):
    dbname = get_db_name(username)
    with sqlite3.connect(dbname) as con:
        cur = con.cursor()
        for s in sql.split(';'):
            if s.strip() == '':
                continue
            try:
                cur.execute(s)
            except sqlite3.Error as e:
                print(f"SQL error: {e}")
        con.commit()
    return cur


def parse_table_schema(create_sql):
    """Parst CREATE TABLE SQL und extrahiert Spalten, Primär- und Fremdschlüssel."""
    columns = []
    primary_keys = set()
    foreign_keys = set()

    # Extrahiere Definitionen innerhalb der Klammern
    match = re.search(r'\((.*)\)', create_sql, re.DOTALL)
    if not match:
        return columns, primary_keys, foreign_keys
    body = match.group(1)

    # Zerlege Einträge durch Kommas, ohne Kommas innerhalb von Klammern zu trennen
    parts = re.split(r',\s*(?![^()]*\))', body)

    for part in parts:
        part = part.strip()

        # Spaltendefinition (keine Constraints)
        col_match = re.match(r'^"?(\w+)"?\s+([\w()]+)', part)
        if col_match and not part.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "CONSTRAINT")):
            col_name, col_type = col_match.groups()
            columns.append((col_name, col_type))

            # Inline Primärschlüssel
            if re.search(r'\bPRIMARY\s+KEY\b', part, re.IGNORECASE):
                primary_keys.add(col_name)

        # Separat definierter Primärschlüssel
        elif part.upper().startswith("PRIMARY KEY"):
            pk_match = re.search(r'\((.*?)\)', part)
            if pk_match:
                pk_cols = [col.strip().strip('"') for col in pk_match.group(1).split(',')]
                primary_keys.update(pk_cols)

        # Fremdschlüssel
        elif part.upper().startswith("FOREIGN KEY"):
            fk_match = re.search(r'\((.*?)\)', part)
            if fk_match:
                fk_cols = [col.strip().strip('"') for col in fk_match.group(1).split(',')]
                foreign_keys.update(fk_cols)

    return columns, primary_keys, foreign_keys

def generate_html_table(name, columns, pks, fks):
    col_strs = []
    for col, dtype in columns:
        text = f"{escape(col)} : {escape(dtype)}"
        if col in pks:
            text = f"<u>{text}</u>"
        if col in fks:
            text = f"<span style='text-decoration: underline dotted'>{text}</span>"
        col_strs.append(text)
    return f"{escape(name)}({', '.join(col_strs)})"

def convert_sqlite_master_to_html(db_path):
    cursor = runSql("SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL",db_path)
    result = cursor.fetchall()

    html_lines = []
    for name, sql in result:
        cols, pks, fks = parse_table_schema(sql)
        html_line = generate_html_table(name, cols, pks, fks)
        html_lines.append(html_line)

    return "<br>\n".join(html_lines)