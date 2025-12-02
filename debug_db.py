import sqlite3
import os

db_path = r'c:\Users\Avinash\OneDrive\Desktop\REDAI\backend\userids.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

email = 'avinash.bhurke23@vit.edu'

print(f"Querying for {email}...")

# Get user ID
cursor.execute("SELECT id, test_id FROM userids WHERE candidate_email = ?", (email,))
user = cursor.fetchone()

if user:
    user_id, test_id = user
    print(f"User ID: {user_id}, Test ID: {test_id}")
    
    # Get results
    cursor.execute("SELECT question_id, solved, result_data FROM test_results WHERE userid_id = ?", (user_id,))
    results = cursor.fetchall()
    
    print(f"Found {len(results)} results:")
    for row in results:
        q_id, solved, data = row
        print(f"  QID: '{q_id}', Solved: {solved}")
        
else:
    print("User not found")

conn.close()
