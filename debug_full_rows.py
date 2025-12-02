import sqlite3
import os

db_path = r'c:\Users\Avinash\OneDrive\Desktop\REDAI\backend\selected_candidates.db'

def inspect_full_rows():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Full Test Rows ---")
    cursor.execute("SELECT * FROM tests")
    rows = cursor.fetchall()
    for row in rows:
        print(f"Row len={len(row)}: {row}")
        
    conn.close()

if __name__ == "__main__":
    inspect_full_rows()
