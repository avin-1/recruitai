@echo off

:: ------------------------------------------------------------
:: REDAI Production Startup Script
:: ------------------------------------------------------------

:: Get the project root directory
set PROJECT_ROOT=%~dp0

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Ensure waitress is installed (quietly ignore errors)
pip install waitress >nul 2>&1 || echo [WARN] waitress install failed or already present

:: ------------------------------------------------------------
:: Start each backend service in its own console window
:: Using wrapper scripts to handle Python imports correctly
:: ------------------------------------------------------------
start "Upload API" cmd /k "cd /d %PROJECT_ROOT% && waitress-serve --host=0.0.0.0 --port=8080 run_upload_api:app"
start "Shortlisting API" cmd /k "cd /d %PROJECT_ROOT% && waitress-serve --host=0.0.0.0 --port=5001 run_shortlisting_api:app"
start "Interview API" cmd /k "cd /d %PROJECT_ROOT% && waitress-serve --host=0.0.0.0 --port=5002 run_interview_api:app"
start "Settings API" cmd /k "cd /d %PROJECT_ROOT% && waitress-serve --host=0.0.0.0 --port=5003 run_settings_api:app"

:: ------------------------------------------------------------
:: Inform the user
:: ------------------------------------------------------------

echo.
echo Production servers started.
echo Frontend should be built and served using a static file server or Nginx.
echo To run frontend locally for testing: cd front ^&^& npm run dev
echo.

pause
