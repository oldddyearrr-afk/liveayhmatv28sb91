#!/bin/bash

# ═══════════════════════════════════════════════════════════
# Facebook Live Stream - Control Panel
# ═══════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh" 2>/dev/null || SESSION_NAME="fbstream"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════
# Logging functions
# ═══════════════════════════════════════════════════════════

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}   Facebook Live Stream - Control Panel   ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
    echo ""
}

check_secrets_env() {
    # Stream key is now provided via web UI
    return 0
}

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
# Get stream status
# ═══════════════════════════════════════════════════════════

get_stream_status() {
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo "running"
    else
        echo "stopped"
    fi
}

# ═══════════════════════════════════════════════════════════
# Start stream
# ═══════════════════════════════════════════════════════════

start_stream() {
    local status=$(get_stream_status)
    local stream_key="${1:-}"
    
    if [ "$status" = "running" ]; then
        log_warning "Stream is already running!"
        return 0
    fi
    
    # If stream_key provided as parameter, use it
    if [ -n "$stream_key" ]; then
        export FB_STREAM_KEY="$stream_key"
        log_success "Using provided stream key from parameter"
    else
        # Try to read from environment (Replit Secrets)
        log_info "Checking for stream key in Replit Secrets..."
        
        if [ -z "$FB_STREAM_KEY" ]; then
            check_secrets_env
            return 1
        fi
        
        log_success "Stream key found in Replit Secrets"
    fi
    
    # Ensure FB_STREAM_KEY is exported for child processes
    export FB_STREAM_KEY
    
    log_info "Starting stream..."
    log_info "Stream key: ${FB_STREAM_KEY:0:10}..." # Show first 10 chars only
    echo ""
    
    # Run main.sh with exported environment
    FB_STREAM_KEY="$FB_STREAM_KEY" bash "$SCRIPT_DIR/main.sh"
}

# ═══════════════════════════════════════════════════════════
# Stop stream
# ═══════════════════════════════════════════════════════════

stop_stream() {
    local status=$(get_stream_status)
    
    if [ "$status" = "stopped" ]; then
        log_warning "Stream is already stopped"
        return 1
    fi
    
    log_info "Stopping stream..."
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null
    
    sleep 1
    
    if [ "$(get_stream_status)" = "stopped" ]; then
        log_success "Stream stopped successfully"
    else
        log_error "Failed to stop stream"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════
# Restart stream
# ═══════════════════════════════════════════════════════════

restart_stream() {
    log_info "Restarting stream..."
    
    if [ "$(get_stream_status)" = "running" ]; then
        stop_stream
        sleep 2
    fi
    
    start_stream
}

# ═══════════════════════════════════════════════════════════
# Show stream status
# ═══════════════════════════════════════════════════════════

show_status() {
    local status=$(get_stream_status)
    
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}           Current Stream Status            ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ "$status" = "running" ]; then
        echo -e "${GREEN}Status: RUNNING${NC}"
        echo ""
        
        if command -v pgrep &> /dev/null && pgrep -f "ffmpeg.*$SESSION_NAME" &> /dev/null; then
            local pid=$(pgrep -f "ffmpeg.*flv" | head -1)
            if [ -n "$pid" ]; then
                echo -e "${BLUE}Process ID:${NC} $pid"
                
                if command -v ps &> /dev/null; then
                    local cpu=$(ps -p $pid -o %cpu --no-headers 2>/dev/null | tr -d ' ')
                    local mem=$(ps -p $pid -o %mem --no-headers 2>/dev/null | tr -d ' ')
                    local runtime=$(ps -p $pid -o etime --no-headers 2>/dev/null | tr -d ' ')
                    
                    [ -n "$cpu" ] && echo -e "${BLUE}CPU Usage:${NC} ${cpu}%"
                    [ -n "$mem" ] && echo -e "${BLUE}RAM Usage:${NC} ${mem}%"
                    [ -n "$runtime" ] && echo -e "${BLUE}Uptime:${NC} $runtime"
                fi
            fi
        fi
        
        if [ -d "logs" ] && [ "$(ls -A logs 2>/dev/null)" ]; then
            local latest_log=$(ls -t logs/*.log 2>/dev/null | head -1)
            if [ -n "$latest_log" ]; then
                echo -e "${BLUE}Latest log:${NC} $latest_log"
            fi
        fi
        
        echo ""
        log_info "To view live stream:"
        echo -e "  ${GREEN}tmux attach -t $SESSION_NAME${NC}"
        echo -e "  ${YELLOW}(Press Ctrl+B then D to detach)${NC}"
        
    else
        echo -e "${RED}Status: STOPPED${NC}"
        echo ""
        log_info "To start the stream:"
        echo -e "  ${GREEN}./control.sh start${NC}"
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════
# Show logs
# ═══════════════════════════════════════════════════════════

show_logs() {
    if [ ! -d "logs" ] || [ ! "$(ls -A logs 2>/dev/null)" ]; then
        log_warning "No logs available yet"
        return 1
    fi
    
    local latest_log=$(ls -t logs/*.log 2>/dev/null | head -1)
    
    if [ -z "$latest_log" ]; then
        log_warning "No logs found"
        return 1
    fi
    
    log_info "Showing last 30 lines from log..."
    echo ""
    tail -n 30 "$latest_log"
}

# ═══════════════════════════════════════════════════════════
# Attach to tmux session
# ═══════════════════════════════════════════════════════════

attach_stream() {
    local status=$(get_stream_status)
    
    if [ "$status" = "stopped" ]; then
        log_error "Stream is not running!"
        log_info "Start it first: ./control.sh start"
        return 1
    fi
    
    log_info "Attaching to stream session..."
    log_warning "To detach: Press Ctrl+B then D (won't stop stream)"
    sleep 2
    tmux attach -t "$SESSION_NAME"
}

# ═══════════════════════════════════════════════════════════
# Show help
# ═══════════════════════════════════════════════════════════

start_with_monitor() {
    log_info "Starting stream with auto-monitor..."
    bash "$SCRIPT_DIR/start_with_monitor.sh"
}

show_help() {
    print_header
    echo -e "${CYAN}Usage:${NC}"
    echo -e "  ./control.sh ${GREEN}[command]${NC} ${YELLOW}[stream_key]${NC}"
    echo ""
    echo -e "${CYAN}Available Commands:${NC}"
    echo ""
    echo -e "  ${GREEN}start${NC} ${YELLOW}[key]${NC}  - Start streaming (optional: provide stream key)"
    echo -e "  ${GREEN}monitor${NC}      - Start with auto-restart on failure ⭐"
    echo -e "  ${GREEN}stop${NC}         - Stop streaming"
    echo -e "  ${GREEN}restart${NC}      - Restart streaming"
    echo -e "  ${GREEN}status${NC}       - Show stream status"
    echo -e "  ${GREEN}logs${NC}         - Show log files"
    echo -e "  ${GREEN}attach${NC}       - Attach to stream session"
    echo -e "  ${GREEN}help${NC}         - Show this help"
    echo ""
    echo -e "${CYAN}Setup Instructions:${NC}"
    echo -e "  ${YELLOW}1.${NC} Add ${GREEN}FB_STREAM_KEY${NC} to Replit Secrets (🔒 icon)"
    echo -e "  ${YELLOW}2.${NC} Configure ${GREEN}SOURCE${NC} URL in config.sh"
    echo -e "  ${YELLOW}3.${NC} Run: ${GREEN}./control.sh monitor${NC} (recommended)"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo -e "  ./control.sh monitor                  ${BLUE}# Start with auto-restart ⭐${NC}"
    echo -e "  ./control.sh start                    ${BLUE}# Use FB_STREAM_KEY from Secrets${NC}"
    echo -e "  ./control.sh start YOUR_KEY_HERE      ${BLUE}# Use provided stream key${NC}"
    echo -e "  ./control.sh status                   ${BLUE}# Check stream status${NC}"
    echo -e "  ./control.sh logs                     ${BLUE}# View logs${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════
# Interactive menu
# ═══════════════════════════════════════════════════════════

interactive_menu() {
    while true; do
        print_header
        
        local status=$(get_stream_status)
        if [ "$status" = "running" ]; then
            echo -e "${GREEN}Status: RUNNING${NC}"
        else
            echo -e "${RED}Status: STOPPED${NC}"
        fi
        
        echo ""
        echo -e "${CYAN}Select an option:${NC}"
        echo ""
        echo "  1) Start Stream"
        echo "  2) Stop Stream"
        echo "  3) Restart Stream"
        echo "  4) Show Status"
        echo "  5) Show Logs"
        echo "  6) Attach to Stream"
        echo "  0) Exit"
        echo ""
        read -p "Your choice: " choice
        
        case $choice in
            1) start_stream; read -p "Press Enter to continue..." ;;
            2) stop_stream; read -p "Press Enter to continue..." ;;
            3) restart_stream; read -p "Press Enter to continue..." ;;
            4) show_status; read -p "Press Enter to continue..." ;;
            5) show_logs; read -p "Press Enter to continue..." ;;
            6) attach_stream ;;
            0) log_info "Goodbye!"; exit 0 ;;
            *) log_error "Invalid option"; sleep 1 ;;
        esac
    done
}

# ═══════════════════════════════════════════════════════════
# Main program
# ═══════════════════════════════════════════════════════════

main() {
    case "${1:-}" in
        start)
            print_header
            start_stream "${2:-}"
            ;;
        monitor)
            print_header
            start_with_monitor
            ;;
        stop)
            print_header
            stop_stream
            ;;
        restart)
            print_header
            restart_stream
            ;;
        status)
            print_header
            show_status
            ;;
        logs)
            print_header
            show_logs
            ;;
        attach)
            attach_stream
            ;;
        help|--help|-h)
            show_help
            ;;
        menu|"")
            interactive_menu
            ;;
        *)
            log_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
