#!/usr/bin/env python
"""Wrapper script to run shortlisting API with proper Python path"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add agents/shortlisting to path for local imports
shortlisting_path = os.path.join(project_root, 'agents', 'shortlisting')
if shortlisting_path not in sys.path:
    sys.path.insert(0, shortlisting_path)

# Import and run the app
from agents.shortlisting.api import app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
