#!/bin/bash
cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║           🚀  FINANCIAL REPORT ANALYZER                    ║"
echo "║               (Streamlit Dashboard)                        ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed.${NC}"
    exit 1
fi

# Create virtual env if not exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies (only if requirements.txt updated)
if [ ! -f ".installed" ] || [ "requirements.txt" -nt ".installed" ]; then
    echo -e "${BLUE}⬇️  Updating/Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install --prefer-binary -r requirements.txt
    touch .installed
else
    echo -e "${GREEN}✓ Dependencies up to date.${NC}"
fi

# Run Streamlit
echo -e "${BLUE}🌐 Launching Dashboard in your browser...${NC}"
echo -e "   If it doesn't open, visit: http://localhost:8501"
echo ""

python -m streamlit run app_streamlit.py
