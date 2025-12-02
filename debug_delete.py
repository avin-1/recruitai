import sqlite3
import os

db_path = r'c:\Users\Avinash\OneDrive\Desktop\REDAI\backend\selected_candidates.db'

def inspect_db():
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- Tests ---")
    cursor.execute("SELECT id, test_name, status FROM tests")
    tests = cursor.fetchall()
    for t in tests:
        print(t)
        if t[1] == "Monali Test":
            target_id = t[0]
            print(f"TARGET FOUND: ID={target_id}")

    print("\n--- Schema: tests ---")
    cursor.execute("PRAGMA table_info(tests)")
    for col in cursor.fetchall():
        print(col)

    print("\n--- Schema: test_notifications ---")
    cursor.execute("PRAGMA table_info(test_notifications)")
    for col in cursor.fetchall():
        print(col)
        
    print("\n--- Foreign Keys ---")
    cursor.execute("PRAGMA foreign_key_list(test_notifications)")
    for fk in cursor.fetchall():
        print(f"test_notifications FK: {fk}")

    conn.close()

if __name__ == "__main__":
    inspect_db()
