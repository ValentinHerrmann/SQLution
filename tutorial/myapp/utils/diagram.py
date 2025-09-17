import json

from myapp.utils.utils import *
from myapp.utils.sqlite_connector import *


def load_json(json_bytes, username):
    try:
        json_string = json_bytes.decode('utf-8')
        data = json.loads(json_string)
        
        sql_output = format_sql(extract_tables(data))

        with open(get_user_directory(username)+'/_CreateDB.sql_', "w") as f:
            f.write(sql_output)
        with open(get_user_directory(username)+'/model.json', "wb+") as f:
            f.write(json_bytes)
        create_db(sql_output, username)  # Call the function to execute SQL statements

    except Exception as e:
        print(f"Error: {e}")
