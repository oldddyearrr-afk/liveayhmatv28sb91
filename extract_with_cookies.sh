#!/bin/bash

# ═══════════════════════════════════════════════════════════
# استخراج رابط فيسبوك باستخدام الكوكيز
# ═══════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  استخراج رابط البث باستخدام الكوكيز      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# تحقق من وجود yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} yt-dlp غير مثبت!"
    echo -e "${BLUE}[INFO]${NC} جاري التثبيت..."
    pip install -U yt-dlp
    echo ""
fi

# تعليمات الحصول على الكوكيز
echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
echo -e "${YELLOW}الخطوة 1: احصل على ملف الكوكيز${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}للحصول على ملف cookies.txt من متصفحك:${NC}"
echo ""
echo -e "${GREEN}الطريقة الأولى - استخدام إضافة المتصفح:${NC}"
echo ""
echo -e "  ${BLUE}لـ Chrome:${NC}"
echo -e "  1. ثبت إضافة: ${GREEN}Get cookies.txt LOCALLY${NC}"
echo -e "     الرابط: chrome.google.com/webstore"
echo -e "     ابحث عن: Get cookies.txt LOCALLY"
echo ""
echo -e "  ${BLUE}لـ Firefox:${NC}"
echo -e "  1. ثبت إضافة: ${GREEN}cookies.txt${NC}"
echo -e "     الرابط: addons.mozilla.org"
echo -e "     ابحث عن: cookies.txt"
echo ""
echo -e "  ${BLUE}بعد تثبيت الإضافة:${NC}"
echo -e "  2. اذهب إلى ${GREEN}facebook.com${NC} وسجل دخولك"
echo -e "  3. اضغط على أيقونة الإضافة"
echo -e "  4. اضغط ${GREEN}Export${NC} أو ${GREEN}Download${NC}"
echo -e "  5. احفظ الملف باسم: ${GREEN}facebook_cookies.txt${NC}"
echo ""
echo -e "${GREEN}الطريقة الثانية - يدوياً (للمحترفين):${NC}"
echo -e "  استخدم F12 → Application → Cookies → facebook.com"
echo ""
echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
echo ""

# طلب ملف الكوكيز
echo -e "${CYAN}أدخل مسار ملف الكوكيز:${NC}"
echo -e "${BLUE}(مثال: facebook_cookies.txt أو ./cookies.txt)${NC}"
read -p "المسار: " COOKIE_FILE

if [ -z "$COOKIE_FILE" ]; then
    echo -e "${RED}[ERROR]${NC} لم تدخل مسار الملف!"
    exit 1
fi

if [ ! -f "$COOKIE_FILE" ]; then
    echo -e "${RED}[ERROR]${NC} الملف غير موجود: $COOKIE_FILE"
    echo ""
    echo -e "${YELLOW}نصيحة:${NC} تأكد من أن الملف في نفس المجلد أو أدخل المسار الكامل"
    exit 1
fi

echo -e "${GREEN}[SUCCESS]${NC} تم العثور على ملف الكوكيز!"
echo ""

# طلب رابط البث
echo -e "${CYAN}أدخل رابط البث على فيسبوك:${NC}"
read -p "الرابط: " FB_URL

if [ -z "$FB_URL" ]; then
    echo -e "${RED}[ERROR]${NC} لم تدخل أي رابط!"
    exit 1
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${BLUE}جاري استخراج الرابط...${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""

# محاولة استخراج الرابط
EXTRACTED_URL=$(yt-dlp --cookies "$COOKIE_FILE" --get-url "$FB_URL" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          تم الاستخراج بنجاح! ✓           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}الرابط المباشر:${NC}"
    echo -e "${GREEN}$EXTRACTED_URL${NC}"
    echo ""
    
    # حفظ الرابط في ملف
    echo "$EXTRACTED_URL" > extracted_url.txt
    echo -e "${BLUE}[INFO]${NC} تم حفظ الرابط في: ${GREEN}extracted_url.txt${NC}"
    echo ""
    
    # سؤال عن تحديث config.sh
    echo -e "${YELLOW}هل تريد تحديث config.sh تلقائياً؟ (y/n)${NC}"
    read -p "اختيارك: " UPDATE_CONFIG
    
    if [[ "$UPDATE_CONFIG" =~ ^[Yy]$ ]]; then
        # عمل نسخة احتياطية
        cp config.sh config.sh.backup.$(date +%Y%m%d_%H%M%S)
        
        # تحديث SOURCE
        sed -i "s|^SOURCE=.*|SOURCE=\"$EXTRACTED_URL\"|" config.sh
        
        echo -e "${GREEN}[SUCCESS]${NC} تم تحديث config.sh بنجاح!"
        echo -e "${BLUE}[INFO]${NC} تم إنشاء نسخة احتياطية"
        echo ""
        echo -e "${CYAN}الآن يمكنك بدء البث:${NC}"
        echo -e "  ${GREEN}./control.sh start${NC}"
    else
        echo -e "${YELLOW}[INFO]${NC} يمكنك نسخ الرابط من ملف: extracted_url.txt"
    fi
    
else
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║            فشل الاستخراج ✗                ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}تفاصيل الخطأ:${NC}"
    echo "$EXTRACTED_URL"
    echo ""
    echo -e "${YELLOW}الحلول المحتملة:${NC}"
    echo -e "  1. تأكد من أن ملف الكوكيز صحيح وحديث"
    echo -e "  2. تأكد من أنك مسجل دخول على فيسبوك"
    echo -e "  3. جرب تصدير الكوكيز مرة أخرى"
    echo -e "  4. تأكد من أن البث ${GREEN}مباشر الآن 🔴${NC}"
    echo -e "  5. إذا كان البث خاص، تأكد من أن حسابك لديه صلاحية المشاهدة"
fi

echo ""
