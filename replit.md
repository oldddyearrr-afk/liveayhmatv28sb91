# Telegram Bot - Facebook Live Streaming

## Project Overview
Telegram bot that streams live video from multiple sources (Periscope/Twitter, YouTube, Twitch) to Facebook Live with customizable logo overlay and anti-detection features.

## Recent Changes (Dec 1, 2025)

### Major Rewrite: Stream Approach Fixed ✅
- **Problem**: FFmpeg started but didn't transmit data to Facebook - connection failed despite proper flags
- **Solution**: Adopted proven tmux-based approach from working reference project (`myproject/*.sh`)
- **Key Improvements**:
  1. **Process Management**: Switched from subprocess.Popen to tmux sessions (like reference scripts)
  2. **FFmpeg Input Parameters**: 
     - Proper reconnection flags: `-multiple_requests`, `-reconnect`, `-reconnect_streamed`, `-reconnect_at_eof`
     - Fast analysis: `-analyzeduration 2000000`, `-probesize 2000000`
     - Better timeouts: `-timeout 5000000`, `-rw_timeout 5000000`
  3. **Output Format**: FLV with proper flags: `-flvflags no_duration_filesize+no_metadata`
  4. **Connection Verification**: Checks if tmux session survives 3 seconds, then 8 seconds (ensures real connection)
  5. **Monitoring**: Background thread monitors stream health

### Architecture Changes
```
OLD: subprocess.Popen → wait 10s → check if alive → start monitor
NEW: tmux session → wait 3s → verify alive → wait 5s → verify again → monitor
```

## Project Structure
```
.
├── bot.py                    # Telegram bot with command handlers
├── stream.py                 # Stream manager (NOW using tmux approach)
├── config.py                 # Configuration and constants
├── anti_detection.py         # Anti-detection techniques
├── preview_app.py            # Logo preview web app
├── requirements.txt          # Python dependencies
├── static/logo.png          # Logo overlay image
├── templates/preview.html   # Logo preview template
└── myproject/               # Reference scripts (working approach)
    ├── main (1).sh          # Main streaming script (reference)
    ├── config (1).sh        # Configuration file (reference)
    └── control (1).sh       # Control panel script (reference)
```

## How It Works Now

### FFmpeg Command Flow
1. **Input parameters** (before `-i`):
   - Reconnection: Automatic reconnect with exponential backoff
   - Analysis: Fast M3U8 parsing
   - Timeouts: Long timeouts for weak sources
   
2. **Encoding**:
   - Codec: libx264 (CPU-friendly)
   - Preset: ultrafast (low latency)
   - Bitrate: 5000k/6000k (high quality)
   
3. **Output** (to Facebook RTMPS):
   - Format: FLV (Facebook native)
   - Flags: No duration/metadata overhead
   - Flush: Every packet sent immediately

### Process Management (Tmux-Based)
```
Start: tmux new-session -d -s fbstream "ffmpeg ..."
Monitor: tmux has-session -t fbstream (every 5 seconds)
Stop: tmux kill-session -t fbstream
```

## User Flow

1. User sends `/stream` command
2. Bot asks for M3U8 URL
3. User provides M3U8 URL (any valid HLS/Live stream)
4. Bot parses M3U8 and selects best quality automatically
5. Bot asks for Facebook Stream Key
6. User provides Stream Key from Facebook Live page
7. Bot starts streaming via tmux session
8. Bot verifies connection (survives 8+ seconds)
9. User sees "البث يعمل" (Stream is working) message
10. Video appears on Facebook Live page

## Supported Sources
- **Periscope/Twitter**: Full support with auto quality detection
- **YouTube Live**: Supported (requires extractable M3U8)
- **Twitch**: Supported (requires extractable M3U8)
- **Any HLS Stream**: M3U8 format required

## Anti-Detection Features
- Random user agents
- Random FFmpeg parameters
- Stream spacing (delays between commands)
- Protocol whitelisting
- TLS/SSL bypass for non-standard certificates

## Deployment
- **Port 8000**: Health check (GET /)
- **Port 5000**: Logo preview (GET /)
- **Telegram Bot**: Uses polling (getUpdates)
- **Render.com**: Ready (uses health check on port 8000)

## Known Working Test Case
- **Source**: `https://prod-fastly-us-west-2.video.pscp.tv:443/Transcoding/.../master_dynamic_highlatency.m3u8?type=live`
- **Status**: Stable 4+ day streaming in reference project
- **Quality**: Auto-detected, stable

## Next Steps for User Testing
1. Get fresh M3U8 URL from Periscope/Twitter/other source
2. Get active Facebook Stream Key from Facebook Live page
3. Send `/stream` command to bot
4. Provide M3U8 URL and Stream Key
5. Check Facebook Live page for video
6. If working: ✅ Problem solved
7. If not: Check FFmpeg logs in `/tmp/fbstream_*.log`

## Configuration
Edit `config.py` to adjust:
- Logo size and position
- FFmpeg command location
- Facebook RTMP server
- Logging verbosity

## Debugging
- **Bot logs**: Show FFmpeg startup status
- **Tmux session logs**: `tmux capture-pane -t fbstream -p`
- **FFmpeg logs**: Check `/tmp/ffmpeg_output.log`
- **Status**: `/api/status` endpoint via health check server
