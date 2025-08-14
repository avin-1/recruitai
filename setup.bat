@echo off
setlocal

rem Define the main project directory
set "PROJECT_DIR=recruitai"

rem --- Create Main Project Directory ---
echo Creating main project directory: %PROJECT_DIR%
mkdir %PROJECT_DIR%
if not exist %PROJECT_DIR% (
    echo Error: Could not create %PROJECT_DIR%. Exiting.
    exit /b 1
)
cd %PROJECT_DIR%

rem --- Create Agent Directories ---
echo Creating agents/ directory...
mkdir agents
echo This directory contains the logic for each individual agent. > agents\agents_info.txt
type nul > agents\__init__.py

rem --- Create Core Directories ---
echo Creating core/ directory...
mkdir core
echo This directory contains central components and utilities. > core\core_info.txt
type nul > core\__init__.py

rem --- Create Prompts Directory ---
echo Creating prompts/ directory...
mkdir prompts
echo This directory holds the LLM prompt templates. > prompts\prompts_info.txt
type nul > prompts\__init__.py

rem --- Create Data Directories ---
echo Creating data/ directory...
mkdir data
echo This directory is for storing raw and processed data. > data\data_info.txt
mkdir data\raw_resumes
echo Raw uploaded resume files. > data\raw_resumes\raw_resumes_info.txt
mkdir data\processed_data
echo Processed JSON profiles and other structured data. > data\processed_data\processed_data_info.txt
mkdir data\test_data
echo Sample JDs and resumes for testing. > data\test_data\test_data_info.txt

rem --- Create Templates Directory ---
echo Creating templates/ directory...
mkdir templates
echo This directory contains HTML templates for the frontend. > templates\templates_info.txt

rem --- Create Static Directories ---
echo Creating static/ directory...
mkdir static
echo This directory holds static frontend assets like CSS and JS. > static\static_info.txt
mkdir static\css
echo CSS stylesheets. > static\css\css_info.txt
mkdir static\js
echo JavaScript files. > static\js\js_info.txt

rem --- Create Tests Directories ---
echo Creating tests/ directory...
mkdir tests
echo This directory contains unit and integration tests. > tests\tests_info.txt
type nul > tests\__init__.py

rem --- Create Root Project Files ---
echo Creating root project files...
echo Main application entry point. > app.py.txt
echo Python package dependencies. > requirements.txt.txt
echo Environment variables (API keys, database credentials). > .env.txt

echo.
echo Directory structure and placeholder files created successfully in ./%PROJECT_DIR%/
endlocal