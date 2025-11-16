#!/bin/bash

LOG_DIR="logs"
MAX_LOGS_TO_KEEP=10

if [ ! -d "$LOG_DIR" ]; then
    echo "مجلد اللوجات غير موجود"
    exit 0
fi

TOTAL_LOGS=$(ls -1 "$LOG_DIR"/*.log 2>/dev/null | wc -l)

if [ "$TOTAL_LOGS" -eq 0 ]; then
    echo "✓ لا توجد ملفات لوج للحذف"
    exit 0
fi

echo "📊 إجمالي ملفات اللوج: $TOTAL_LOGS"

if [ "$TOTAL_LOGS" -gt "$MAX_LOGS_TO_KEEP" ]; then
    LOGS_TO_DELETE=$((TOTAL_LOGS - MAX_LOGS_TO_KEEP))
    echo "🗑️  سيتم حذف $LOGS_TO_DELETE ملف قديم..."
    
    ls -t "$LOG_DIR"/*.log 2>/dev/null | tail -n +$((MAX_LOGS_TO_KEEP + 1)) | xargs rm -f
    
    echo "✅ تم حذف الملفات القديمة"
    echo "✓ تم الاحتفاظ بآخر $MAX_LOGS_TO_KEEP ملفات فقط"
else
    echo "✓ عدد الملفات ($TOTAL_LOGS) أقل من الحد الأقصى ($MAX_LOGS_TO_KEEP)"
fi

REMAINING=$(ls -1 "$LOG_DIR"/*.log 2>/dev/null | wc -l)
echo "📁 الملفات المتبقية: $REMAINING"
