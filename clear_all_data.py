import sqlite3
import os

def clear_database(db_path):
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return

    print(f"Clearing database: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Disable foreign keys to allow deleting in any order
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
        tables = cursor.fetchall()
        
        for table_name in tables:
            table = table_name[0]
            print(f"  - Deleting entries from table: {table}")
            cursor.execute(f"DELETE FROM {table}")
        
        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence")
        
        conn.commit()
        print(f"Successfully cleared {db_path}")
        
    except Exception as e:
        print(f"Error clearing {db_path}: {e}")
    finally:
        if conn:
            conn.close()

def main():
    # Define paths to all databases
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, 'backend')
    
    databases = [
        os.path.join(backend_dir, 'selected_candidates.db'),
        os.path.join(backend_dir, 'userids.db'),
        os.path.join(backend_dir, 'interview.db'),
        os.path.join(backend_dir, 'prompts.db')
    ]
    
    print("WARNING: This script will delete ALL data from the following databases:")
    for db in databases:
        print(f" - {db}")
    
    confirm = input("\nAre you sure you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return

    for db_path in databases:
        clear_database(db_path)
    
    print("\nAll databases cleared successfully.")

if __name__ == "__main__":
    main()
