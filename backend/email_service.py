import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        
        # Initialize SQLite database
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for selected candidates"""
        db_path = os.path.join(os.path.dirname(__file__), 'selected_candidates.db')
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selected_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                job_title TEXT NOT NULL,
                candidate_name TEXT NOT NULL,
                candidate_email TEXT NOT NULL,
                selection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                email_sent BOOLEAN DEFAULT FALSE,
                email_sent_date TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def send_selection_email(self, candidate_email, candidate_name, job_title, company):
        """Send email to selected candidate"""
        if not self.sender_email or not self.sender_password:
            raise ValueError("Email credentials not configured. Please set SENDER_EMAIL and SENDER_PASSWORD in .env file")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = candidate_email
        msg['Subject'] = f"Congratulations! You've been selected for {job_title}"
        
        # Email body
        body = f"""
Dear {candidate_name},

Congratulations! We are pleased to inform you that you have been selected for the next stage of our recruitment process for the position of {job_title} at {company}.

Your application stood out among many others, and we would like to invite you for an interview to discuss the role further.

We will be in touch soon with details about the interview process, including scheduling and format.

Thank you for your interest in joining our team. We look forward to meeting you!

Best regards,
The Recruitment Team
{company}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, candidate_email, text)
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email to {candidate_email}: {str(e)}")
            return False
    
    def select_candidates(self, job_id, job_title, company, candidates):
        """Select candidates and send emails"""
        results = {
            'success': [],
            'failed': [],
            'total_selected': 0
        }
        
        cursor = self.conn.cursor()
        
        for candidate in candidates:
            try:
                # Store in database
                cursor.execute('''
                    INSERT INTO selected_candidates 
                    (job_id, job_title, candidate_name, candidate_email, selection_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (job_id, job_title, candidate['name'], candidate['email'], datetime.now()))
                
                # Send email
                email_sent = self.send_selection_email(
                    candidate['email'], 
                    candidate['name'], 
                    job_title, 
                    company
                )
                
                # Update email status
                if email_sent:
                    cursor.execute('''
                        UPDATE selected_candidates 
                        SET email_sent = TRUE, email_sent_date = ?
                        WHERE job_id = ? AND candidate_email = ?
                    ''', (datetime.now(), job_id, candidate['email']))
                    results['success'].append(candidate)
                else:
                    results['failed'].append(candidate)
                
                results['total_selected'] += 1
                
            except Exception as e:
                print(f"Error processing candidate {candidate['name']}: {str(e)}")
                results['failed'].append(candidate)
        
        self.conn.commit()
        return results
    
    def get_selected_candidates(self, job_id=None):
        """Get selected candidates from database"""
        cursor = self.conn.cursor()
        
        if job_id:
            cursor.execute('''
                SELECT * FROM selected_candidates 
                WHERE job_id = ? 
                ORDER BY selection_date DESC
            ''', (job_id,))
        else:
            cursor.execute('''
                SELECT * FROM selected_candidates 
                ORDER BY selection_date DESC
            ''')
        
        columns = [description[0] for description in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            result = dict(zip(columns, row))
            results.append(result)
        
        return results
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
