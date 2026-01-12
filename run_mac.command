#!/bin/bash

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "======================================================"
echo "🚀 Financial Alpha Intelligence - Mac/Linux Launcher"
echo "======================================================"

# Check for Python
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python3 is not installed."
    echo "Please install Python 3.10+ using Homebrew or from python.org"
    read -p "Press enter to exit"
    exit
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[INFO] Activating environment..."
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "venv/.installed" ]; then
    echo "[INFO] Installing dependencies (this may take a few minutes)..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/.installed
fi

echo "[INFO] Starting the application..."
echo "------------------------------------------------------"
streamlit run app_streamlit.py
