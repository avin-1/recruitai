import sqlite3

db_path = r'c:\Users\Avinash\OneDrive\Desktop\REDAI\backend\selected_candidates.db'

def check_schema():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Schema: tests ---")
    cursor.execute("PRAGMA table_info(tests)")
    cols = cursor.fetchall()
    for col in cols:
        print(f"Index {col[0]}: {col[1]} ({col[2]})")
        
    print("\n--- First Row ---")
    cursor.execute("SELECT * FROM tests LIMIT 1")
    row = cursor.fetchone()
    print(row)
    
    conn.close()

if __name__ == "__main__":
    check_schema()
