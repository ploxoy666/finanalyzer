@echo off
setlocal
title Financial Alpha Intelligence - Launcher

echo ======================================================
echo 🚀 Financial Alpha Intelligence - Windows Launcher
echo ======================================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org
    pause
    exit /b
)

:: Create and activate virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

echo [INFO] Activating environment...
call venv\Scripts\activate

:: Check if requirements are installed
if not exist "venv\.installed" (
    echo [INFO] Installing dependencies (this may take a few minutes)...
    pip install --upgrade pip
    pip install -r requirements.txt
    echo done > venv\.installed
)

echo [INFO] Starting the application...
echo ------------------------------------------------------
streamlit run app_streamlit.py

pause
