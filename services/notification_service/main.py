from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# --- Email Service Class (logic adapted from old EmailService) ---
class NotificationManager:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        self.init_database()

    def init_database(self):
        db_path = os.path.join(os.path.dirname(__file__), 'notifications.db')
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

    def _send_email(self, to_email, subject, body, attachment_path=None):
        if not self.sender_email or not self.sender_password:
            return False, "Email credentials not configured."
        
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if attachment_path:
            try:
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)
            except Exception as e:
                return False, f"Error attaching file: {str(e)}"

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, to_email, msg.as_string())
            server.quit()
            return True, "Sent"
        except Exception as e:
            return False, str(e)

    def select_candidate(self, job_id, job_title, company, candidate):
        # 1. Save to DB
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO selected_candidates 
            (job_id, job_title, candidate_name, candidate_email, selection_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (job_id, job_title, candidate['name'], candidate['email'], datetime.now()))
        self.conn.commit()

        # 2. Send Email
        subject = f"Congratulations! You've been selected for {job_title}"
        body = f"""
Dear {candidate['name']},

Congratulations! We are pleased to inform you that you have been selected for the next stage of our recruitment process for the position of {job_title} at {company}.
Your application stood out among many others, and we would like to invite you for an interview to discuss the role further.
We will be in touch soon with details about the interview process, including scheduling and format.

Best regards,
The Recruitment Team
{company}
"""
        success, error = self._send_email(candidate['email'], subject, body)
        
        if success:
            cursor.execute('''
                UPDATE selected_candidates 
                SET email_sent = TRUE, email_sent_date = ?
                WHERE job_id = ? AND candidate_email = ?
            ''', (datetime.now(), job_id, candidate['email']))
            self.conn.commit()
            
        return success, error

    def get_history(self, job_id=None):
        cursor = self.conn.cursor()
        if job_id:
            cursor.execute('SELECT * FROM selected_candidates WHERE job_id = ? ORDER BY selection_date DESC', (job_id,))
        else:
            cursor.execute('SELECT * FROM selected_candidates ORDER BY selection_date DESC')
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Global Manager
manager = NotificationManager()

# --- Routes ---

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "Notification Service Online"}), 200

@app.route("/send/offer", methods=["POST"])
def send_offer():
    """Send offer letter with attachment"""
    data = request.form
    file = request.files.get('file')
    
    candidate_email = data.get('candidate_email')
    candidate_name = data.get('candidate_name', 'Candidate')
    job_title = data.get('job_title', 'Role')
    company = data.get('company', 'Company')
    custom_body = data.get('email_body')

    if not file:
        return jsonify({"error": "No offer letter file provided"}), 400

    # Save temp file
    import tempfile
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, file.filename)
    file.save(temp_path)

    subject = f"Offer Letter: {job_title} at {company}"
    body = custom_body if custom_body else f"""
Dear {candidate_name},

We are delighted to offer you the position of {job_title} at {company}!
Please find your official offer letter attached to this email.
We are excited about the possibility of you joining our team and look forward to your positive response.

Best regards,
The Recruitment Team
{company}
"""
    
    success, error = manager._send_email(candidate_email, subject, body, attachment_path=temp_path)
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)

    if success:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "error": error}), 500

@app.route("/send/rejection", methods=["POST"])
def send_rejection():
    data = request.get_json()
    candidate_email = data.get('candidate_email')
    candidate_name = data.get('candidate_name')
    job_title = data.get('job_title')
    company = data.get('company')

    subject = f"Update regarding your application for {job_title}"
    body = f"""
Dear {candidate_name},

Thank you for giving us the opportunity to consider your application for the {job_title} position at {company}.
We have reviewed your application and qualifications. While we were impressed with your background, we have decided to move forward with other candidates who more closely match our current needs for this role.
We appreciate the time and effort you put into your application and wish you the best of luck in your job search.

Best regards,
The Recruitment Team
{company}
"""
    success, error = manager._send_email(candidate_email, subject, body)
    return jsonify({"success": success, "error": error}), (200 if success else 500)

@app.route("/send/interview-selection", methods=["POST"])
def send_interview_selection():
    data = request.get_json()
    candidate_email = data.get('candidate_email')
    candidate_name = data.get('candidate_name')
    test_name = data.get('test_name')

    subject = f"Interview Selection: {test_name}"
    body = f"""
Dear {candidate_name},

Congratulations! We are pleased to inform you that based on your performance in the "{test_name}", you have been shortlisted for an interview.
We were impressed with your skills and would like to proceed to the next stage of our recruitment process.
Our HR team will be in touch with you shortly to schedule the interview.

Best regards,
The Recruitment Team
"""
    success, error = manager._send_email(candidate_email, subject, body)
    return jsonify({"success": success, "error": error}), (200 if success else 500)

@app.route("/send/test-invitation", methods=["POST"])
def send_test_invitation():
    data = request.get_json()
    candidate_email = data.get('candidate_email')
    candidate_name = data.get('candidate_name')
    test_link = data.get('test_link')

    subject = "Technical Test Invitation - Codeforces Assessment"
    body = f"""
Dear {candidate_name},

You have been invited to take a technical assessment test as part of our recruitment process.

Test Details:
- Platform: Codeforces
- Test Link: {test_link}

Please complete the test at your earliest convenience.

Best regards,
The Recruitment Team
"""
    success, error = manager._send_email(candidate_email, subject, body)
    return jsonify({"success": success, "error": error}), (200 if success else 500)

@app.route("/select-candidates", methods=["POST"])
def select_candidates():
    """Bulk selection and email"""
    data = request.get_json()
    job_id = data.get('job_id')
    job_title = data.get('job_title')
    company = data.get('company')
    candidates = data.get('candidates', []) # List of {name, email}

    results = {'success': [], 'failed': [], 'total_selected': 0}

    for cand in candidates:
        success, error = manager.select_candidate(job_id, job_title, company, cand)
        if success:
            results['success'].append(cand)
            results['total_selected'] += 1
        else:
            cand['error'] = error
            results['failed'].append(cand)

    return jsonify(results), 200

@app.route("/selected-history", methods=["GET"])
def get_history():
    job_id = request.args.get('job_id')
    history = manager.get_history(job_id)
    return jsonify({"selected_candidates": history}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005)) # Defaulting to 5005 for Notification Service
    app.run(host="0.0.0.0", port=port)
