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
print("Loading upload_api...", flush=True)
from backend.upload_api import app as upload_app
print("Loaded upload_api.", flush=True)

print("Loading shortlisting_api...", flush=True)
from agents.shortlisting.api import app as shortlisting_app
print("Loaded shortlisting_api.", flush=True)

print("Loading interview_api...", flush=True)
from agents.interview.api import app as interview_app
print("Loaded interview_api.", flush=True)

print("Loading settings_api...", flush=True)
from backend.settings_api import app as settings_app
print("Loaded settings_api.", flush=True)

# ... imports ...
from flask import Flask, send_from_directory

# ... existing code ...

# Frontend App
frontend_dist = os.path.join(project_root, 'front', 'dist')
frontend_app = Flask(__name__, static_folder=frontend_dist, static_url_path='/')

@frontend_app.route('/')
def serve_index():
    return send_from_directory(frontend_app.static_folder, 'index.html')

@frontend_app.route('/<path:path>')
def serve_static(path):
    # Check if file exists in dist
    full_path = os.path.join(frontend_app.static_folder, path)
    if os.path.exists(full_path):
        return send_from_directory(frontend_app.static_folder, path)
    # Fallback to index.html for SPA routing
    return send_from_directory(frontend_app.static_folder, 'index.html')

def application(environ, start_response):
    """
    Custom WSGI middleware to dispatch requests to different Flask apps
    based on the path prefix and Accept header.
    """
    path = environ.get('PATH_INFO', '')
    accept = environ.get('HTTP_ACCEPT', '')
    
    # 1. API Routes (Explicit prefixes)
    if path.startswith('/api/interviews'):
        return interview_app(environ, start_response)
    
    elif path.startswith('/api/settings'):
        return settings_app(environ, start_response)
    
    elif path.startswith('/api/tests') or \
         path.startswith('/api/notifications') or \
         path.startswith('/api/candidates'):
        return shortlisting_app(environ, start_response)

    # 2. Frontend Static Assets (Vite uses /assets)
    if path.startswith('/assets/'):
        return frontend_app(environ, start_response)

    # 3. Backend Static Files (Social Images, etc.)
    # MUST come before root/frontend catch-all
    if path.startswith('/static/'):
        return upload_app(environ, start_response)

    # 4. Root -> Frontend
    if path == '/':
        return frontend_app(environ, start_response)

    # 5. Collisions (/jobs, /profiles, etc.)
    # If browser requesting HTML -> Frontend
    if 'text/html' in accept:
         return frontend_app(environ, start_response)

    # 6. Default to upload_api for Core API routes (/upload, /apply, etc.)
    return upload_app(environ, start_response)

# Apply ProxyFix to handle headers from tunnels (ngrok, pinggy, etc.)
# This ensures request.host_url matches the public URL, not localhost
from werkzeug.middleware.proxy_fix import ProxyFix
application = ProxyFix(application, x_for=1, x_proto=1, x_host=1, x_prefix=1)

app = application # For Gunicorn

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Unified Server (Frontend + Backend) on port {port}...")
    run_simple('0.0.0.0', port, application, use_reloader=True)
