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
echo -e "${BLUE}    📺 Facebook Live Stream - البدء السريع ${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}الخطوة 1: استخراج رابط البث${NC}"
echo "  الأمر: ./extract_link.sh"
echo ""

echo -e "${YELLOW}الخطوة 2: ضبط مفتاح البث${NC}"
echo "  الأمر: export FB_STREAM_KEY='مفتاحك_هنا'"
echo ""

echo -e "${YELLOW}الخطوة 3: بدء البث${NC}"
echo "  الأمر: ./control.sh start"
echo ""

echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""

echo "هل تريد البدء الآن؟"
echo ""
echo "  1) استخراج رابط البث"
echo "  2) بدء البث (إذا كان الرابط جاهز)"
echo "  3) عرض الحالة"
echo "  4) خروج"
echo ""

read -p "اختيارك: " choice

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
        echo "مع السلامة! 👋"
        exit 0
        ;;
    *)
        echo "اختيار غير صحيح"
        ;;
esac
