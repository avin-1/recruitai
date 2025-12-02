import sqlite3
import json

db_path = r'c:\Users\Avinash\OneDrive\Desktop\REDAI\backend\selected_candidates.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Querying test 1...")
cursor.execute("SELECT questions FROM tests WHERE id = 1")
row = cursor.fetchone()

if row:
    questions_json = row[0]
    print(f"Raw JSON: {questions_json}")
    try:
        data = json.loads(questions_json)
        print(json.dumps(data, indent=2))
    except:
        print("Invalid JSON")
else:
    print("Test 1 not found")

conn.close()
