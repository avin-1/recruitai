@echo off
REM === Activate main venv in current window ===
call venv\Scripts\activate

REM === Start Backend (upload_api.py) in a new cmd ===
start cmd /k "call venv\Scripts\activate && cd backend && python upload_api.py"

REM === Start Agent JobDescription in a new cmd ===
start cmd /k "call venv\Scripts\activate && cd agents\jobdescription && python main.py"

REM === Start Agent ResumeAndMatching in a new cmd ===
start cmd /k "call venv\Scripts\activate && cd agents\resumeandmatching && python main.py"

REM === Start Frontend (npm run dev) in a new cmd ===
start cmd /k "cd front && npm run dev"

echo All services started in separate windows.
pause
