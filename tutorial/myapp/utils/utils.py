from datetime import datetime
from io import BytesIO
import os
import re
import collections
import shutil
import zipfile
import time

from myapp.models import ZippedFolder



def timestamp():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]") + "\t"

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



def remove_nones_from_sqlresult(result:list):
    if result:
        return [tuple('' if v is None else v for v in row) for row in result]
    return []