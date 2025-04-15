import sqlite3
import os
from .models import DatabaseModel

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

    #bDB = DatabaseModel.objects.filter(user=username).first().db
    #if bDB is not None:
    #    with open(dbname, 'wb') as file:
    #        file.write(bDB)

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

    #with open(dbname, 'rb') as file:
    #    binary_data = file.read()
    #    DatabaseModel.objects.filter(user=username).first().db = binary_data
    return cur