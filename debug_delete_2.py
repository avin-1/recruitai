import sqlite3
import os

db_path = r'c:\Users\Avinash\OneDrive\Desktop\REDAI\backend\selected_candidates.db'

def debug_delete():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    test_id = 2
    print(f"Debugging deletion for Test ID: {test_id}")
    
    # Check notifications
    cursor.execute("SELECT count(*) FROM test_notifications WHERE test_id = ?", (test_id,))
    count = cursor.fetchone()[0]
    print(f"Notifications count: {count}")
    
    # Check interview_candidates
    try:
        cursor.execute("SELECT count(*) FROM interview_candidates WHERE test_id = ?", (test_id,))
        count = cursor.fetchone()[0]
        print(f"Interview candidates count: {count}")
    except Exception as e:
        print(f"Error checking interview_candidates: {e}")

    # Check FKs on interview_candidates
    try:
        cursor.execute("PRAGMA foreign_key_list(interview_candidates)")
        print(f"interview_candidates FKs: {cursor.fetchall()}")
    except:
        pass

    # Try manual delete sequence
    print("\nAttempting manual delete sequence...")
    try:
        print("Deleting notifications...")
        cursor.execute("DELETE FROM test_notifications WHERE test_id = ?", (test_id,))
        print(f"Deleted {cursor.rowcount} notifications.")
        
        print("Deleting test...")
        cursor.execute("DELETE FROM tests WHERE id = ?", (test_id,))
        print(f"Deleted {cursor.rowcount} tests.")
        
        conn.commit()
        print("COMMIT SUCCESSFUL")
    except Exception as e:
        print(f"DELETE FAILED: {e}")
        conn.rollback()
        
    conn.close()

if __name__ == "__main__":
    debug_delete()
