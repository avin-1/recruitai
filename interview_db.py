import os
import sqlite3
import sys

def get_db_path():
    # Allow an optional CLI arg: python print_interview_db.py [path_to_db]
    if len(sys.argv) > 1:
        return sys.argv[1]
    # Default to repo layout: backend/interview.db
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = script_dir  # adjust if placing this file elsewhere
    default_path = os.path.join(repo_root, 'backend', 'interview.db')
    return default_path

def fetch_all_interview_candidates(db_path):
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interview_candidates'")
        if cur.fetchone() is None:
            print("Table 'interview_candidates' does not exist.")
            return

        cur.execute("SELECT id, candidate_email, codeforces_username, test_id, approved_at FROM interview_candidates ORDER BY approved_at DESC")
        rows = cur.fetchall()

        if not rows:
            print("No entries found in 'interview_candidates'.")
            return

        # Pretty print
        headers = ["id", "candidate_email", "codeforces_username", "test_id", "approved_at"]
        widths = {h: max(len(h), *(len(str(r[h])) for r in rows)) for h in headers}

        def line():
            return "+-" + "-+-".join("-" * widths[h] for h in headers) + "-+"

        print(line())
        print("| " + " | ".join(h.ljust(widths[h]) for h in headers) + " |")
        print(line())
        for r in rows:
            print("| " + " | ".join(str(r[h]).ljust(widths[h]) for h in headers) + " |")
        print(line())
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = get_db_path()
    fetch_all_interview_candidates(db_path)