#!/usr/bin/env python
"""Wrapper script to run interview API with proper Python path"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add agents/interview to path for local imports
interview_path = os.path.join(project_root, 'agents', 'interview')
if interview_path not in sys.path:
    sys.path.insert(0, interview_path)

# Import and run the app
from agents.interview.api import app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port, debug=False)
