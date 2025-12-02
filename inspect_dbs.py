import sqlite3
import os

dbs = [
    r'c:\Users\Avinash\OneDrive\Desktop\REDAI\backend\selected_candidates.db',
    r'c:\Users\Avinash\OneDrive\Desktop\REDAI\backend\interview.db'
]

with open('schema_dump.txt', 'w') as f:
    for db_path in dbs:
        f.write(f"\n--- Database: {os.path.basename(db_path)} ---\n")
        if not os.path.exists(db_path):
            f.write("File not found.\n")
            continue
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            f.write(f"Table: {table_name}\n")
            cursor.execute(f"PRAGMA table_info({table_name})")
            cols = cursor.fetchall()
            for col in cols:
                f.write(f"  - {col[1]} ({col[2]})\n")
                
        conn.close()
