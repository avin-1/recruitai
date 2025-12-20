from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SELECTED_DB = os.path.join(BASE_DIR, 'selected_candidates.db')
INTERVIEW_DB = os.path.join(BASE_DIR, 'interview.db')

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/analytics/summary', methods=['GET'])
def get_summary():
    summary = {
        'total_candidates': 0,
        'shortlisted': 0,
        'interviews_scheduled': 0,
        'offers_sent': 0
    }
    
    try:
        # Get total candidates (using selected_candidates as proxy for now, or count unique emails)
        conn_sel = get_db_connection(SELECTED_DB)
        cursor_sel = conn_sel.cursor()
        
        # Total candidates (unique emails in selected_candidates)
        cursor_sel.execute("SELECT COUNT(DISTINCT candidate_email) FROM selected_candidates")
        summary['total_candidates'] = cursor_sel.fetchone()[0] or 0
        
        # Shortlisted (assuming all in selected_candidates are shortlisted/selected)
        summary['shortlisted'] = summary['total_candidates']
        
        conn_sel.close()
        
        # Get interview stats
        if os.path.exists(INTERVIEW_DB):
            conn_int = get_db_connection(INTERVIEW_DB)
            cursor_int = conn_int.cursor()
            
            # Interviews Scheduled
            cursor_int.execute("SELECT COUNT(*) FROM interview_schedules")
            summary['interviews_scheduled'] = cursor_int.fetchone()[0] or 0
            
            # Offers Sent
            cursor_int.execute("SELECT COUNT(*) FROM interview_results WHERE offer_letter_sent = 1")
            summary['offers_sent'] = cursor_int.fetchone()[0] or 0
            
            conn_int.close()
            
    except Exception as e:
        print(f"Error fetching summary: {e}")
        return jsonify({'error': str(e)}), 500
        
    return jsonify(summary)

@app.route('/api/analytics/funnel', methods=['GET'])
def get_funnel():
    # Funnel: Applied -> Shortlisted -> Interviewed -> Offer
    # Note: 'Applied' might need to come from a different source if we have raw resumes, 
    # but for now we'll estimate or use available data.
    
    funnel = []
    try:
        conn_sel = get_db_connection(SELECTED_DB)
        cursor_sel = conn_sel.cursor()
        cursor_sel.execute("SELECT COUNT(DISTINCT candidate_email) FROM selected_candidates")
        shortlisted = cursor_sel.fetchone()[0] or 0
        conn_sel.close()
        
        interviews = 0
        offers = 0
        
        if os.path.exists(INTERVIEW_DB):
            conn_int = get_db_connection(INTERVIEW_DB)
            cursor_int = conn_int.cursor()
            cursor_int.execute("SELECT COUNT(*) FROM interview_schedules")
            interviews = cursor_int.fetchone()[0] or 0
            cursor_int.execute("SELECT COUNT(*) FROM interview_results WHERE offer_letter_sent = 1")
            offers = cursor_int.fetchone()[0] or 0
            conn_int.close()
            
        funnel = [
            {'name': 'Shortlisted', 'value': shortlisted, 'fill': '#8884d8'},
            {'name': 'Interviewed', 'value': interviews, 'fill': '#82ca9d'},
            {'name': 'Offer Sent', 'value': offers, 'fill': '#ffc658'}
        ]
        
    except Exception as e:
        print(f"Error fetching funnel: {e}")
        return jsonify({'error': str(e)}), 500
        
    return jsonify(funnel)

@app.route('/api/analytics/recent', methods=['GET'])
def get_recent():
    recent_activity = []
    try:
        if os.path.exists(INTERVIEW_DB):
            conn = get_db_connection(INTERVIEW_DB)
            cursor = conn.cursor()
            
            # Get recent interviews
            cursor.execute("""
                SELECT candidate_email, 'Interview Scheduled' as type, created_at as date 
                FROM interview_schedules 
                ORDER BY created_at DESC LIMIT 5
            """)
            rows = cursor.fetchall()
            for row in rows:
                recent_activity.append(dict(row))
                
            conn.close()
            
    except Exception as e:
        print(f"Error fetching recent: {e}")
        
    return jsonify(recent_activity)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5005))
    app.run(host='0.0.0.0', port=port)
