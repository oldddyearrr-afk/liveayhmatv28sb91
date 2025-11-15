#!/bin/bash

# ═══════════════════════════════════════════════════════════
# Configuration File - Facebook Live Stream
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# 1. Source and Destination Settings
# ═══════════════════════════════════════════════════════════

# M3U8 video source URL
SOURCE="http://g.rosexz.xyz/at/sh/805768?token=SxAKVEBaQ14XUwYBBVYCD1VdBQRSB1cABAAEUVoFBw4JC1ADBQZUAVQTHBNGEEFcBQhpWAASCFcBAABTFUQTR0NXEGpaVkNeFwUHBgxVBAxGSRRFDV1XQA8ABlQKUFcFCAdXGRFCCAAXC15EWQgfGwEdQlQWXlMOalVUElAFAxQKXBdZXx5DC1tuVFRYBV1dRl8UAEYcEAtGQRNeVxMKWhwQAFxHQAAQUBMKX0AIXxVGBllECkRAGxcLEy1oREoUVUoWUF1BCAtbEwoTQRcRFUYMRW4WVUEWR1RQCVwURAwSAkAZEV8AHGpSX19bAVBNDQpYQkYKEFMXHRMJVggPQl9APUVaVkNeW0RcXUg"

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

# Auto reconnect settings
RECONNECT_ENABLED="true"
RECONNECT_DELAY_MAX="10"
RECONNECT_ATTEMPTS="-1"  # -1 = unlimited attempts

# Encoding settings
PRESET="ultrafast"  # ultrafast, superfast, veryfast, faster, fast, medium, slow
TUNE="zerolatency"  # For live streaming
PIXEL_FORMAT="yuv420p"

# Audio Settings
AUDIO_CODEC="copy"  # copy = stream copy (faster, no re-encoding) | aac = re-encode
AUDIO_RATE="44100"  # Only used if re-encoding

# ═══════════════════════════════════════════════════════════
# 4. Logo/Watermark Settings
# ═══════════════════════════════════════════════════════════

# Enable logo overlay
LOGO_ENABLED="false"  # true or false

# Path to logo image file (PNG with transparency recommended)
LOGO_PATH="logo.png"

# Logo position: topleft, topright, bottomleft, bottomright
LOGO_POSITION="topright"

# Logo offset from edges (in pixels)
LOGO_OFFSET_X="10"
LOGO_OFFSET_Y="10"

# Logo size (leave empty for original size, or specify like "200:100" for WxH)
LOGO_SIZE=""

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
    
    echo "-i \"$LOGO_PATH\" -filter_complex \"[1:v]${size_filter}${opacity_filter}format=rgba[logo];[0:v][logo]overlay=$position_filter\""
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
