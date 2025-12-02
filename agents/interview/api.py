from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
from interview_database import InterviewDatabase
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import sqlite3
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import time as dtime
import uuid
import pytz
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.agent_orchestrator import scheduling_agent
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("interview_api")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]
# These env vars must be set in .env or OS environment
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")  # Optional, for service account

# OAuth Installed App helper (uses credentials.json and token.json in same folder)
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.json')

def build_calendar_service_oauth():
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # Refresh failed (e.g. revoked), so force new login
                creds = None
        
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                raise Exception("credentials.json not found for OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # Launch local server for user consent
            creds = flow.run_local_server(port=0)
            
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build('calendar', 'v3', credentials=creds)


# Compute free 30-min slots given busy periods within a date range and working hours
# busy_periods: list of {start: iso, end: iso}
# returns: list of {start, end}
def compute_free_slots(busy_periods, window_start_utc, window_end_utc, slot_minutes=30, workday_start=dtime(9,0), workday_end=dtime(18,0)):
    # normalize busy intervals
    intervals = []
    for b in busy_periods:
        try:
            bs = datetime.datetime.fromisoformat(b['start'].replace('Z','+00:00'))
            be = datetime.datetime.fromisoformat(b['end'].replace('Z','+00:00'))
            if be > window_start_utc and bs < window_end_utc:
                intervals.append((max(bs, window_start_utc), min(be, window_end_utc)))
        except Exception:
            continue
    # merge intervals
    intervals.sort()
    merged = []
    for s,e in intervals:
        if not merged or s > merged[-1][1]:
            merged.append([s,e])
        else:
            merged[-1][1] = max(merged[-1][1], e)
    # iterate days and produce free slots
    slots = []
    cur = window_start_utc
    one_day = datetime.timedelta(days=1)
    slot_delta = datetime.timedelta(minutes=slot_minutes)
    while cur < window_end_utc:
        # workday bounds for this day
        wd_start = datetime.datetime.combine(cur.date(), workday_start, tzinfo=datetime.timezone.utc)
        wd_end = datetime.datetime.combine(cur.date(), workday_end, tzinfo=datetime.timezone.utc)
        day_start = max(wd_start, window_start_utc)
        day_end = min(wd_end, window_end_utc)
        if day_start < day_end:
            # walk free gaps by subtracting merged busy
            t = day_start
            # find busy intervals overlapping this day
            day_busy = []
            for s,e in merged:
                if e <= day_start: continue
                if s >= day_end: break
                day_busy.append((max(s, day_start), min(e, day_end)))
            # produce free ranges between day_busy
            free_ranges = []
            if not day_busy:
                free_ranges.append((day_start, day_end))
            else:
                t = day_start
                for s,e in day_busy:
                    if s > t:
                        free_ranges.append((t, s))
                    t = max(t, e)
                if t < day_end:
                    free_ranges.append((t, day_end))
            # slice into slot-sized chunks
            for fs, fe in free_ranges:
                t = fs
                while t + slot_delta <= fe:
                    slots.append({
                        'start': (t).isoformat().replace('+00:00','Z'),
                        'end': (t + slot_delta).isoformat().replace('+00:00','Z')
                    })
                    t += slot_delta
        cur = (datetime.datetime.combine((cur+one_day).date(), dtime(0,0), tzinfo=datetime.timezone.utc))
    return slots

def get_google_calendar_availability_oauth(days=5):
    service = build_calendar_service_oauth()
    now = datetime.datetime.now(datetime.timezone.utc)
    time_min = now.isoformat()
    time_max = (now + datetime.timedelta(days=days)).isoformat()
    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": "primary"}]
    }
    response = service.freebusy().query(body=body).execute()
    busy_periods = response['calendars']['primary']['busy']
    # compute free slots
    window_start = now
    window_end = datetime.datetime.fromisoformat(time_max)
    return compute_free_slots(busy_periods, window_start, window_end)

# Utility to get HR's busy slots from their Google Calendar
# Email should have a calendar (must be authorized via OAuth2 or service account with access!)
def get_google_calendar_availability(hr_email, days=5):
    # Prefer service account for daemon/server; else, OAuth2 needed per HR account
    # Here, expect service account json in GOOGLE_SERVICE_ACCOUNT_FILE
    try:
        creds = None
        if GOOGLE_SERVICE_ACCOUNT_FILE:
            creds = service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=SCOPES,
                subject=hr_email  # Domain-wide delegation, if available
            )
        else:
            raise Exception("Service account-based fetch not configured. Set GOOGLE_SERVICE_ACCOUNT_FILE.")
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.now(datetime.timezone.utc)
        time_min = now.isoformat()
        time_max = (now + datetime.timedelta(days=days)).isoformat()
        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": hr_email}]
        }
        response = service.freebusy().query(body=body).execute()
        busy_periods = response['calendars'][hr_email]['busy']
        # Return computed free slots
        window_start = now
        window_end = datetime.datetime.fromisoformat(time_max)
        return compute_free_slots(busy_periods, window_start, window_end)
    except Exception as e:
        return f"Error fetching availability: {str(e)}"

db = InterviewDatabase()

@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path} | Data: {request.get_data(as_text=True)}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status} {response.get_data(as_text=True)[:300]}")
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Exception: {repr(e)}", exc_info=True)
    return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/interviews/candidates', methods=['GET'])
def get_interview_candidates():
    try:
        emails = db.get_interview_candidate_emails()
        return jsonify({'success': True, 'emails': emails})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/debug/add_dummy_candidate', methods=['POST'])
def add_dummy_candidate():
    try:
        from datetime import datetime
        email = request.json.get("email", "dummy@example.com")
        test_id = request.json.get("test_id", 1)
        codeforces = request.json.get("codeforces", "dummy_user")
        # Insert into DB using raw sqlite
        conn = db  # InterviewDatabase instance
        sqlite_conn = sqlite3.connect(conn.interview_db)
        cursor = sqlite_conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO interview_candidates (candidate_email, codeforces_username, test_id, approved_at) VALUES (?, ?, ?, ?)",
            (email, codeforces, test_id, datetime.utcnow())
        )
        sqlite_conn.commit()
        sqlite_conn.close()
        return jsonify({"success": True, "message": f"Inserted {email}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/interviews/debug/db_info', methods=['GET'])
def db_info():
    try:
        from database import InterviewDatabase
        db = InterviewDatabase()
        emails = db.get_interview_candidate_emails()
        db_path = db.interview_db
        return jsonify({
            "success": True,
            "db_path": os.path.abspath(db_path),
            "candidate_count": len(emails),
            "emails": emails
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/interviews/availability', methods=['POST'])
def get_hr_availability():
    try:
        data = request.get_json() or {}
        hr_email = data.get('hr_email')
        
        scheduling_agent.notify(
            f"📅 Fetching calendar availability for {hr_email}...",
            'processing'
        )
        
        # First try Service Account path
        busy_slots = get_google_calendar_availability(hr_email)
        if isinstance(busy_slots, str):
            # If service account failed due to auth, try OAuth fallback (installed app)
            lowered = busy_slots.lower()
            if 'unauthorized_client' in lowered or 'invalid_grant' in lowered or 'not configured' in lowered:
                try:
                    busy_slots = get_google_calendar_availability_oauth()
                    scheduling_agent.notify(
                        f"✅ Calendar availability retrieved via OAuth: {len(busy_slots)} free slots found",
                        'success',
                        reasoning="Used OAuth authentication to access Google Calendar API"
                    )
                except Exception as oauth_err:
                    scheduling_agent.notify(
                        f"❌ Failed to fetch calendar: {str(oauth_err)}",
                        'warning'
                    )
                    return jsonify({'success': False, 'error': f'OAuth fallback failed: {str(oauth_err)}'}), 500
            else:
                scheduling_agent.notify(
                    f"❌ Calendar fetch error: {busy_slots}",
                    'warning'
                )
                return jsonify({'success': False, 'error': busy_slots}), 500
        
        scheduling_agent.notify(
            f"✅ Found {len(busy_slots)} available time slots from HR calendar",
            'success',
            reasoning=f"Analyzed calendar and computed free 30-minute slots between busy periods"
        )
        
        # Return in the "slots" field for frontend compatibility
        return jsonify({'success': True, 'slots': busy_slots})
    except Exception as e:
        scheduling_agent.notify(
            f"❌ Error fetching availability: {str(e)}",
            'warning'
        )
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/propose', methods=['POST'])
def propose_interview_slots():
    """Autonomous AI agent proposes optimal interview slots"""
    try:
        data = request.get_json() or {}
        availability = data.get('availability', [])
        emails = db.get_interview_candidate_emails()
        candidate_count = len(emails)
        
        # Use autonomous scheduling agent
        proposals = scheduling_agent.propose_best_slots(availability, candidate_count)
        
        return jsonify({'success': True, 'proposals': proposals[:5]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create_google_calendar_event_logic(hr_email, event_body, conference_data=None):
    """
    Helper to create a Google Calendar event using Service Account (primary) or OAuth (fallback).
    Returns the created event object or raises an exception.
    """
    # Try service account first
    try:
        if not GOOGLE_SERVICE_ACCOUNT_FILE:
            raise Exception('Service account not configured')
        
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
            subject=hr_email
        )
        service = build('calendar', 'v3', credentials=creds)
        insert_kwargs = {'calendarId': hr_email, 'body': event_body}
        if conference_data:
            event_body['conferenceData'] = conference_data
            insert_kwargs['conferenceDataVersion'] = 1
        
        return service.events().insert(**insert_kwargs).execute()
        
    except Exception as sa_err:
        logger.warning(f"Service account calendar creation failed: {sa_err}. Trying OAuth fallback...")
        # OAuth fallback on primary calendar
        try:
            oauth_service = build_calendar_service_oauth()
            insert_kwargs = {'calendarId': 'primary', 'body': event_body}
            if conference_data:
                event_body['conferenceData'] = conference_data
                insert_kwargs['conferenceDataVersion'] = 1
            
            return oauth_service.events().insert(**insert_kwargs).execute()
        except Exception as oauth_err:
            raise Exception(f"Both Service Account and OAuth failed. SA: {sa_err}, OAuth: {oauth_err}")

@app.route('/api/interviews/schedule', methods=['POST'])
def schedule_interviews():
    try:
        data = request.get_json() or {}
        start = data.get('start')
        end = data.get('end')
        hr_email = data.get('hr_email')
        meeting_link_input = data.get('meeting_link', '')
        timezone = data.get('timezone', 'Asia/Kolkata')
        if not start or not end:
            return jsonify({'success': False, 'error': 'start and end are required'}), 400
        emails = db.get_interview_candidate_emails()

        # Always create calendar event (use provided link or auto-create Meet)
        meeting_link = meeting_link_input.strip()
        
        try:
            # Prepare event body
            start_utc = start.replace('Z', '+00:00') if start.endswith('Z') else start
            end_utc = end.replace('Z', '+00:00') if end.endswith('Z') else end
            dt_start = datetime.datetime.fromisoformat(start_utc)
            dt_end = datetime.datetime.fromisoformat(end_utc)
            if dt_start.tzinfo is None:
                dt_start = dt_start.replace(tzinfo=datetime.timezone.utc)
            if dt_end.tzinfo is None:
                dt_end = dt_end.replace(tzinfo=datetime.timezone.utc)
            tz = pytz.timezone(timezone)
            dt_start_local = dt_start.astimezone(tz)
            dt_end_local = dt_end.astimezone(tz)
            start_iso = dt_start_local.isoformat()
            end_iso = dt_end_local.isoformat()

            event = {
                'summary': 'Interview',
                'start': { 'dateTime': start_iso, 'timeZone': timezone },
                'end': { 'dateTime': end_iso, 'timeZone': timezone },
                'attendees': [{ 'email': e } for e in emails]
            }
            
            conferenceData = None
            if meeting_link:
                event['description'] = f'Interview Meeting Link: {meeting_link}'
            else:
                conferenceData = {
                    'createRequest': {
                        'requestId': str(uuid.uuid4())
                    }
                }
            
            created = create_google_calendar_event_logic(hr_email, event, conferenceData)
            
            # Extract meeting link from created event if we auto-created Meet
            if not meeting_link and created:
                meeting_link = created.get('hangoutLink') or created.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri') or ''
                logger.info(f"Created calendar event with Meet link: {meeting_link}")
            elif created:
                logger.info(f"Created calendar event with provided link: {meeting_link}")
                
        except Exception as create_err:
            # Log error but continue - still save to DB and send emails
            logger.error(f"Failed to create calendar event: {str(create_err)}")
            if not meeting_link:
                meeting_link = 'Calendar event creation failed - link not available'

        scheduled = []
        for email in emails:
            schedule_id = db.save_interview_schedule(email, start, end, hr_email, meeting_link)
            scheduled.append({'email': email, 'schedule_id': schedule_id})
        
        scheduling_agent.notify(
            f"✅ Scheduled interviews for {len(scheduled)} candidates",
            'success',
            reasoning=f"Created calendar events and sent notifications to all {len(scheduled)} candidates"
        )

        # Send notification emails if SMTP configured
        try:
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            sender_email = os.getenv('SENDER_EMAIL')
            sender_password = os.getenv('SENDER_PASSWORD')
            if sender_email and sender_password:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(sender_email, sender_password)
                for email in emails:
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = email
                    msg['Subject'] = 'Interview Scheduled'
                    body = f"""
Dear Candidate,

Your interview has been scheduled.

Start: {start}
End: {end}
Meeting link: {meeting_link or 'Will be shared separately'}

Regards,
HR
"""
                    msg.attach(MIMEText(body, 'plain'))
                    server.sendmail(sender_email, email, msg.as_string())
                server.quit()
        except Exception as mail_err:
            logger.warning(f"Email sending failed: {mail_err}")

        return jsonify({'success': True, 'scheduled': scheduled, 'meeting_link': meeting_link})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/create_event', methods=['POST'])
def create_calendar_event():
    try:
        data = request.get_json() or {}
        hr_email = data.get('hr_email')
        start = data.get('start')
        end = data.get('end')
        attendees = data.get('attendees', [])  # list of emails
        title = data.get('title', 'Interview')
        timezone = data.get('timezone', 'Asia/Kolkata')  # Default to IST
        create_meet = bool(data.get('create_meet', True))
        if not start or not end:
            return jsonify({'success': False, 'error': 'start and end are required'}), 400
        
        # Parse UTC datetime and convert to specified timezone
        try:
            # Remove Z if present and parse as UTC
            start_utc = start.replace('Z', '+00:00') if start.endswith('Z') else start
            end_utc = end.replace('Z', '+00:00') if end.endswith('Z') else end
            dt_start = datetime.datetime.fromisoformat(start_utc)
            dt_end = datetime.datetime.fromisoformat(end_utc)
            
            # Ensure timezone aware
            if dt_start.tzinfo is None:
                dt_start = dt_start.replace(tzinfo=datetime.timezone.utc)
            if dt_end.tzinfo is None:
                dt_end = dt_end.replace(tzinfo=datetime.timezone.utc)
            
            # Convert to target timezone (Google Calendar expects local time with timezone)
            tz = pytz.timezone(timezone)
            dt_start_local = dt_start.astimezone(tz)
            dt_end_local = dt_end.astimezone(tz)
            
            # Format for Google Calendar API
            start_iso = dt_start_local.isoformat()
            end_iso = dt_end_local.isoformat()
        except Exception as parse_err:
            # Fallback: use as-is but add timezone
            start_iso = start.replace('Z', '') if start.endswith('Z') else start
            end_iso = end.replace('Z', '') if end.endswith('Z') else end
        
        # Build event body with timezone
        event = {
            'summary': title,
            'start': { 'dateTime': start_iso, 'timeZone': timezone },
            'end': { 'dateTime': end_iso, 'timeZone': timezone },
            'attendees': [{ 'email': e } for e in attendees if isinstance(e, str) and '@' in e]
        }
        
        conferenceData = None
        if create_meet:
            conferenceData = {
                'createRequest': {
                    'requestId': str(uuid.uuid4())
                }
            }
            
        created = create_google_calendar_event_logic(hr_email, event, conferenceData)
        
        meet_link = created.get('hangoutLink') or created.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri')
        return jsonify({'success': True, 'event_id': created.get('id'), 'htmlLink': created.get('htmlLink'), 'meet_link': meet_link})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/chat', methods=['POST'])
def chat_interview_agent():
    """Chat endpoint for interview scheduler"""
    try:
        data = request.get_json() or {}
        message = data.get('message', '').lower()
        hr_email = data.get('hr_email')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400

        response_text = ""
        slots = []
        action = None
        action_data = {}
        
        # Intent: Suggest Slots
        if 'suggest' in message or 'slot' in message or 'schedule' in message:
            # Trigger slot proposal logic
            busy_slots = get_google_calendar_availability(hr_email)
            if isinstance(busy_slots, str): # Error case
                try:
                    busy_slots = get_google_calendar_availability_oauth()
                except Exception:
                    return jsonify({'success': True, 'response': "I couldn't access your calendar. Please check your permissions."})

            emails = db.get_interview_candidate_emails()
            candidate_count = len(emails)
            
            if candidate_count == 0:
                 return jsonify({'success': True, 'response': "There are no candidates to schedule interviews for."})

            proposals = scheduling_agent.propose_best_slots(busy_slots, candidate_count)
            slots = proposals[:3] # Return top 3
            response_text = f"Based on your calendar and the number of candidates ({candidate_count}), here are some suggested time slots:"
        
        # Intent: Count Candidates
        elif 'how many' in message or 'count' in message:
            emails = db.get_interview_candidate_emails()
            count = len(emails)
            response_text = f"There are currently {count} candidates in the interview list."
            
        # Intent: Remove Candidate
        elif 'remove' in message or 'delete' in message:
            # Extract email using simple logic (or regex)
            import re
            email_match = re.search(r'[\w\.-]+@[\w\.-]+', message)
            if email_match:
                email_to_remove = email_match.group(0)
                # We don't remove directly here, we tell frontend to do it or call another endpoint
                # But to be "agentic", we should probably do it or instruct frontend
                # Let's instruct frontend to trigger the removal flow
                response_text = f"I'll help you remove {email_to_remove}. Please confirm."
                action = "REMOVE_CANDIDATE"
                action_data = {"email": email_to_remove}
            else:
                response_text = "Who would you like to remove? Please specify the email address."
                
        # Intent: List Candidates
        elif 'list' in message or 'show candidates' in message:
            emails = db.get_interview_candidate_emails()
            if emails:
                response_text = "Here are the candidates:\n" + "\n".join([f"- {e}" for e in emails[:10]])
                if len(emails) > 10:
                    response_text += f"\n...and {len(emails)-10} more."
            else:
                response_text = "The candidate list is empty."

        else:
            response_text = "I can help you schedule interviews. Try asking me to 'suggest slots', 'count candidates', or 'remove [email]'."

        return jsonify({
            'success': True, 
            'response': response_text,
            'slots': slots,
            'action': action,
            'data': action_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/candidates-with-schedules', methods=['GET'])
def get_interview_candidates_with_schedules():
    try:
        candidates = db.get_candidates_with_schedules()
        return jsonify({'success': True, 'candidates': candidates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/reject-candidate', methods=['POST'])
def reject_interview_candidate():
    try:
        data = request.get_json() or {}
        candidate_email = data.get('candidate_email')
        if not candidate_email:
            return jsonify({'success': False, 'error': 'candidate_email is required'}), 400
            
        success = db.reject_candidate(candidate_email)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interviews/select-candidate', methods=['POST'])
def select_interview_candidate():
    try:
        data = request.get_json() or {}
        candidate_email = data.get('candidate_email')
        if not candidate_email:
            return jsonify({'success': False, 'error': 'candidate_email is required'}), 400
            
        success = db.select_candidate(candidate_email)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("===============================")
    print("Interview Scheduler Flask API Ready!")
    print("Listening for requests on http://localhost:5002 ...")
    print("===============================")
    # Production ready: disable debug, allow port configuration
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port, debug=False)



