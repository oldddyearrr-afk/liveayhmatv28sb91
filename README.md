# 🎥 Facebook Live Stream

Enhanced Facebook Live streaming using FFmpeg with advanced features.

## ✨ Features

- ✅ **Optimized 1080p Settings**: 5000kbps, 30fps, 2s key interval
- ✅ **Multiple Quality Presets**: Low, Medium, High, Ultra
- ✅ **Smart Error Handling**: Auto-check internet, source, and keys
- ✅ **Easy Control Panel**: Simple commands to manage streaming
- ✅ **GPU Acceleration**: Support for NVIDIA, Intel, AMD
- ✅ **Enhanced Security**: Stream key in environment variables
- ✅ **Advanced Logging**: Complete logging for each stream session
- ✅ **Auto Reconnect**: Reconnects automatically on internet drop
- ✅ **Audio Stream Copy**: Copy audio directly from source (faster, no re-encoding)
- ✅ **Logo Overlay**: Add watermark/logo to your stream

## 🚀 Quick Start

### 1. Initial Setup

```bash
# Copy example config
cp .env.example .env

# Edit .env and add your stream key
nano .env
```

### 2. Get Stream Key from Facebook

1. Go to: https://www.facebook.com/live/producer
2. Select "Go Live"
3. Copy "Stream Key"
4. Put it in `.env`:

```
FB_STREAM_KEY=your-actual-stream-key-here
```

### 3. Start Streaming

```bash
# Method 1: Using control panel (recommended)
./control.sh

# Method 2: Direct start
./main.sh
```

## 📋 Using Control Panel

```bash
# Show interactive menu
./control.sh

# Or use direct commands:
./control.sh start      # Start streaming
./control.sh stop       # Stop streaming
./control.sh restart    # Restart streaming
./control.sh status     # Check status
./control.sh logs       # View logs
./control.sh attach     # Attach to stream session
```

## ⚙️ Configuration

### Change Quality

Edit `config.sh`:

```bash
# Choose: low, medium, high, ultra, custom
QUALITY_MODE="ultra"
```

### Audio Settings

By default, audio is copied from source (faster):

```bash
# In config.sh
AUDIO_CODEC="copy"  # Stream copy (no re-encoding)
# Or
AUDIO_CODEC="aac"   # Re-encode audio
```

### Add Logo/Watermark

Edit `config.sh`:

```bash
# Enable logo
LOGO_ENABLED="true"

# Set logo file path (PNG with transparency recommended)
LOGO_PATH="logo.png"

# Position: topleft, topright, bottomleft, bottomright
LOGO_POSITION="topright"

# Offset from edges (pixels)
LOGO_OFFSET_X="10"
LOGO_OFFSET_Y="10"

# Size (WxH, leave empty for original size)
LOGO_SIZE=""  # Example: "200:100"

# Opacity (0.0 to 1.0)
LOGO_OPACITY="1.0"
```

### Change Video Source

```bash
# In config.sh
SOURCE="https://your-stream-url.m3u8"
```

### Custom Settings

```bash
# In config.sh - CUSTOM section
CUSTOM_RESOLUTION="1920x1080"
CUSTOM_FPS="30"
CUSTOM_BITRATE="5000k"
CUSTOM_MAXRATE="6000k"
CUSTOM_KEYINT="2"  # Key interval in seconds
```

## 🎮 Available Quality Modes

| Mode | Resolution | FPS | Bitrate | Use Case |
|------|-----------|-----|---------|----------|
| Low | 720p | 30 | 2000k | Weak internet |
| Medium | 720p | 30 | 3000k | Medium quality |
| High | 1080p | 30 | 4500k | High quality |
| **Ultra** | **1080p** | **30** | **5000k** | **Best quality** ⭐ |
| Custom | Custom | Custom | Custom | Your settings |

## 🛡️ Security Features

- ✅ Stream key in environment variables (not in code)
- ✅ `.env` file protected from Git
- ✅ No secret logging
- ✅ Separate config from code

## 📊 Monitor Streaming

### View Status

```bash
./control.sh status
```

Shows:
- Stream status (running/stopped)
- CPU & RAM usage
- Uptime
- Log file location

### Attach to Live Stream

```bash
./control.sh attach

# To detach without stopping:
# Press: Ctrl+B then D
```

### Read Logs

```bash
# Last 30 lines
./control.sh logs

# Or read full file
cat logs/stream_*.log
```

## 🚨 Error Handling

The project automatically checks:

1. ✅ FFmpeg & tmux installation
2. ✅ Internet connection
3. ✅ Stream key presence
4. ✅ Source URL validity

If an error occurs, you'll get a clear message explaining the issue.

## 💻 Performance Optimizations

### GPU Usage (if available)

Auto-detects:
- NVIDIA GPU (h264_nvenc)
- Intel GPU (h264_vaapi, h264_qsv)
- AMD GPU (h264_amf)

Manual control in `config.sh`:

```bash
USE_GPU="auto"    # Auto-detect (recommended)
USE_GPU="nvidia"  # NVIDIA only
USE_GPU="off"     # CPU only
```

### Audio Stream Copy

By default, audio is copied directly from source:
- ✅ Faster processing
- ✅ No quality loss
- ✅ Lower CPU usage
- ✅ Preserves original audio codec

## 📁 Project Structure

```
.
├── main.sh          # Main streaming script
├── config.sh        # Configuration file
├── control.sh       # Control panel
├── .env             # Environment variables (secret)
├── .env.example     # Example config
├── logs/            # Log files directory
└── README.md        # This file
```

## 🔧 System Requirements

- ✅ FFmpeg (installed automatically)
- ✅ tmux (installed automatically)
- ✅ Bash 4.0+
- ✅ Stable internet connection

## 📝 Important Notes

1. **Don't share stream key**: `.env` file is protected and shouldn't be shared
2. **Current settings**: Ultra mode (1080p, 5000kbps, 30fps)
3. **Key interval**: 2 seconds (optimal for live streaming)
4. **Auto reconnect**: Automatically reconnects on internet drop
5. **Audio**: Stream copy by default (no re-encoding)

## 🆘 Help

```bash
# Show help
./control.sh help
```

## 📖 Examples

### Basic Streaming

```bash
# Start stream
./control.sh start

# Check if running
./control.sh status

# Stop stream
./control.sh stop
```

### With Logo

1. Place your logo file (PNG recommended): `logo.png`
2. Edit `config.sh`:
   ```bash
   LOGO_ENABLED="true"
   LOGO_PATH="logo.png"
   LOGO_POSITION="topright"
   ```
3. Start stream: `./control.sh start`

### Change Quality on the Fly

1. Stop current stream: `./control.sh stop`
2. Edit `config.sh`: `QUALITY_MODE="high"`
3. Restart: `./control.sh start`

## 📄 License

Open source - use it as you wish! 🎉
