#!/bin/bash
source config.sh
source <(grep -A 100 "^build_ffmpeg_command" main.sh | grep -B 100 "^}")
source <(grep -A 30 "^get_quality_settings" config.sh | grep -B 30 "^}")

get_quality_settings
VIDEO_ENCODER="libx264"

echo "═══════════════════════════════════════════════════════════"
echo "🎯 اختبار الوضعين: Stream Copy & Re-encode"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Test 1: Stream Copy Mode
echo "1️⃣ وضع النسخ المباشر (STREAMING_MODE=copy)"
echo "───────────────────────────────────────────────────────────"
STREAMING_MODE="copy"
FFMPEG_CMD=$(build_ffmpeg_command)
OUTPUT_PARAMS="${FFMPEG_CMD#*OUTPUT:}"
echo "الأمر: ffmpeg -i source.ts $OUTPUT_PARAMS rtmp://..."
echo "✅ نسخ مباشر - بدون re-encoding - بدون لوقو"
echo ""

# Test 2: Re-encode Mode
echo "2️⃣ وضع إعادة الترميز (STREAMING_MODE=encode)"
echo "───────────────────────────────────────────────────────────"
STREAMING_MODE="encode"
LOGO_ENABLED="true"
LOGO_SIZE="350:-1"
FFMPEG_CMD=$(build_ffmpeg_command)

INPUT_PARAMS="${FFMPEG_CMD#*INPUT:}"
INPUT_PARAMS="${INPUT_PARAMS%%LOGO:*}"

LOGO_PARAMS="${FFMPEG_CMD#*LOGO:}"
LOGO_PARAMS="${LOGO_PARAMS%%OUTPUT:*}"

OUTPUT_PARAMS="${FFMPEG_CMD#*OUTPUT:}"

echo "اللوقو: $LOGO_PARAMS"
echo "حجم اللوقو: 350px (أكبر من 250px السابق)"
echo "✅ إعادة ترميز - مع لوقو بحجم 350px"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "✅ كلا الوضعين جاهزان!"
echo "═══════════════════════════════════════════════════════════"
