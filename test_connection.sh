#!/bin/bash

# Test Facebook RTMP connection
echo "🔍 اختبار الاتصال بفيسبوك..."
echo ""

# Test RTMP server
echo "1️⃣ فحص سيرفر RTMP..."
if timeout 5 bash -c "echo > /dev/tcp/live-api-s.facebook.com/443" 2>/dev/null; then
    echo "✅ الاتصال بسيرفر فيسبوك يعمل"
else
    echo "❌ لا يمكن الوصول لسيرفر فيسبوك"
fi
echo ""

# Test with different RTMP URLs
echo "2️⃣ اختبار روابط RTMP مختلفة..."
echo "   - rtmps://live-api-s.facebook.com:443/rtmp/"
echo "   - rtmp://live-api-s.facebook.com:80/rtmp/"
echo ""

# Check if FB_STREAM_KEY exists
echo "3️⃣ فحص مفتاح البث..."
if [ -n "$FB_STREAM_KEY" ]; then
    echo "✅ مفتاح البث موجود (طوله: ${#FB_STREAM_KEY} حرف)"
    echo "   أول 10 أحرف: ${FB_STREAM_KEY:0:10}..."
else
    echo "❌ مفتاح البث غير موجود!"
    echo "   أضفه في Replit Secrets"
fi
echo ""

# Test FFmpeg RTMP support
echo "4️⃣ فحص دعم FFmpeg لـ RTMP..."
if ffmpeg -protocols 2>/dev/null | grep -q rtmp; then
    echo "✅ FFmpeg يدعم RTMP"
else
    echo "❌ FFmpeg لا يدعم RTMP"
fi
echo ""

echo "═══════════════════════════════════════"
echo "انتهى الاختبار"
