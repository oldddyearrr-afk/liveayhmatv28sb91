#!/bin/bash

echo "════════════════════════════════════════"
echo "  تحديث رابط البث في config.sh"
echo "════════════════════════════════════════"
echo ""
echo "الصق الرابط الذي استخرجته من المتصفح:"
read NEW_SOURCE

if [ -z "$NEW_SOURCE" ]; then
    echo "[ERROR] لم تدخل أي رابط!"
    exit 1
fi

# Backup old config
cp config.sh config.sh.backup

# Update SOURCE in config.sh
sed -i "s|^SOURCE=.*|SOURCE=\"$NEW_SOURCE\"|" config.sh

echo ""
echo "[SUCCESS] تم تحديث رابط البث بنجاح!"
echo ""
echo "الرابط الجديد:"
echo "$NEW_SOURCE"
echo ""
echo "لبدء البث الآن، استخدم:"
echo "  ./control.sh start"
echo ""
