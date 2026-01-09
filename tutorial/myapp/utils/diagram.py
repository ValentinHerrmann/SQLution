import json


from myapp.utils.utils import format_sql
from myapp.utils.json_to_sql import extract_tables
from myapp.utils.directories import get_user_directory
from myapp.utils.sqlite_connector import create_db



def load_json(json_bytes, username):
    try:
        json_string = json_bytes.decode('utf-8')
        data = json.loads(json_string)
        
        sql_output = format_sql(extract_tables(data))


        with open(get_user_directory(username)+'/_CreateDB.sql_', "w") as f:
            f.write(sql_output)
        create_db(sql_output, username)  # Call the function to execute SQL statements

    except Exception as e:
        print(f"Error: {e}")
        raise e
