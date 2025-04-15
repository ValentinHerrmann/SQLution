import sqlite3
import os

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

def runSql(sql:str, username:str):
    rows = None
    with sqlite3.connect(get_db_name(username)) as con:
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