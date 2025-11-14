#!/bin/bash

# ═══════════════════════════════════════════════════════════
# Facebook Live Stream - Enhanced Version
# ═══════════════════════════════════════════════════════════

set -e

# Load configuration file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

# ═══════════════════════════════════════════════════════════
# Colors for console output
# ═══════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════
# Colored logging functions
# ═══════════════════════════════════════════════════════════

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ═══════════════════════════════════════════════════════════
# 1. Check system requirements
# ═══════════════════════════════════════════════════════════

check_requirements() {
    log_info "Checking system requirements..."
    
    local missing_deps=()
    
    if ! command -v ffmpeg &> /dev/null; then
        missing_deps+=("ffmpeg")
    fi
    
    if ! command -v tmux &> /dev/null; then
        missing_deps+=("tmux")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install them first"
        exit 1
    fi
    
    log_success "All requirements met"
}

# ═══════════════════════════════════════════════════════════
# 2. Check internet connection
# ═══════════════════════════════════════════════════════════

check_internet() {
    log_info "Checking internet connection..."
    
    if ! ping -c 1 -W 3 8.8.8.8 &> /dev/null; then
        log_error "No internet connection!"
        log_info "Please check your network connection"
        exit 1
    fi
    
    log_success "Internet connection OK"
}

# ═══════════════════════════════════════════════════════════
# 3. Check stream key
# ═══════════════════════════════════════════════════════════

check_stream_key() {
    log_info "Checking stream key..."
    
    if [ -z "$FB_STREAM_KEY" ]; then
        log_error "Stream key not found!"
        log_warning "Please set environment variable: FB_STREAM_KEY"
        log_info "Example: export FB_STREAM_KEY='your-stream-key-here'"
        exit 1
    fi
    
    if [ "$FB_STREAM_KEY" = "YOUR_STREAM_KEY_HERE" ]; then
        log_error "Please change stream key from default value"
        exit 1
    fi
    
    log_success "Stream key found"
}

# ═══════════════════════════════════════════════════════════
# 4. Check source URL validity
# ═══════════════════════════════════════════════════════════

check_source() {
    log_info "Checking source URL..."
    
    if ! curl -Is --max-time 10 "$SOURCE" | head -n 1 | grep -q "200\|302\|301"; then
        log_warning "Source URL may not be valid"
        log_info "Will attempt to stream anyway..."
    else
        log_success "Source URL is valid"
    fi
}

# ═══════════════════════════════════════════════════════════
# 5. Setup logging directory
# ═══════════════════════════════════════════════════════════

setup_logs() {
    if [ "$LOG_ENABLED" = "true" ]; then
        mkdir -p "$LOG_DIR"
        log_success "Logging directory ready: $LOG_DIR"
    fi
}

# ═══════════════════════════════════════════════════════════
# 6. Get quality settings
# ═══════════════════════════════════════════════════════════

get_quality_settings

# ═══════════════════════════════════════════════════════════
# 7. Detect GPU encoder
# ═══════════════════════════════════════════════════════════

VIDEO_ENCODER=$(detect_gpu_encoder)

if [ "$VIDEO_ENCODER" != "libx264" ]; then
    log_success "GPU encoder detected: $VIDEO_ENCODER"
else
    log_info "Using CPU encoder: libx264"
fi

# ═══════════════════════════════════════════════════════════
# 8. Build FFmpeg parameters
# ═══════════════════════════════════════════════════════════

build_ffmpeg_params() {
    local params=""
    
    # Reconnection parameters
    if [ "$RECONNECT_ENABLED" = "true" ]; then
        params="$params -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max $RECONNECT_DELAY_MAX"
    fi
    
    # Logo overlay
    local logo_filter=$(build_logo_filter)
    if [ -n "$logo_filter" ]; then
        params="$params $logo_filter"
        log_info "Logo overlay enabled"
    fi
    
    # Video encoding parameters
    params="$params -c:v $VIDEO_ENCODER"
    
    # libx264 specific settings
    if [ "$VIDEO_ENCODER" = "libx264" ]; then
        params="$params -preset $PRESET -tune $TUNE"
    fi
    
    # Resolution and FPS
    if [ -z "$logo_filter" ]; then
        params="$params -s $RESOLUTION -r $FPS"
    else
        params="$params -r $FPS"
    fi
    
    # Bitrate and buffer
    params="$params -b:v $BITRATE -maxrate $MAXRATE -bufsize $BUFSIZE"
    
    # Key interval (2 seconds)
    local keyint_frames=$((FPS * KEYINT))
    params="$params -g $keyint_frames -keyint_min $keyint_frames"
    
    # Pixel format
    params="$params -pix_fmt $PIXEL_FORMAT"
    
    # Audio parameters
    if [ "$AUDIO_CODEC" = "copy" ]; then
        params="$params -c:a copy"
        log_info "Audio: stream copy (no re-encoding)"
    else
        params="$params -c:a $AUDIO_CODEC -b:a $AUDIO_BITRATE -ar $AUDIO_RATE"
        log_info "Audio: re-encoding with $AUDIO_CODEC"
    fi
    
    # Threads
    if [ "$THREADS" != "0" ]; then
        params="$params -threads $THREADS"
    fi
    
    # Log level
    if [ "$LOG_ENABLED" = "true" ]; then
        params="$params -loglevel $LOG_LEVEL"
    else
        params="$params -loglevel error"
    fi
    
    echo "$params"
}

# ═══════════════════════════════════════════════════════════
# 9. Display stream information
# ═══════════════════════════════════════════════════════════

display_stream_info() {
    echo ""
    log_info "========================================"
    log_info "Stream Configuration"
    log_info "========================================"
    echo -e "${BLUE}Quality:${NC} $QUALITY_MODE"
    echo -e "${BLUE}Resolution:${NC} $RESOLUTION"
    echo -e "${BLUE}FPS:${NC} $FPS"
    echo -e "${BLUE}Bitrate:${NC} $BITRATE (max: $MAXRATE)"
    echo -e "${BLUE}Key Interval:${NC} ${KEYINT}s (every $((FPS * KEYINT)) frames)"
    
    if [ "$AUDIO_CODEC" = "copy" ]; then
        echo -e "${BLUE}Audio:${NC} Stream copy (no re-encoding)"
    else
        echo -e "${BLUE}Audio:${NC} $AUDIO_BITRATE @ ${AUDIO_RATE}Hz"
    fi
    
    echo -e "${BLUE}Encoder:${NC} $VIDEO_ENCODER"
    
    if [ "$LOGO_ENABLED" = "true" ] && [ -f "$LOGO_PATH" ]; then
        echo -e "${BLUE}Logo:${NC} Enabled ($LOGO_POSITION)"
    fi
    
    echo -e "${BLUE}Source:${NC} $SOURCE"
    log_info "========================================"
    echo ""
}

# ═══════════════════════════════════════════════════════════
# 10. Start streaming
# ═══════════════════════════════════════════════════════════

start_stream() {
    log_info "Stopping any previous session..."
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
    
    log_info "Building FFmpeg parameters..."
    FFMPEG_PARAMS=$(build_ffmpeg_params)
    
    display_stream_info
    
    # Build complete command
    RTMP_URL="${RTMP_SERVER}${FB_STREAM_KEY}"
    
    local LOG_FILE=""
    if [ "$LOG_ENABLED" = "true" ]; then
        LOG_FILE="$LOG_DIR/stream_$(date +%Y%m%d_%H%M%S).log"
        touch "$LOG_FILE"
    fi
    
    log_info "Starting stream..."
    
    # Create temporary script to run inside tmux
    local TEMP_SCRIPT="/tmp/fbstream_$$.sh"
    cat > "$TEMP_SCRIPT" << EOFSCRIPT
#!/bin/bash
echo "========================================"
echo "Stream started at: \$(date)"
echo "========================================"
EOFSCRIPT

    if [ -n "$LOG_FILE" ]; then
        cat >> "$TEMP_SCRIPT" << EOFSCRIPT
echo "Log file: $LOG_FILE"
echo "========================================"
ffmpeg -i "$SOURCE" $FFMPEG_PARAMS -f flv "$RTMP_URL" 2>&1 | tee -a "$LOG_FILE"
EOFSCRIPT
    else
        cat >> "$TEMP_SCRIPT" << EOFSCRIPT
echo "========================================"
ffmpeg -i "$SOURCE" $FFMPEG_PARAMS -f flv "$RTMP_URL"
EOFSCRIPT
    fi
    
    chmod +x "$TEMP_SCRIPT"
    
    # Create tmux session and run script
    tmux new-session -d -s "$SESSION_NAME" "$TEMP_SCRIPT"
    
    # Wait and verify session started
    sleep 1
    
    local attempt=0
    local max_attempts=5
    local session_started=false
    
    while [ $attempt -lt $max_attempts ]; do
        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            session_started=true
            break
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    if [ "$session_started" = true ]; then
        log_success "Stream started successfully!"
        echo ""
        log_info "To view stream status:"
        echo -e "  ${GREEN}tmux attach -t $SESSION_NAME${NC}"
        echo ""
        log_info "Or use:"
        echo -e "  ${GREEN}./control.sh status${NC}"
        echo ""
        if [ -n "$LOG_FILE" ]; then
            log_info "Log file: $LOG_FILE"
        fi
        echo ""
        log_warning "Note: If stream stops suddenly, check:"
        echo -e "  - Stream key validity (FB_STREAM_KEY)"
        echo -e "  - Source URL validity"
        echo -e "  - Internet connection"
        echo -e "  - Logs: ${GREEN}./control.sh logs${NC}"
    else
        log_error "Failed to start stream!"
        echo ""
        if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
            log_info "Last log entries:"
            tail -n 20 "$LOG_FILE"
        fi
        rm -f "$TEMP_SCRIPT"
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════
# Main program
# ═══════════════════════════════════════════════════════════

main() {
    echo ""
    log_info "========================================"
    log_info "Facebook Live Stream"
    log_info "========================================"
    echo ""
    
    check_requirements
    check_internet
    check_stream_key
    check_source
    setup_logs
    start_stream
    
    echo ""
    log_success "Done!"
    echo ""
}

main "$@"
