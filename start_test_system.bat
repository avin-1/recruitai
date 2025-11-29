@echo off
echo Starting Test Management System...
echo.

echo Starting Backend API Server...
start "Test Management API" cmd /k "cd agents\shortlisting && python start_server.py"

echo.
echo Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo Starting Frontend Development Server...
start "Frontend Dev Server" cmd /k "cd front && npm run dev"

echo.
echo System started successfully!
echo.
echo HR Interface: http://localhost:3000/hr-tests
echo API Server: http://localhost:5001
echo Candidate Test URL: http://localhost:3000/test/{test_id}
echo.
echo Press any key to exit...
pause > nul
