#!/bin/bash
echo "═══════════════════════════════════════════════════════════"
echo "🎯 اختبار سريع للنظام المحدث"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Test config reading
source config.sh

echo "📊 الإعدادات الحالية:"
echo "───────────────────────────────────────────────────────────"
echo "  وضع البث: $STREAMING_MODE"
echo "  حجم اللوقو: $LOGO_SIZE"
echo "  اللوقو مفعّل: $LOGO_ENABLED"
echo ""

if [ "$STREAMING_MODE" = "copy" ]; then
    echo "✅ وضع Stream Copy مفعّل"
    echo "   → جودة أصلية 100%"
    echo "   → صفر استخدام CPU"
    echo "   → بدون لوقو"
elif [ "$STREAMING_MODE" = "encode" ]; then
    echo "✅ وضع Re-encode مفعّل"
    echo "   → لوقو بحجم $LOGO_SIZE"
    echo "   → تحكم كامل في الجودة"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ النظام جاهز للاستخدام!"
echo ""
echo "للتشغيل:"
echo "  ./control.sh monitor"
echo "═══════════════════════════════════════════════════════════"
