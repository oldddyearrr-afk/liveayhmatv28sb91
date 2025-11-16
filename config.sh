#!/bin/bash

# ═══════════════════════════════════════════════════════════
# Configuration File - Facebook Live Stream
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# 1. Source and Destination Settings
# ═══════════════════════════════════════════════════════════

# Facebook Live Stream URL (DASH format)
SOURCE="https://prod-fastly-eu-central-1.video.pscp.tv:443/Transcoding/v1/hls/46nxSDfa09rMtUJJ6VazshhCx_5sR7TrQpzts5pQUjzlyQeTJTkEUdOnTbKebirVBwzBUu39k5AuEKp2cAVWSQ/transcode/eu-central-1/periscope-replay-direct-prod-eu-central-1-public/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInZlcnNpb24iOiIyIn0.eyJFbmNvZGVyU2V0dGluZyI6ImVuY29kZXJfc2V0dGluZ18xMDgwcDMwXzEwIiwiSGVpZ2h0IjoxMDgwLCJLYnBzIjo1NTAwLCJXaWR0aCI6MTkyMH0.OImMZabKYJ0cs9CnIapU-4aBk6KNBiJxi1hh-6l4BZ4/dynamic_highlatency.m3u8?type=live"

# RTMP server for Facebook (Stream Key is fetched from environment variables for security)
RTMP_SERVER="rtmps://live-api-s.facebook.com:443/rtmp/"

# ═══════════════════════════════════════════════════════════
# 2. Quality Presets
# ═══════════════════════════════════════════════════════════

# Choose one: low, medium, high, ultra, custom
QUALITY_MODE="ultra"

# ─────────────────────────────────────────────────────────
# LOW Mode - 720p @ 30fps (for weak internet)
# ─────────────────────────────────────────────────────────
LOW_RESOLUTION="1280x720"
LOW_FPS="30"
LOW_BITRATE="2000k"
LOW_MAXRATE="2500k"
LOW_BUFSIZE="4000k"
LOW_AUDIO_BITRATE="96k"

# ─────────────────────────────────────────────────────────
# MEDIUM Mode - 720p @ 30fps (medium quality)
# ─────────────────────────────────────────────────────────
MEDIUM_RESOLUTION="1280x720"
MEDIUM_FPS="30"
MEDIUM_BITRATE="3000k"
MEDIUM_MAXRATE="3500k"
MEDIUM_BUFSIZE="6000k"
MEDIUM_AUDIO_BITRATE="128k"

# ─────────────────────────────────────────────────────────
# HIGH Mode - 1080p @ 30fps (high quality)
# ─────────────────────────────────────────────────────────
HIGH_RESOLUTION="1920x1080"
HIGH_FPS="30"
HIGH_BITRATE="4500k"
HIGH_MAXRATE="5000k"
HIGH_BUFSIZE="9000k"
HIGH_AUDIO_BITRATE="160k"

# ─────────────────────────────────────────────────────────
# ULTRA Mode - 1080p @ 30fps (best quality) ⭐ New Settings
# ─────────────────────────────────────────────────────────
ULTRA_RESOLUTION="1920x1080"
ULTRA_FPS="30"
ULTRA_BITRATE="5000k"
ULTRA_MAXRATE="6000k"
ULTRA_BUFSIZE="10000k"
ULTRA_AUDIO_BITRATE="192k"
ULTRA_KEYINT="2"  # Key interval 2 seconds

# ─────────────────────────────────────────────────────────
# CUSTOM Mode - Custom settings
# ─────────────────────────────────────────────────────────
CUSTOM_RESOLUTION="1920x1080"
CUSTOM_FPS="30"
CUSTOM_BITRATE="5000k"
CUSTOM_MAXRATE="6000k"
CUSTOM_BUFSIZE="10000k"
CUSTOM_AUDIO_BITRATE="192k"
CUSTOM_KEYINT="2"

# ═══════════════════════════════════════════════════════════
# 3. Advanced Settings
# ═══════════════════════════════════════════════════════════

# Auto reconnect settings (optimized for fast connection)
RECONNECT_ENABLED="true"
RECONNECT_DELAY_MAX="2"  # Fast reconnect delay
RECONNECT_ATTEMPTS="-1"  # Unlimited attempts for reliability

# Auto restart on failure
AUTO_RESTART="true"
RESTART_DELAY="3"  # Reduced from 5 to 3 seconds

# Encoding settings
PRESET="ultrafast"  # ultrafast, superfast, veryfast, faster, fast, medium, slow
TUNE="zerolatency"  # For live streaming
PIXEL_FORMAT="yuv420p"

# Audio Settings
AUDIO_CODEC="copy"  # copy = stream copy (faster, no re-encoding) | aac = re-encode
AUDIO_RATE="44100"  # Only used if re-encoding

# ═══════════════════════════════════════════════════════════
# Streaming Mode (NEW!) ⭐
# ═══════════════════════════════════════════════════════════

# STREAMING_MODE: "copy" or "encode"
# - "copy": Stream copy (fast, no CPU, original quality, NO LOGO) ⚡
# - "encode": Re-encode with logo overlay (uses CPU, allows logo) 🎨
STREAMING_MODE="encode"

# ═══════════════════════════════════════════════════════════
# 4. Logo/Watermark Settings
# ═══════════════════════════════════════════════════════════
# NOTE: Logo only works when STREAMING_MODE="encode"

# Enable logo overlay
LOGO_ENABLED="true"  # true or false

# Path to logo image file (PNG with transparency recommended)
LOGO_PATH="channel_logo.png"

# Logo position: topleft, topright, bottomleft, bottomright
LOGO_POSITION="topright"

# ════════════════════════════════════════════════════════════
# موضع اللوجو من حافة الشاشة (بالبكسل)
# ════════════════════════════════════════════════════════════
# 
# LOGO_OFFSET_X = المسافة من الحافة اليمنى أو اليسرى
# LOGO_OFFSET_Y = المسافة من الحافة العلوية أو السفلية
#
# 📐 أمثلة توضيحية:
#
# ┌─────────────────────────────────────┐
# │  LOGO_OFFSET_X="20"                 │  لوجو بعيد عن الحافة (مسافة كبيرة)
# │  LOGO_OFFSET_Y="20"                 │
# └─────────────────────────────────────┘
#
# ┌─────────────────────────────────────┐
# │  LOGO_OFFSET_X="5"                  │  لوجو قريب من الحافة (مسافة صغيرة)
# │  LOGO_OFFSET_Y="5"                  │
# └─────────────────────────────────────┘
#
# ┌─────────────────────────────────────┐
# │  LOGO_OFFSET_X="0"                  │  لوجو ملاصق للحافة تماماً
# │  LOGO_OFFSET_Y="0"                  │
# └─────────────────────────────────────┘
#
# 💡 نصيحة: استخدم أرقام صغيرة للالتصاق بالحافة (0-10)
#           أو أرقام كبيرة للابتعاد عن الحافة (20-50)
#
LOGO_OFFSET_X="10"    # المسافة الأفقية من حافة الشاشة
LOGO_OFFSET_Y="50"    # المسافة العمودية من حافة الشاشة

# Logo size (leave empty for original size, or specify like "200:100" for WxH)
# Example: "350:-1" = 350px width, maintain aspect ratio
LOGO_SIZE="450:-1"

# Logo opacity (0.0 to 1.0, where 1.0 is fully opaque)
LOGO_OPACITY="1.0"

# ═══════════════════════════════════════════════════════════
# 5. Performance Settings
# ═══════════════════════════════════════════════════════════

# Use GPU for encoding (if available)
USE_GPU="off"  # auto, nvidia, intel, amd, off

# Number of threads for CPU encoding
THREADS="0"  # 0 = automatic

# ═══════════════════════════════════════════════════════════
# 6. tmux Settings
# ═══════════════════════════════════════════════════════════

SESSION_NAME="fbstream"

# ═══════════════════════════════════════════════════════════
# 7. Logging Settings
# ═══════════════════════════════════════════════════════════

LOG_DIR="logs"
LOG_ENABLED="true"
LOG_LEVEL="info"  # quiet, panic, fatal, error, warning, info, verbose, debug

# ═══════════════════════════════════════════════════════════
# 8. Status File for API Integration
# ═══════════════════════════════════════════════════════════

STATUS_FILE="/tmp/fbstream_status.txt"

# ═══════════════════════════════════════════════════════════
# Function: Get Quality Settings
# ═══════════════════════════════════════════════════════════

get_quality_settings() {
    case $QUALITY_MODE in
        low)
            RESOLUTION=$LOW_RESOLUTION
            FPS=$LOW_FPS
            BITRATE=$LOW_BITRATE
            MAXRATE=$LOW_MAXRATE
            BUFSIZE=$LOW_BUFSIZE
            AUDIO_BITRATE=$LOW_AUDIO_BITRATE
            KEYINT="2"
            ;;
        medium)
            RESOLUTION=$MEDIUM_RESOLUTION
            FPS=$MEDIUM_FPS
            BITRATE=$MEDIUM_BITRATE
            MAXRATE=$MEDIUM_MAXRATE
            BUFSIZE=$MEDIUM_BUFSIZE
            AUDIO_BITRATE=$MEDIUM_AUDIO_BITRATE
            KEYINT="2"
            ;;
        high)
            RESOLUTION=$HIGH_RESOLUTION
            FPS=$HIGH_FPS
            BITRATE=$HIGH_BITRATE
            MAXRATE=$HIGH_MAXRATE
            BUFSIZE=$HIGH_BUFSIZE
            AUDIO_BITRATE=$HIGH_AUDIO_BITRATE
            KEYINT="2"
            ;;
        ultra)
            RESOLUTION=$ULTRA_RESOLUTION
            FPS=$ULTRA_FPS
            BITRATE=$ULTRA_BITRATE
            MAXRATE=$ULTRA_MAXRATE
            BUFSIZE=$ULTRA_BUFSIZE
            AUDIO_BITRATE=$ULTRA_AUDIO_BITRATE
            KEYINT=$ULTRA_KEYINT
            ;;
        custom)
            RESOLUTION=$CUSTOM_RESOLUTION
            FPS=$CUSTOM_FPS
            BITRATE=$CUSTOM_BITRATE
            MAXRATE=$CUSTOM_MAXRATE
            BUFSIZE=$CUSTOM_BUFSIZE
            AUDIO_BITRATE=$CUSTOM_AUDIO_BITRATE
            KEYINT=$CUSTOM_KEYINT
            ;;
        *)
            echo "Warning: Unknown quality mode: $QUALITY_MODE - Using ULTRA as default"
            QUALITY_MODE="ultra"
            get_quality_settings
            ;;
    esac
}

# ═══════════════════════════════════════════════════════════
# Function: Build Logo Filter
# ═══════════════════════════════════════════════════════════

build_logo_filter() {
    if [ "$LOGO_ENABLED" != "true" ]; then
        echo ""
        return
    fi
    
    if [ ! -f "$LOGO_PATH" ]; then
        echo ""
        return
    fi
    
    local position_filter=""
    case $LOGO_POSITION in
        topleft)
            position_filter="x=$LOGO_OFFSET_X:y=$LOGO_OFFSET_Y"
            ;;
        topright)
            position_filter="x=W-w-$LOGO_OFFSET_X:y=$LOGO_OFFSET_Y"
            ;;
        bottomleft)
            position_filter="x=$LOGO_OFFSET_X:y=H-h-$LOGO_OFFSET_Y"
            ;;
        bottomright)
            position_filter="x=W-w-$LOGO_OFFSET_X:y=H-h-$LOGO_OFFSET_Y"
            ;;
        *)
            position_filter="x=W-w-$LOGO_OFFSET_X:y=$LOGO_OFFSET_Y"
            ;;
    esac
    
    local size_filter=""
    if [ -n "$LOGO_SIZE" ]; then
        size_filter="scale=$LOGO_SIZE,"
    fi
    
    local opacity_filter=""
    if [ "$LOGO_OPACITY" != "1.0" ]; then
        opacity_filter="format=rgba,colorchannelmixer=aa=$LOGO_OPACITY,"
    fi
    
    # Return only the filter, not the -i flag
    echo "-filter_complex \"[1:v]${size_filter}${opacity_filter}format=rgba[logo];[0:v][logo]overlay=$position_filter\""
}

# ═══════════════════════════════════════════════════════════
# Function: Detect and Enable GPU Encoding
# ═══════════════════════════════════════════════════════════

detect_gpu_encoder() {
    if [ "$USE_GPU" = "off" ]; then
        echo "libx264"
        return
    fi
    
    if [ "$USE_GPU" = "nvidia" ] || { [ "$USE_GPU" = "auto" ] && command -v nvidia-smi &> /dev/null; }; then
        if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_nvenc"; then
            echo "h264_nvenc"
            return
        fi
    fi
    
    if [ "$USE_GPU" = "intel" ] || [ "$USE_GPU" = "auto" ]; then
        if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_vaapi"; then
            echo "h264_vaapi"
            return
        fi
        if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_qsv"; then
            echo "h264_qsv"
            return
        fi
    fi
    
    if [ "$USE_GPU" = "amd" ] || [ "$USE_GPU" = "auto" ]; then
        if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q "h264_amf"; then
            echo "h264_amf"
            return
        fi
    fi
    
    echo "libx264"
}
