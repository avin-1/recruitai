import os
import sqlite3

class InterviewDatabase:
    def __init__(self):
        self.backend_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
        self.interview_db = os.path.join(self.backend_dir, 'interview.db')
        print(f"[InterviewDatabase] Using DB: {os.path.abspath(self.interview_db)}")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.interview_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interview_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_email TEXT NOT NULL,
                codeforces_username TEXT,
                test_id INTEGER,
                approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(candidate_email, test_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interview_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_email TEXT NOT NULL,
                interview_start TIMESTAMP NOT NULL,
                interview_end TIMESTAMP NOT NULL,
                hr_email TEXT,
                meeting_link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interview_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_email TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                offer_letter_sent BOOLEAN DEFAULT FALSE,
                offer_sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(candidate_email)
            )
        ''')
        conn.commit()
        conn.close()

    def get_interview_candidate_emails(self) -> list:
        conn = sqlite3.connect(self.interview_db)
        cursor = conn.cursor()
        cursor.execute('SELECT candidate_email FROM interview_candidates ORDER BY approved_at DESC')
        rows = cursor.fetchall()
        conn.close()
        print(f"[InterviewDatabase] get_interview_candidate_emails fetched {len(rows)} rows from {os.path.abspath(self.interview_db)}")
        return [row[0] for row in rows]

    def save_interview_schedule(self, candidate_email: str, start_iso: str, end_iso: str, hr_email: str = None, meeting_link: str = None) -> int:
        conn = sqlite3.connect(self.interview_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO interview_schedules (candidate_email, interview_start, interview_end, hr_email, meeting_link)
            VALUES (?, ?, ?, ?, ?)
        ''', (candidate_email, start_iso, end_iso, hr_email, meeting_link))
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return schedule_id

    def get_candidates_with_schedules(self) -> list:
        """Get all candidates with their schedule information"""
        conn = sqlite3.connect(self.interview_db)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT 
                ic.candidate_email,
                ic.codeforces_username,
                ic.test_id,
                ic.approved_at,
                isch.interview_start,
                isch.interview_end,
                isch.hr_email,
                isch.meeting_link,
                COALESCE(ir.status, 'pending') as status,
                COALESCE(ir.offer_letter_sent, 0) as offer_letter_sent
            FROM interview_candidates ic
            LEFT JOIN interview_schedules isch ON ic.candidate_email = isch.candidate_email
            LEFT JOIN interview_results ir ON ic.candidate_email = ir.candidate_email
            ORDER BY ic.approved_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [{
            'email': row[0],
            'codeforces_username': row[1],
            'test_id': row[2],
            'approved_at': row[3],
            'interview_start': row[4],
            'interview_end': row[5],
            'hr_email': row[6],
            'meeting_link': row[7],
            'status': row[8],
            'offer_letter_sent': bool(row[9])
        } for row in rows]

    def select_candidate(self, candidate_email: str) -> bool:
        """Mark candidate as selected and send offer letter"""
        conn = sqlite3.connect(self.interview_db)
        cursor = conn.cursor()
        from datetime import datetime, timezone
        cursor.execute('''
            INSERT OR REPLACE INTO interview_results 
            (candidate_email, status, offer_letter_sent, offer_sent_at)
            VALUES (?, 'selected', 1, ?)
        ''', (candidate_email, datetime.now(timezone.utc)))
        conn.commit()
        conn.close()
        return True

    def reject_candidate(self, candidate_email: str) -> bool:
        """Reject candidate and remove from database"""
        conn = sqlite3.connect(self.interview_db)
        cursor = conn.cursor()
        # Remove from interview_results
        cursor.execute('DELETE FROM interview_results WHERE candidate_email = ?', (candidate_email,))
        # Remove from interview_candidates
        cursor.execute('DELETE FROM interview_candidates WHERE candidate_email = ?', (candidate_email,))
        # Remove from interview_schedules
        cursor.execute('DELETE FROM interview_schedules WHERE candidate_email = ?', (candidate_email,))
        conn.commit()
        conn.close()
        return True



