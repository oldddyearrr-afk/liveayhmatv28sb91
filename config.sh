#!/bin/bash

# ═══════════════════════════════════════════════════════════
# Configuration File - Facebook Live Stream
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# 1. Source and Destination Settings
# ═══════════════════════════════════════════════════════════

# Facebook Live Stream URL (DASH format)
SOURCE="http://hydratv.cc:80/live/aboud5d/57874g/415774.ts"

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
# 4. Watermark Text Settings (Scrolling Text)
# ═══════════════════════════════════════════════════════════
# NOTE: Watermark only works when STREAMING_MODE="encode"

# Enable watermark text
WATERMARK_ENABLED="true"  # true or false

# Watermark text content
WATERMARK_TEXT="Your Channel Name - Subscribe Now! 🔴 LIVE"

# Text appearance
WATERMARK_FONTSIZE="30"
WATERMARK_FONTCOLOR="white@0.85"
WATERMARK_SHADOWCOLOR="black@0.3"
WATERMARK_SHADOWX="1"
WATERMARK_SHADOWY="1"

# Position (from bottom)
WATERMARK_Y_OFFSET="40"  # pixels from bottom

# Scroll speed (pixels per second)
WATERMARK_SCROLL_SPEED="120"

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
# Function: Build Watermark Text Filter
# ═══════════════════════════════════════════════════════════

build_watermark_filter() {
    if [ "$WATERMARK_ENABLED" != "true" ]; then
        echo ""
        return
    fi
    
    # Escape single quotes in text
    local safe_text="${WATERMARK_TEXT//\'/\\\'}"
    
    # Build drawtext filter with scrolling animation
    local filter="-vf \"drawtext=text='${safe_text}'"
    filter="${filter}:fontsize=${WATERMARK_FONTSIZE}"
    filter="${filter}:fontcolor=${WATERMARK_FONTCOLOR}"
    filter="${filter}:shadowcolor=${WATERMARK_SHADOWCOLOR}"
    filter="${filter}:shadowx=${WATERMARK_SHADOWX}"
    filter="${filter}:shadowy=${WATERMARK_SHADOWY}"
    filter="${filter}:y=h-th-${WATERMARK_Y_OFFSET}"
    filter="${filter}:x=w-mod(t*${WATERMARK_SCROLL_SPEED}\,w+tw)\""
    
    echo "$filter"
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
