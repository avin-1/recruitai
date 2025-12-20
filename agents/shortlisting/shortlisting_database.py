import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.backend_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
        self.selected_candidates_db = os.path.join(self.backend_dir, 'selected_candidates.db')
        self.userids_db = os.path.join(self.backend_dir, 'userids.db')
        self.interview_db = os.path.join(self.backend_dir, 'interview.db')
        self.init_databases()
    
    def init_databases(self):
        """Initialize both databases with required tables"""
        # Initialize selected_candidates.db (already exists, just ensure test tables)
        self.init_selected_candidates_db()
        
        # Initialize userids.db
        self.init_userids_db()
        
        # Initialize interview.db
        self.init_interview_db()
    
    def _get_connection(self, db_path):
        """Get a database connection with increased timeout and WAL mode"""
        conn = sqlite3.connect(db_path, timeout=30.0)
        # Enable Write-Ahead Logging for better concurrency
        conn.execute('PRAGMA journal_mode=WAL')
        return conn

    def init_selected_candidates_db(self):
        """Initialize selected_candidates database with test-related tables"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        
        # Create tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                test_description TEXT,
                questions TEXT NOT NULL,  -- JSON string of selected questions
                platform_type TEXT DEFAULT 'codeforces',  -- 'codeforces' or 'custom'
                custom_platform_name TEXT,  -- Name of custom platform if platform_type is 'custom'
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'  -- active, completed, archived
            )
        ''')
        
        # Create test_notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                candidate_email TEXT NOT NULL,
                notification_sent BOOLEAN DEFAULT FALSE,
                sent_date TIMESTAMP,
                test_link TEXT,
                FOREIGN KEY (test_id) REFERENCES tests (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def init_userids_db(self):
        """Initialize userids database"""
        conn = self._get_connection(self.userids_db)
        cursor = conn.cursor()
        
        # Create userids table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS userids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_email TEXT NOT NULL,
                codeforces_username TEXT NOT NULL,
                test_id INTEGER,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tab_switches INTEGER DEFAULT 0,
                time_taken INTEGER DEFAULT 0,
                FOREIGN KEY (test_id) REFERENCES tests (id)
            )
        ''')
        
        # Migration: Add columns if they don't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE userids ADD COLUMN tab_switches INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass # Column likely exists
            
        try:
            cursor.execute('ALTER TABLE userids ADD COLUMN time_taken INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass # Column likely exists
        
        # Create test_results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid_id INTEGER NOT NULL,
                test_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                solved BOOLEAN DEFAULT FALSE,
                submission_time TIMESTAMP,
                result_data TEXT,  -- JSON string of detailed results
                FOREIGN KEY (userid_id) REFERENCES userids (id),
                FOREIGN KEY (test_id) REFERENCES tests (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def init_interview_db(self):
        """Initialize interview database to store approved candidates"""
        conn = self._get_connection(self.interview_db)
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

    def save_interview_candidate(self, candidate_email: str, codeforces_username: str = None, test_id: int = None) -> int:
        """Insert a candidate into interview list; idempotent on (email, test_id)"""
        conn = self._get_connection(self.interview_db)
        cursor = conn.cursor()
        
        # Try insert, if exists then fetch existing id
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO interview_candidates (candidate_email, codeforces_username, test_id)
                VALUES (?, ?, ?)
            ''', (candidate_email, codeforces_username, test_id))
            conn.commit()
            if cursor.rowcount == 0:
                cursor.execute('SELECT id FROM interview_candidates WHERE candidate_email = ? AND IFNULL(test_id, -1) IS IFNULL(?, -1)', (candidate_email, test_id))
                row = cursor.fetchone()
                candidate_id = row[0] if row else None
            else:
                candidate_id = cursor.lastrowid
        finally:
            conn.close()
        
        return candidate_id if candidate_id is not None else -1

    def get_interview_candidate_emails(self) -> list:
        """Return list of candidate emails from interview_candidates"""
        conn = self._get_connection(self.interview_db)
        cursor = conn.cursor()
        cursor.execute('SELECT candidate_email FROM interview_candidates ORDER BY approved_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

    def get_interview_candidates_details(self) -> list:
        """Return list of candidate details from interview_candidates with schedule and status"""
        conn = self._get_connection(self.interview_db)
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
            'username': row[1], # frontend expects 'username' or 'codeforces_username' depending on usage, keeping 'username' for consistency with previous simple version, but frontend might check codeforces_username
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

    def reject_candidate(self, candidate_email: str) -> bool:
        """Reject candidate and remove from database"""
        conn = self._get_connection(self.interview_db)
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

    def select_candidate(self, candidate_email: str) -> bool:
        """Select candidate and mark offer letter as sent"""
        conn = self._get_connection(self.interview_db)
        cursor = conn.cursor()
        try:
            # Check if entry exists in interview_results
            cursor.execute('SELECT id FROM interview_results WHERE candidate_email = ?', (candidate_email,))
            row = cursor.fetchone()
            
            if row:
                cursor.execute('UPDATE interview_results SET status = ?, offer_letter_sent = ? WHERE candidate_email = ?', ('selected', 1, candidate_email))
            else:
                cursor.execute('INSERT INTO interview_results (candidate_email, status, offer_letter_sent) VALUES (?, ?, ?)', (candidate_email, 'selected', 1))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error selecting candidate: {e}")
            return False
        finally:
            conn.close()

    def save_interview_schedule(self, candidate_email: str, start_iso: str, end_iso: str, hr_email: str = None, meeting_link: str = None) -> int:
        conn = self._get_connection(self.interview_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO interview_schedules (candidate_email, interview_start, interview_end, hr_email, meeting_link)
            VALUES (?, ?, ?, ?, ?)
        ''', (candidate_email, start_iso, end_iso, hr_email, meeting_link))
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return schedule_id

    def create_test(self, test_name, test_description, questions, platform_type='codeforces', custom_platform_name=None):
        """Create a new test"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tests (test_name, test_description, questions, platform_type, custom_platform_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (test_name, test_description, questions, platform_type, custom_platform_name))
        
        test_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return test_id
    
    def get_test_platform(self, test_id):
        """Get platform type for a test"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT platform_type, custom_platform_name FROM tests WHERE id = ?', (test_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {'platform_type': result[0] or 'codeforces', 'custom_platform_name': result[1]}
        return {'platform_type': 'codeforces', 'custom_platform_name': None}
    
    def get_all_candidates(self):
        """Get all selected candidates"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT candidate_email, candidate_name FROM selected_candidates')
        candidates = cursor.fetchall()
        conn.close()
        
        return [{'email': row[0], 'name': row[1]} for row in candidates]
    
    def send_test_notifications(self, test_id, test_link):
        """Send test notifications to all candidates"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        
        candidates = self.get_all_candidates()
        
        for candidate in candidates:
            cursor.execute('''
                INSERT INTO test_notifications (test_id, candidate_email, test_link)
                VALUES (?, ?, ?)
            ''', (test_id, candidate['email'], test_link))
        
        conn.commit()
        conn.close()
        
        return candidates
    
    def register_codeforces_user(self, candidate_email, codeforces_username, test_id):
        """Register a candidate's Codeforces username"""
        conn = self._get_connection(self.userids_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO userids (candidate_email, codeforces_username, test_id)
            VALUES (?, ?, ?)
        ''', (candidate_email, codeforces_username, test_id))
        
        userid_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return userid_id
    
    def get_test_questions(self, test_id):
        """Get questions for a specific test"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT questions FROM tests WHERE id = ?', (test_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            import json
            return json.loads(result[0])
        return []
    
    def get_registered_users(self, test_id):
        """Get all registered users for a test"""
        conn = self._get_connection(self.userids_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, candidate_email, codeforces_username 
            FROM userids WHERE test_id = ?
        ''', (test_id,))
        
        users = cursor.fetchall()
        conn.close()
        
        return [{'id': row[0], 'email': row[1], 'username': row[2]} for row in users]
    
    def save_test_results(self, userid_id, test_id, results):
        """Save test results for a user"""
        conn = self._get_connection(self.userids_db)
        cursor = conn.cursor()
        
        try:
            # Clear existing results for this user
            cursor.execute('DELETE FROM test_results WHERE userid_id = ?', (userid_id,))
            
            # Insert new results
            for question_id, result_data in results.items():
                cursor.execute('''
                    INSERT INTO test_results (userid_id, test_id, question_id, solved, result_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (userid_id, test_id, question_id, result_data.get('solved', False), str(result_data)))
            
            conn.commit()
        finally:
            conn.close()

    def update_candidate_metrics(self, userid_id, tab_switches, time_taken):
        """Update candidate metrics (tab switches, time taken)"""
        conn = self._get_connection(self.userids_db)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE userids 
                SET tab_switches = ?, time_taken = ?
                WHERE id = ?
            ''', (tab_switches, time_taken, userid_id))
            conn.commit()
        finally:
            conn.close()

    def delete_candidate_result(self, test_id, candidate_email):
        """Delete a candidate's result and registration for a specific test"""
        conn = self._get_connection(self.userids_db)
        cursor = conn.cursor()
        try:
            # Get userid_id
            cursor.execute('SELECT id FROM userids WHERE test_id = ? AND candidate_email = ?', (test_id, candidate_email))
            row = cursor.fetchone()
            if not row:
                return False
            
            userid_id = row[0]
            
            # Delete from test_results
            cursor.execute('DELETE FROM test_results WHERE userid_id = ?', (userid_id,))
            
            # Delete from userids
            cursor.execute('DELETE FROM userids WHERE id = ?', (userid_id,))
            
            conn.commit()
            return True
        finally:
            conn.close()
    
    def get_test_results(self, test_id):
        """Get all test results for a specific test"""
        conn = self._get_connection(self.userids_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.candidate_email, u.codeforces_username, tr.question_id, tr.solved, tr.result_data, u.tab_switches, u.time_taken
            FROM userids u
            JOIN test_results tr ON u.id = tr.userid_id
            WHERE u.test_id = ?
            ORDER BY u.candidate_email, tr.question_id
        ''', (test_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_all_tests(self):
        """Get all tests"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tests ORDER BY created_date DESC')
        tests = cursor.fetchall()
        conn.close()
        
        return tests

    def archive_test(self, test_id: int) -> None:
        """Soft-delete a test by marking status as 'archived'"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        cursor.execute('UPDATE tests SET status = ? WHERE id = ?', ('archived', test_id))
        conn.commit()
        conn.close()

    def get_test_status(self, test_id: int) -> str:
        """Get the status of a test"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM tests WHERE id = ?', (test_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def permanently_delete_test(self, test_id: int) -> None:
        """Permanently delete a test and all associated data"""
        
        # 1. Delete from test_notifications (Child of tests in selected_candidates.db)
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM test_notifications WHERE test_id = ?', (test_id,))
            conn.commit()
        except Exception as e:
            print(f"Error deleting notifications: {e}")
        
        # 2. Delete from tests table (Parent in selected_candidates.db)
        # Now safe to delete as children are gone
        try:
            cursor.execute('DELETE FROM tests WHERE id = ?', (test_id,))
            conn.commit()
        except Exception as e:
            print(f"Error deleting test: {e}")
            raise e # Re-raise to notify caller
        finally:
            conn.close()
        
        # 3. Delete from userids table (registrations) and test_results (in userids.db)
        # These are in a separate DB, so no FK constraint with tests table in selected_candidates.db
        conn = self._get_connection(self.userids_db)
        cursor = conn.cursor()
        
        try:
            # Get userids for this test to delete their results
            cursor.execute('SELECT id FROM userids WHERE test_id = ?', (test_id,))
            user_ids = [row[0] for row in cursor.fetchall()]
            
            if user_ids:
                # Delete results for these users
                placeholders = ','.join(['?'] * len(user_ids))
                cursor.execute(f'DELETE FROM test_results WHERE userid_id IN ({placeholders})', user_ids)
                
            # Delete registrations
            cursor.execute('DELETE FROM userids WHERE test_id = ?', (test_id,))
            conn.commit()
        except Exception as e:
            print(f"Error deleting user data: {e}")
        finally:
            conn.close()

    def get_agent_prompt(self, agent_name: str) -> str:
        """Get custom prompt for an agent, or None if not set"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        cursor.execute('SELECT prompt_text FROM agent_prompts WHERE agent_name = ?', (agent_name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def save_agent_prompt(self, agent_name: str, prompt_text: str) -> None:
        """Save or update custom prompt for an agent"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO agent_prompts (agent_name, prompt_text, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (agent_name, prompt_text))
        conn.commit()
        conn.close()

    def reset_agent_prompt(self, agent_name: str) -> None:
        """Remove custom prompt for an agent (revert to default)"""
        conn = self._get_connection(self.selected_candidates_db)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM agent_prompts WHERE agent_name = ?', (agent_name,))
        conn.commit()
        conn.close()
