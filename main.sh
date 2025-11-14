#!/bin/bash

# رابط m3u8 — غيّره إذا تريد
SOURCE="https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"

# رابط RTMP + Stream Key — ضع رابط فيسبوك هنا ↓↓↓↓↓
RTMP="rtmp://rtmp-api.facebook.com:80/rtmp/YOUR_STREAM_KEY_HERE"

# إعادة الاتصال تلقائياً إذا انقطع
RECONNECT="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10"

# جودة البث مناسبة لفيسبوك
VIDEO="-c:v libx264 -preset veryfast -b:v 2500k -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p"
AUDIO="-c:a aac -b:a 128k -ar 44100"

# التشغيل داخل tmux حتى يبقى البث شغال حتى لو سكّرت الشاشة
SESSION="fbstream"

tmux kill-session -t $SESSION 2>/dev/null
tmux new-session -d -s $SESSION "

ffmpeg -i \"$SOURCE\" $RECONNECT -tune zerolatency $VIDEO $AUDIO -f flv \"$RTMP\"
"

echo "🚀 البث بدأ — لفتح الجلسة:"
echo "tmux attach -t fbstream"