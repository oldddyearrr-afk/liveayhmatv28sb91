#!/bin/bash

# ═══════════════════════════════════════════════════════════
# Extract Facebook Live Stream URL
# ═══════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Facebook Live Stream URL Extractor       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}IMPORTANT:${NC} You need to provide the Facebook Live Video URL"
echo -e "Example: https://www.facebook.com/username/videos/1234567890"
echo ""

read -p "Enter Facebook Live Video URL: " FB_VIDEO_URL

if [ -z "$FB_VIDEO_URL" ]; then
    echo -e "${RED}[ERROR]${NC} No URL provided!"
    exit 1
fi

echo ""
echo -e "${BLUE}[INFO]${NC} Attempting to extract stream URL..."
echo -e "${YELLOW}[NOTE]${NC} This only works if the stream is currently LIVE!"
echo ""

# Try to extract using youtube-dl/yt-dlp (if available)
if command -v yt-dlp &> /dev/null; then
    echo -e "${BLUE}[INFO]${NC} Using yt-dlp to extract stream..."
    yt-dlp -f best --get-url "$FB_VIDEO_URL" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}[SUCCESS]${NC} Stream URL extracted!"
        echo -e "${YELLOW}[NOTE]${NC} This URL will expire after the stream ends"
    else
        echo -e "${RED}[ERROR]${NC} Could not extract stream URL"
        echo -e "${YELLOW}Possible reasons:${NC}"
        echo "  - Stream is not live yet"
        echo "  - Video is private/restricted"
        echo "  - Facebook blocked the extraction"
    fi
elif command -v youtube-dl &> /dev/null; then
    echo -e "${BLUE}[INFO]${NC} Using youtube-dl to extract stream..."
    youtube-dl -f best --get-url "$FB_VIDEO_URL" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}[SUCCESS]${NC} Stream URL extracted!"
        echo -e "${YELLOW}[NOTE]${NC} This URL will expire after the stream ends"
    else
        echo -e "${RED}[ERROR]${NC} Could not extract stream URL"
    fi
else
    echo -e "${RED}[ERROR]${NC} Neither yt-dlp nor youtube-dl is installed!"
    echo ""
    echo -e "${BLUE}[INFO]${NC} Installing yt-dlp..."
    echo ""
    
    if command -v pip3 &> /dev/null; then
        pip3 install -U yt-dlp
        echo ""
        echo -e "${GREEN}[SUCCESS]${NC} yt-dlp installed! Run this script again."
    elif command -v pip &> /dev/null; then
        pip install -U yt-dlp
        echo ""
        echo -e "${GREEN}[SUCCESS]${NC} yt-dlp installed! Run this script again."
    else
        echo -e "${RED}[ERROR]${NC} pip not found! Cannot install yt-dlp"
    fi
fi

echo ""
echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
echo -e "${YELLOW}ملاحظة: إذا فشل الاستخراج التلقائي${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}الحل البديل - الاستخراج اليدوي:${NC}"
echo ""
echo -e "1. افتح البث في متصفح Chrome/Firefox"
echo -e "2. اضغط ${GREEN}F12${NC} لفتح أدوات المطور"
echo -e "3. اذهب لتبويب ${GREEN}Network${NC} (الشبكة)"
echo -e "4. ابحث عن: ${GREEN}.m3u8${NC} في مربع البحث"
echo -e "5. شغل الفيديو أو حدث الصفحة (F5)"
echo -e "6. اضغط بيمين على ملف ${GREEN}.m3u8${NC}"
echo -e "7. اختر ${GREEN}Copy → Copy link address${NC}"
echo -e "8. استخدم الرابط المنسوخ في config.sh"
echo ""
echo -e "${BLUE}مثال الرابط المطلوب:${NC}"
echo -e "${GREEN}https://video.xx.fbcdn.net/.../xxx.m3u8?token=...${NC}"
echo ""
