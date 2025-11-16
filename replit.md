# Facebook Live Stream Rebroadcasting System

## Overview

This is a Facebook Live rebroadcasting system that takes video from any source (HLS/DASH/RTMP) and streams it to Facebook Live using FFmpeg. The system includes:

- Arabic web interface for easy control
- CLI control panel for terminal management
- Automatic reconnection and monitoring
- Support for custom logo overlay
- Two streaming modes: direct copy (fast) and re-encoding (with logo support)
- Automatic log cleanup and health monitoring

The system is designed to run 24/7 with automatic recovery from connection failures.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Performance Improvements (Nov 2025)

**Speed Optimizations:**
- Reduced connection time from ~38s to ~15-20s
- Removed unnecessary delays in web_app.py (6.3s → 1s)
- Optimized FFmpeg timeouts and buffer settings
- Faster validation checks with log-based verification

**Code Quality:**
- Removed deprecated FFmpeg flags (-async, -strict experimental)
- Eliminated interactive prompts causing headless mode hangs
- Fixed buffer blocking issues (stdout/stderr → DEVNULL)
- Added STATUS_FILE system for real-time state tracking

**Reliability:**
- Improved error detection via log analysis
- Better failure reporting with specific error messages
- Cleanup handler preserves failure states for diagnostics
- Enhanced RTMP connection validation

## System Architecture

### Frontend Architecture

**Web Interface (Flask)**
- Single-page application using Flask
- Real-time status monitoring via AJAX polling
- Arabic-first UI with RTL support
- Controls for starting, stopping, and monitoring streams
- Visual status indicators for stream health
- Logo configuration interface

**Technology Stack:**
- Flask for web server
- Jinja2 templates for HTML rendering
- JavaScript for dynamic status updates
- Bootstrap for responsive UI (implied from web app structure)

### Backend Architecture

**Core Streaming Engine**
- **Main Component**: `main.sh` - Bash script that orchestrates FFmpeg streaming
- **Process Management**: Uses tmux for background execution and persistence
- **Configuration Management**: Centralized in `config.sh` with environment variable support
- **Status Tracking**: File-based status system (`/tmp/fbstream_status.txt`)

**Streaming Modes:**

1. **Stream Copy Mode** (Default)
   - Direct copy without re-encoding
   - Zero CPU usage for transcoding
   - 100% original quality
   - No logo support (requires pixel manipulation)

2. **Encode Mode**
   - Full re-encoding with FFmpeg
   - Supports logo overlay with positioning and opacity
   - Configurable quality presets (low, medium, high, ultra, custom)
   - GPU acceleration support (NVIDIA, Intel, AMD)

**Architecture Decision Rationale:**
- Bash scripts chosen for simplicity and direct FFmpeg integration
- tmux selected for reliable background process management without requiring systemd
- File-based status tracking for simplicity and cross-process communication
- Dual-mode approach balances performance (copy) vs features (encode)

### Monitoring and Recovery System

**Automatic Monitoring**
- `monitor_stream.sh`: Checks stream health every 10 seconds
- Automatic restart on failure detection
- Separate monitoring logs for debugging
- Integration with control script via `./control.sh monitor`

**Connection Resilience:**
- Automatic reconnection on network failures
- Retry logic for HTTP errors (4xx, 5xx)
- Configurable timeout and buffer settings
- Facebook RTMP server connectivity validation

**Log Management:**
- `cleanup_logs.sh`: Automatic log rotation and cleanup
- Prevents disk space exhaustion
- Maintains recent logs for debugging

### Configuration System

**Hierarchical Configuration:**
1. `config.sh` - Base configuration file
2. Replit Secrets - Sensitive data (FB_STREAM_KEY)
3. Runtime parameters - Command-line overrides

**Key Configuration Categories:**
- Source settings (video input URL)
- Quality presets (resolution, bitrate, FPS)
- Logo customization (size, position, opacity)
- Streaming mode selection (copy vs encode)
- Advanced FFmpeg parameters
- Monitoring intervals

**Design Philosophy:**
- Configuration separated from logic
- Sensible defaults with override capability
- Support for both simple and advanced use cases

### Process Architecture

**Process Flow:**
1. User triggers stream via web UI or CLI
2. `control.sh` validates configuration and prerequisites
3. `main.sh` launched in tmux session named 'fbstream'
4. FFmpeg process streams to Facebook RTMP endpoint
5. Optional: `monitor_stream.sh` watches for failures
6. Status updates written to status file
7. Web UI polls status file for real-time updates

**Session Management:**
- Single tmux session prevents duplicate streams
- Session naming convention: 'fbstream'
- Clean shutdown ensures no orphaned processes

## External Dependencies

### Core Dependencies

**FFmpeg**
- Purpose: Video encoding, transcoding, and streaming
- Features used:
  - RTMP protocol support
  - HLS/DASH input handling
  - Video filtering (logo overlay)
  - Hardware acceleration (optional)
- Required codecs: H.264/AAC for Facebook compatibility

**tmux**
- Purpose: Terminal multiplexer for background process management
- Enables detached streaming sessions
- Survives SSH disconnections

### Third-Party Services

**Facebook Live API**
- RTMP endpoint: `rtmps://live-api-s.facebook.com:443/rtmp/`
- Authentication: Stream key from Facebook Creator Studio
- Protocol: RTMPS (RTMP over TLS)
- Requirements:
  - Valid stream key stored in Replit Secrets
  - Active Facebook page or profile with streaming permissions

### Platform-Specific Integrations

**Replit Environment**
- Secrets management for FB_STREAM_KEY
- Persistent file system for logs and configuration
- Network access for RTMP streaming
- Python 3 runtime for Flask web server

### Optional Integrations

**GPU Acceleration** (if available)
- NVIDIA: NVENC encoder
- Intel: Quick Sync Video
- AMD: VCE/AMF encoder
- Falls back to software encoding if unavailable

**Logo System**
- Accepts PNG files with transparency
- FFmpeg overlay filter for positioning
- Only available in encode mode

### Network Dependencies

**Required Network Access:**
- Outbound RTMPS (port 443) to Facebook servers
- HTTP/HTTPS for source video URLs (HLS/DASH)
- Inbound HTTP (web interface)

**Bandwidth Considerations:**
- Input: Depends on source quality
- Output: Configured via quality presets (varies from ~1 Mbps to 10+ Mbps)
- Monitoring: Minimal overhead