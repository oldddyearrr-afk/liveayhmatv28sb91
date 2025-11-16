#!/bin/bash
source config.sh
source <(grep -A 100 "^build_ffmpeg_command" main.sh | grep -B 100 "^}")

# Get quality settings
get_quality_settings

# Detect encoder
VIDEO_ENCODER=$(detect_gpu_encoder)

# Build command
FFMPEG_CMD=$(build_ffmpeg_command)

# Split parameters
INPUT_PARAMS="${FFMPEG_CMD#*INPUT:}"
INPUT_PARAMS="${INPUT_PARAMS%%LOGO:*}"

LOGO_PARAMS="${FFMPEG_CMD#*LOGO:}"
LOGO_PARAMS="${LOGO_PARAMS%%OUTPUT:*}"

OUTPUT_PARAMS="${FFMPEG_CMD#*OUTPUT:}"

# Test URL
TEST_RTMP="rtmps://live-api-s.facebook.com:443/rtmp/TEST_KEY"

echo "═══════════════════════════════════════"
echo "🔍 معاينة أمر FFmpeg"
echo "═══════════════════════════════════════"
echo ""
echo "INPUT_PARAMS:"
echo "$INPUT_PARAMS"
echo ""
echo "LOGO_PARAMS:"
echo "$LOGO_PARAMS"
echo ""
echo "OUTPUT_PARAMS:"
echo "$OUTPUT_PARAMS"
echo ""
echo "═══════════════════════════════════════"
echo "الأمر الكامل:"
echo "ffmpeg $INPUT_PARAMS -i \"$SOURCE\" $LOGO_PARAMS $OUTPUT_PARAMS \"$TEST_RTMP\""
echo "═══════════════════════════════════════"
