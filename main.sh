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
    
    # Try ping first
    if ping -c 1 -W 3 8.8.8.8 &> /dev/null; then
        log_success "Internet connection OK"
        return 0
    fi
    
    # If ping fails, try curl (better for Replit environment)
    if curl -s --max-time 5 --head https://www.facebook.com &> /dev/null; then
        log_success "Internet connection OK (verified via HTTP)"
        return 0
    fi
    
    log_error "No internet connection!"
    log_info "Please check your network connection"
    exit 1
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
    log_info "Source: $SOURCE"
    
    # Try to get HTTP response
    local http_code=$(curl -Is --max-time 10 "$SOURCE" 2>/dev/null | head -n 1 | grep -oP '\d{3}' | head -n 1)
    
    if [ -n "$http_code" ]; then
        if echo "$http_code" | grep -q "200\|302\|301"; then
            log_success "Source URL is accessible (HTTP $http_code)"
        else
            log_warning "Source returned HTTP $http_code"
        fi
    else
        log_warning "Could not verify source via HTTP"
    fi
    
    # Try ffprobe to check if it's a valid stream
    log_info "Testing source with FFmpeg..."
    if timeout 15 ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$SOURCE" &>/dev/null; then
        log_success "Source is a valid video stream"
    else
        log_error "Source does not appear to be a valid video stream!"
        log_warning "This may cause streaming to fail"
        echo ""
        log_info "Common issues:"
        echo "  - URL expired or invalid"
        echo "  - Source requires authentication"
        echo "  - Network/firewall blocking access"
        echo "  - Source format not supported"
        echo ""
        read -p "Do you want to continue anyway? (y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Streaming cancelled by user"
            exit 0
        fi
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

build_ffmpeg_command() {
    local input_params=""
    local output_params=""
    
    # INPUT PARAMETERS (before -i)
    # ─────────────────────────────────────────────────────────
    
    # Re-use HTTP connection for TS files
    input_params="$input_params -multiple_requests 1"
    input_params="$input_params -reconnect 1"
    input_params="$input_params -reconnect_streamed 1"
    input_params="$input_params -reconnect_at_eof 1"
    input_params="$input_params -reconnect_delay_max 10"
    
    # TS stream specific settings
    input_params="$input_params -analyzeduration 3000000"
    input_params="$input_params -probesize 3000000"
    input_params="$input_params -fflags +genpts+discardcorrupt+igndts"
    
    # Avoid stalling
    input_params="$input_params -timeout 10000000"
    input_params="$input_params -rw_timeout 10000000"
    
    # Log level
    input_params="$input_params -loglevel info"
    
    # OUTPUT PARAMETERS (after -i)
    # ─────────────────────────────────────────────────────────
    
    # Re-encode video to H.264 and audio to AAC (Facebook requirement)
    output_params="$output_params -c:v $VIDEO_ENCODER"
    output_params="$output_params -preset $PRESET -tune $TUNE"
    output_params="$output_params -b:v $BITRATE -maxrate $MAXRATE -bufsize $BUFSIZE"
    output_params="$output_params -pix_fmt $PIXEL_FORMAT"
    output_params="$output_params -g $((FPS * KEYINT))"
    output_params="$output_params -keyint_min $((FPS * KEYINT))"
    output_params="$output_params -c:a aac -b:a 128k -ar 44100 -ac 2"
    
    # Output format for RTMP/Facebook
    output_params="$output_params -f flv"
    output_params="$output_params -flvflags no_duration_filesize"
    
    # Sync and timing fixes
    output_params="$output_params -async 1"
    output_params="$output_params -vsync cfr"
    output_params="$output_params -copytb 1"
    
    # Buffer settings
    output_params="$output_params -max_muxing_queue_size 9999"
    
    # Return both parts separated by a marker
    echo "INPUT:$input_params OUTPUT:$output_params"
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
    
    log_info "Building FFmpeg command..."
    local FFMPEG_CMD=$(build_ffmpeg_command)
    
    # Split input and output parameters
    local INPUT_PARAMS="${FFMPEG_CMD#*INPUT:}"
    INPUT_PARAMS="${INPUT_PARAMS%%OUTPUT:*}"
    local OUTPUT_PARAMS="${FFMPEG_CMD#*OUTPUT:}"
    
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
echo "Starting FFmpeg..."
ffmpeg $INPUT_PARAMS -i "$SOURCE" $OUTPUT_PARAMS "$RTMP_URL" 2>&1 | tee -a "$LOG_FILE"
EOFSCRIPT
    else
        cat >> "$TEMP_SCRIPT" << EOFSCRIPT
echo "========================================"
echo "Starting FFmpeg..."
ffmpeg $INPUT_PARAMS -i "$SOURCE" $OUTPUT_PARAMS "$RTMP_URL"
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
        # Wait a bit more and check if FFmpeg is actually running
        sleep 3
        
        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
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
                echo ""
                log_info "Checking initial stream output..."
                sleep 2
                if [ -f "$LOG_FILE" ]; then
                    echo ""
                    echo -e "${CYAN}═══ Last 10 lines of log ═══${NC}"
                    tail -n 10 "$LOG_FILE"
                    echo -e "${CYAN}════════════════════════════${NC}"
                fi
            fi
            echo ""
            log_warning "Note: If stream stops suddenly, check:"
            echo -e "  - Stream key validity (FB_STREAM_KEY)"
            echo -e "  - Source URL validity"
            echo -e "  - Internet connection"
            echo -e "  - Logs: ${GREEN}./control.sh logs${NC}"
        else
            log_error "Stream session died immediately after starting!"
            echo ""
            log_info "This usually means:"
            echo -e "  ${YELLOW}1.${NC} Invalid stream key"
            echo -e "  ${YELLOW}2.${NC} Invalid source URL"
            echo -e "  ${YELLOW}3.${NC} FFmpeg encoding error"
            echo ""
            if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
                log_info "Error details from log:"
                echo ""
                tail -n 30 "$LOG_FILE"
            fi
            rm -f "$TEMP_SCRIPT"
            exit 1
        fi
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
