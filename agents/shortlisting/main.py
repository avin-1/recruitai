#!/usr/bin/env python3
"""
Main entry point for the shortlisting test management system
"""

from api import app
from database import DatabaseManager

def initialize_system():
    """Initialize the database and system"""
    db = DatabaseManager()
    print("Database initialized successfully")

if __name__ == '__main__':
    try:
        initialize_system()
        print("Starting Test Management API on http://localhost:5001")
        print("Note: Disable debug mode in production to prevent auto-restarts")
        app.run(debug=False, host='0.0.0.0', port=5001, use_reloader=False)
    except Exception as e:
        print(f"Fatal error starting server: {e}")
        import traceback
        traceback.print_exc()
