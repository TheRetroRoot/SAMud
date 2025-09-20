#!/bin/bash
# SAMUD Server Start Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}         San Antonio MUD (SAMUD) Server Launcher${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python $required_version or higher is required (found $python_version)${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $python_version${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo -e "${BLUE}Checking dependencies...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Environment file created${NC}"
fi

# Create data directory if it doesn't exist
mkdir -p data
echo -e "${GREEN}✓ Data directory ready${NC}"

# Optional: Run with restart on crash
if [ "$1" = "--auto-restart" ]; then
    echo -e "${YELLOW}Running with auto-restart enabled${NC}"
    while true; do
        echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}    SAMUD Server Starting on port 2323${NC}"
        echo -e "${GREEN}    Connect with: telnet localhost 2323${NC}"
        echo -e "${GREEN}    Auto-restart: ENABLED${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}\n"

        python src/server.py

        echo -e "\n${RED}Server stopped. Restarting in 5 seconds...${NC}"
        echo -e "${YELLOW}Press Ctrl+C twice to stop auto-restart${NC}"
        sleep 5
    done
else
    # Normal run
    echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}    SAMUD Server Starting on port 2323${NC}"
    echo -e "${GREEN}    Connect with: telnet localhost 2323${NC}"
    echo -e "${GREEN}    Press Ctrl+C to stop the server${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}\n"

    python src/server.py
fi