#!/bin/bash

# ═══════════════════════════════════════════════════════════
# دليل البدء السريع
# ═══════════════════════════════════════════════════════════

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

clear
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${BLUE}    📺 Facebook Live Stream - Quick Start ${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}Step 1: Extract stream link (optional)${NC}"
echo "  Command: ./extract_link.sh"
echo ""

echo -e "${YELLOW}Step 2: Add stream key in Replit Secrets${NC}"
echo "  1. Open Secrets tab (🔒 icon in sidebar)"
echo "  2. Add new Secret:"
echo "     Key: FB_STREAM_KEY"
echo "     Value: [Your Facebook Stream Key]"
echo ""

echo -e "${YELLOW}Step 3: Configure source in config.sh${NC}"
echo "  Edit SOURCE variable with your stream URL"
echo ""

echo -e "${YELLOW}Step 4: Start streaming${NC}"
echo "  Command: ./control.sh start"
echo ""

echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""

echo "What would you like to do?"
echo ""
echo "  1) Extract stream link"
echo "  2) Start streaming (if ready)"
echo "  3) Show status"
echo "  4) Exit"
echo ""

read -p "Your choice: " choice

case $choice in
    1)
        ./extract_link.sh
        ;;
    2)
        ./control.sh start
        ;;
    3)
        ./control.sh status
        ;;
    4)
        echo "Goodbye! 👋"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
