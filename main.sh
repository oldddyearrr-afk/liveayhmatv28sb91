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
# Status File Management
# ═══════════════════════════════════════════════════════════

set_status() {
    local status="$1"
    local message="${2:-}"
    echo "$status|$message|$(date +%s)" > "$STATUS_FILE"
}

cleanup_on_exit() {
    # Only set STOPPED if we were STREAMING (don't overwrite FAILED)
    if [ -f "$STATUS_FILE" ]; then
        local current_status=$(cat "$STATUS_FILE" 2>/dev/null | cut -d'|' -f1)
        if [ "$current_status" = "STREAMING" ]; then
            set_status "STOPPED" "Stream session ended"
        fi
    fi
}

trap cleanup_on_exit EXIT

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
# 2. Check internet connection and Facebook RTMP
# ═══════════════════════════════════════════════════════════

check_internet() {
    log_info "Checking internet connection..."

    # Try ping first
    if ping -c 1 -W 3 8.8.8.8 &> /dev/null; then
        log_success "Internet connection OK"
    elif curl -s --max-time 5 --head https://www.facebook.com &> /dev/null; then
        log_success "Internet connection OK (verified via HTTP)"
    else
        log_error "No internet connection!"
        log_info "Please check your network connection"
        exit 1
    fi

    # Test Facebook RTMP connection
    log_info "Testing Facebook RTMP server..."
    if timeout 5 bash -c "echo > /dev/tcp/live-api-s.facebook.com/443" 2>/dev/null; then
        log_success "Facebook RTMP server reachable"
    else
        log_warning "Cannot reach Facebook RTMP server (may still work)"
    fi
}

# ═══════════════════════════════════════════════════════════
# 3. Check stream key
# ═══════════════════════════════════════════════════════════

check_stream_key() {
    # Stream key is now passed via environment from web UI
    if [ -z "$FB_STREAM_KEY" ]; then
        log_error "Stream key not provided!"
        exit 1
    fi
    
    log_success "Stream key received"
}

# ═══════════════════════════════════════════════════════════
# 4. Check source URL validity
# ═══════════════════════════════════════════════════════════

check_source() {
    log_info "Checking source URL..."
    log_info "Source: $SOURCE"

    # Quick HTTP check
    local http_code=$(timeout 3 curl -Is --max-time 2 "$SOURCE" 2>/dev/null | head -n 1 | grep -oP '\d{3}' | head -n 1)

    if [ -n "$http_code" ]; then
        if echo "$http_code" | grep -q "200\|302\|301"; then
            log_success "Source URL is accessible (HTTP $http_code)"
        else
            log_warning "Source returned HTTP $http_code - will try anyway"
        fi
    else
        log_warning "Could not verify source via HTTP - continuing"
    fi

    # Quick ffprobe validation (both interactive and non-interactive)
    log_info "Quick source validation..."
    if timeout 8 ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "$SOURCE" &>/dev/null; then
        log_success "Source is a valid video stream"
    else
        log_warning "Source validation failed - FFmpeg will retry during streaming"
        log_info "Common causes: URL expired, network issue, or invalid format"
    fi
}

# ═══════════════════════════════════════════════════════════
# 5. Setup logging directory
# ═══════════════════════════════════════════════════════════

setup_logs() {
    if [ "$LOG_ENABLED" = "true" ]; then
        mkdir -p "$LOG_DIR"
        log_success "Logging directory ready: $LOG_DIR"
        
        if [ -f "$SCRIPT_DIR/cleanup_logs.sh" ]; then
            log_info "Cleaning up old log files..."
            bash "$SCRIPT_DIR/cleanup_logs.sh" 2>/dev/null || true
        fi
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
    local logo_params=""

    # INPUT PARAMETERS (before -i)
    # ─────────────────────────────────────────────────────────

    # Fast reconnection settings (optimized)
    input_params="$input_params -multiple_requests 1"
    input_params="$input_params -reconnect 1"
    input_params="$input_params -reconnect_streamed 1"
    input_params="$input_params -reconnect_at_eof 1"
    input_params="$input_params -reconnect_on_network_error 1"
    input_params="$input_params -reconnect_on_http_error 4xx,5xx"
    input_params="$input_params -reconnect_delay_max $RECONNECT_DELAY_MAX"

    # Fast analysis (reduced times for quicker start)
    input_params="$input_params -analyzeduration 2000000"
    input_params="$input_params -probesize 2000000"
    input_params="$input_params -fflags +genpts+discardcorrupt+nobuffer+flush_packets"

    # Shorter timeouts for faster failure detection
    input_params="$input_params -timeout 5000000"
    input_params="$input_params -rw_timeout 5000000"

    # Log level
    input_params="$input_params -loglevel warning"

    # OUTPUT PARAMETERS (after -i)
    # ─────────────────────────────────────────────────────────

    # Check streaming mode: copy or encode
    if [ "$STREAMING_MODE" = "copy" ]; then
        # ═══════════════════════════════════════════════════════
        # STREAM COPY MODE - Direct copy, no re-encoding
        # ═══════════════════════════════════════════════════════
        output_params="$output_params -c copy"
        
        # Fast output format for RTMP/Facebook
        output_params="$output_params -f flv"
        output_params="$output_params -flvflags no_duration_filesize+no_metadata"
        
        # Fast flush for immediate streaming
        output_params="$output_params -flush_packets 1"
        
    else
        # ═══════════════════════════════════════════════════════
        # ENCODE MODE - Re-encode with logo overlay
        # ═══════════════════════════════════════════════════════
        
        # Add logo input if enabled
        if [ "$LOGO_ENABLED" = "true" ] && [ -f "$LOGO_PATH" ]; then
            logo_params="-i \"$LOGO_PATH\""
        fi

        # Fast video encoding for H.264
        output_params="$output_params -c:v $VIDEO_ENCODER"
        output_params="$output_params -preset $PRESET -tune $TUNE"
        output_params="$output_params -b:v $BITRATE -maxrate $MAXRATE -bufsize $BUFSIZE"
        output_params="$output_params -pix_fmt $PIXEL_FORMAT"
        output_params="$output_params -g $((FPS * KEYINT))"
        output_params="$output_params -keyint_min $((FPS * KEYINT))"
        
        # Fast encoding options
        output_params="$output_params -sc_threshold 0"
        
        # Add logo filter if enabled
        if [ "$LOGO_ENABLED" = "true" ] && [ -f "$LOGO_PATH" ]; then
            local logo_filter=$(build_logo_filter)
            if [ -n "$logo_filter" ]; then
                output_params="$output_params $logo_filter"
            fi
        fi
        
        # Fast audio encoding
        output_params="$output_params -c:a aac -b:a 128k -ar 44100 -ac 2"

        # Optimized output format for RTMP/Facebook
        output_params="$output_params -f flv"
        output_params="$output_params -flvflags no_duration_filesize+no_metadata"

        # Fast sync and timing (async removed for modern FFmpeg compatibility)
        output_params="$output_params -vsync passthrough"
        output_params="$output_params -copytb 1"

        # Optimized buffer settings
        output_params="$output_params -max_muxing_queue_size 1024"
        output_params="$output_params -flush_packets 1"
    fi
    
    # Common RTMP optimization for both modes
    output_params="$output_params -rtmp_buffer 1000"
    output_params="$output_params -rtmp_live live"

    # Return both parts separated by a marker
    echo "INPUT:$input_params LOGO:$logo_params OUTPUT:$output_params"
}

# ═══════════════════════════════════════════════════════════
# 9. Display stream information
# ═══════════════════════════════════════════════════════════

display_stream_info() {
    echo ""
    log_info "========================================"
    log_info "Stream Configuration"
    log_info "========================================"
    
    # Display streaming mode
    if [ "$STREAMING_MODE" = "copy" ]; then
        echo -e "${GREEN}Mode:${NC} Stream Copy ⚡ (Direct, No Re-encoding)"
        echo -e "${BLUE}Video:${NC} Copy from source"
        echo -e "${BLUE}Audio:${NC} Copy from source"
        echo -e "${YELLOW}Logo:${NC} Disabled (not available in copy mode)"
    else
        echo -e "${GREEN}Mode:${NC} Re-encode 🎨 (With Logo Support)"
        echo -e "${BLUE}Quality:${NC} $QUALITY_MODE"
        echo -e "${BLUE}Resolution:${NC} $RESOLUTION"
        echo -e "${BLUE}FPS:${NC} $FPS"
        echo -e "${BLUE}Bitrate:${NC} $BITRATE (max: $MAXRATE)"
        echo -e "${BLUE}Key Interval:${NC} ${KEYINT}s (every $((FPS * KEYINT)) frames)"
        echo -e "${BLUE}Encoder:${NC} $VIDEO_ENCODER"
        
        if [ "$LOGO_ENABLED" = "true" ] && [ -f "$LOGO_PATH" ]; then
            echo -e "${BLUE}Logo:${NC} Enabled ($LOGO_POSITION, size: $LOGO_SIZE)"
        fi
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

    # Split input, logo and output parameters
    local INPUT_PARAMS="${FFMPEG_CMD#*INPUT:}"
    INPUT_PARAMS="${INPUT_PARAMS%%LOGO:*}"
    
    local LOGO_PARAMS="${FFMPEG_CMD#*LOGO:}"
    LOGO_PARAMS="${LOGO_PARAMS%%OUTPUT:*}"
    
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

    # Build complete FFmpeg command
    local FFMPEG_FULL_CMD="ffmpeg $INPUT_PARAMS -i \"$SOURCE\" $LOGO_PARAMS $OUTPUT_PARAMS \"$RTMP_URL\""
    
    log_info "FFmpeg command ready"
    
    # Create temporary script to run inside tmux
    local TEMP_SCRIPT="/tmp/fbstream_$$.sh"
    cat > "$TEMP_SCRIPT" << 'EOFSCRIPT'
#!/bin/bash
echo "========================================"
echo "Stream started at: $(date)"
echo "========================================"
EOFSCRIPT

    if [ -n "$LOG_FILE" ]; then
        cat >> "$TEMP_SCRIPT" << EOFSCRIPT
echo "Log file: $LOG_FILE"
echo "========================================"
echo "Starting FFmpeg..."
$FFMPEG_FULL_CMD 2>&1 | tee -a "$LOG_FILE"
EOFSCRIPT
    else
        cat >> "$TEMP_SCRIPT" << EOFSCRIPT
echo "========================================"
echo "Starting FFmpeg..."
$FFMPEG_FULL_CMD
EOFSCRIPT
    fi

    chmod +x "$TEMP_SCRIPT"

    # Create tmux session and run script
    tmux new-session -d -s "$SESSION_NAME" "$TEMP_SCRIPT"

    # Quick verification with shorter intervals
    local attempt=0
    local max_attempts=6
    local session_started=false

    while [ $attempt -lt $max_attempts ]; do
        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            session_started=true
            break
        fi
        sleep 0.3
        attempt=$((attempt + 1))
    done

    if [ "$session_started" = true ]; then
        # Wait and verify FFmpeg actually connects to Facebook
        log_info "Verifying FFmpeg startup and connection..."
        sleep 3
        
        # Check if session is still alive
        if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            set_status "FAILED" "FFmpeg died immediately - check FB_STREAM_KEY and source"
            log_error "Stream died immediately after startup!"
            if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
                log_info "Last log entries:"
                tail -n 20 "$LOG_FILE"
            fi
            rm -f "$TEMP_SCRIPT"
            exit 1
        fi
        
        # Check log for RTMP connection success or failures
        if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
            # Look for connection errors in log
            if grep -q "Invalid URL\|Connection refused\|Publish Rejected\|Operation not permitted" "$LOG_FILE" 2>/dev/null; then
                set_status "FAILED" "Facebook rejected stream - check FB_STREAM_KEY"
                log_error "Facebook rejected the stream connection!"
                tail -n 15 "$LOG_FILE"
                rm -f "$TEMP_SCRIPT"
                exit 1
            fi
            
            # Look for successful stream indicators
            sleep 2
            if grep -q "rtmps://\|Stream mapping:" "$LOG_FILE" 2>/dev/null && tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
                set_status "STREAMING" "Connected to Facebook"
                log_success "Stream connected successfully!"
            else
                set_status "FAILED" "Stream failed to establish - check source URL"
                log_error "Failed to establish stream!"
                tail -n 15 "$LOG_FILE"
                rm -f "$TEMP_SCRIPT"
                exit 1
            fi
        else
            # No log file - fallback to session check
            sleep 2
            if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
                set_status "STREAMING" "Session running"
                log_success "Stream session running"
            else
                set_status "FAILED" "Stream failed"
                rm -f "$TEMP_SCRIPT"
                exit 1
            fi
        fi
        
        log_info "Stream is running in background"
        if [ -n "$LOG_FILE" ]; then
            log_info "Log file: $LOG_FILE"
        fi
        
        # Clean up temp script in background
        (sleep 5 && rm -f "$TEMP_SCRIPT") &
    else
        set_status "FAILED" "Failed to create stream session"
        log_error "Failed to create stream session!"
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

    set_status "STARTING" "Initializing stream"
    
    check_requirements
    check_internet
    check_stream_key
    
    set_status "VALIDATING" "Checking source"
    check_source
    
    setup_logs
    start_stream

    echo ""
    log_success "Done!"
    echo ""
}

main "$@"