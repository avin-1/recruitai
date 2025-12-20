#!/usr/bin/env python3
"""
Start script for the shortlisting test management system
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, initialize_system

if __name__ == '__main__':
    try:
        print("Initializing Test Management System...")
        initialize_system()
        print("Starting Test Management API on http://localhost:5001")
        print("HR Interface: http://localhost:3000/hr-tests")
        print("Candidate Test URL format: http://localhost:3000/test/{test_id}")
        print("Note: Running with use_reloader=False to prevent crashes")
        app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)
    except Exception as e:
        print(f"Fatal error starting server: {e}")
        import traceback
        traceback.print_exc()
