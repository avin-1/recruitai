import os
import sys
from flask import Flask

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add backend directory to path
backend_path = os.path.join(project_root, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Add agents directories to path
sys.path.insert(0, os.path.join(project_root, 'agents', 'shortlisting'))
sys.path.insert(0, os.path.join(project_root, 'agents', 'interview'))

# Import the apps
# We need to be careful about imports to avoid circular dependencies or double initialization
# but since they are in separate files, it should be fine.
from backend.upload_api import app as upload_app
from agents.shortlisting.api import app as shortlisting_app
from agents.interview.api import app as interview_app
from backend.settings_api import app as settings_app

def application(environ, start_response):
    """
    Custom WSGI middleware to dispatch requests to different Flask apps
    based on the path prefix, WITHOUT stripping the prefix.
    """
    path = environ.get('PATH_INFO', '')
    
    # Routing logic based on analysis of route definitions
    if path.startswith('/api/interviews'):
        return interview_app(environ, start_response)
    
    elif path.startswith('/api/settings'):
        return settings_app(environ, start_response)
    
    elif path.startswith('/api/tests') or \
         path.startswith('/api/notifications') or \
         path.startswith('/api/candidates'):
        return shortlisting_app(environ, start_response)
        
    else:
        # Default to upload_api for root paths (/upload, /jobs, etc.)
        # and any other paths not matched above.
        return upload_app(environ, start_response)

app = application # For Gunicorn

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Unified API Gateway on port {port}...")
    run_simple('0.0.0.0', port, application, use_reloader=True)
