import sqlite3
import os

db_path = r'c:\Users\Avinash\OneDrive\Desktop\REDAI\backend\selected_candidates.db'

def create_table():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating agent_prompts table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_prompts (
            agent_name TEXT PRIMARY KEY,
            prompt_text TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Table created successfully.")

if __name__ == "__main__":
    create_table()
