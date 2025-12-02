import sqlite3

db_path = r'c:\Users\Avinash\OneDrive\Desktop\REDAI\backend\selected_candidates.db'

def map_columns():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # Access by name
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tests LIMIT 1")
    row = cursor.fetchone()
    
    print("--- Column Mapping ---")
    for key in row.keys():
        print(f"{key}: {row[key]}")
        
    # Also print by index
    print("\n--- By Index ---")
    tuple_row = tuple(row)
    for i, val in enumerate(tuple_row):
        print(f"Index {i}: {val}")

    conn.close()

if __name__ == "__main__":
    map_columns()
