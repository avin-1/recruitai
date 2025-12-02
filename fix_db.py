import sqlite3
import datetime

db_path = r'c:\Users\Avinash\OneDrive\Desktop\REDAI\backend\userids.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# User ID 1 (from previous debug)
userid_id = 1
test_id = 1
question_id = '1_2'

print(f"Inserting missing result for {question_id}...")

# Check if exists
cursor.execute("SELECT id FROM test_results WHERE userid_id = ? AND question_id = ?", (userid_id, question_id))
if cursor.fetchone():
    print("Result already exists.")
else:
    cursor.execute('''
        INSERT INTO test_results (userid_id, test_id, question_id, solved, result_data)
        VALUES (?, ?, ?, ?, ?)
    ''', (userid_id, test_id, question_id, 1, "{'solved': True, 'type': 'manual', 'answer': 'Manual Fix'}"))
    conn.commit()
    print("Inserted successfully.")

conn.close()
