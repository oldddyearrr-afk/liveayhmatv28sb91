# 🎥 Facebook Live Stream Project

## Overview
Enhanced Facebook Live streaming project using FFmpeg and tmux with advanced features for error handling and high performance.

## Technologies Used
- **Bash**: Main programming language
- **FFmpeg 6.1.1**: Video processing and streaming
- **tmux 3.4**: Background session management

## بنية المشروع
```
.
├── main.sh          - السكريبت الرئيسي للبث (مع معالجة أخطاء ذكية)
├── config.sh        - ملف الإعدادات (جودات متعددة)
├── control.sh       - لوحة التحكم السهلة
├── .env             - متغيرات البيئة (مفتاح البث)
├── .env.example     - مثال على الإعدادات
├── logs/            - مجلد السجلات
└── README.md        - دليل الاستخدام الكامل
```

## Enhanced Features

### 1. Quality Settings (1080p Ultra)
- **Resolution**: 1920x1080 (Full HD)
- **FPS**: 30 frames/second
- **Bitrate**: 5000 kbps (adaptive)
- **Key Interval**: 2 seconds (for live streaming)
- **Audio**: Stream copy from source (no re-encoding)

### 2. Multiple Quality Modes
- **Low**: 720p @ 2000kbps (weak internet)
- **Medium**: 720p @ 3000kbps (medium quality)
- **High**: 1080p @ 4500kbps (high quality)
- **Ultra**: 1080p @ 5000kbps (best quality) ⭐
- **Custom**: Custom settings

### 3. Smart Error Handling
- ✅ Check FFmpeg & tmux installation
- ✅ Check internet connection
- ✅ Verify stream key
- ✅ Validate source URL
- ✅ Auto-reconnect on drop

### 4. Easy Control Panel
```bash
./control.sh          # Interactive menu
./control.sh start    # Start streaming
./control.sh stop     # Stop streaming
./control.sh restart  # Restart
./control.sh status   # Show status
./control.sh logs     # View logs
./control.sh attach   # Attach to stream
```

### 5. Performance Optimizations
- GPU Encoding support (NVIDIA, Intel, AMD)
- Auto-detect available GPU
- Reduced CPU usage
- Optimized buffer to avoid stuttering
- Audio stream copy (no re-encoding)

### 6. Security Features
- Stream key in environment variables (`.env`)
- `.env` file protected from Git
- No secret logging
- Config separated from code

### 7. Logging System
- Auto-logging for each stream session
- Separate files with timestamp
- Track errors and warnings
- Easy review and analysis

### 8. Logo/Watermark Support
- Add PNG logo to stream
- Position: topleft, topright, bottomleft, bottomright
- Adjustable size and opacity
- Customizable offset from edges

## كيفية الاستخدام

### الإعداد الأولي
1. انسخ `.env.example` إلى `.env`
2. احصل على مفتاح البث من: https://www.facebook.com/live/producer
3. ضع المفتاح في `.env`:
   ```
   FB_STREAM_KEY=your-actual-stream-key
   ```

### بدء البث
```bash
# الطريقة السهلة (موصى بها)
./control.sh

# أو مباشرة
./main.sh
```

### تغيير الجودة
افتح `config.sh` وعدّل:
```bash
QUALITY_MODE="ultra"  # low, medium, high, ultra, custom
```

### تخصيص المصدر
في `config.sh`:
```bash
SOURCE="https://your-stream-url.m3u8"
```

## Current Settings
- **Quality**: Ultra (1080p)
- **Bitrate**: 5000 kbps
- **FPS**: 30
- **Key Interval**: 2s
- **Auto Reconnect**: Enabled
- **GPU**: Auto-detect
- **Audio**: Stream copy (no re-encoding)
- **Logo**: Disabled by default

## المتطلبات
- ✅ FFmpeg 6.1.1 (مثبت)
- ✅ tmux 3.4 (مثبت)
- ✅ Bash 4.0+
- ✅ اتصال إنترنت مستقر
- ✅ مفتاح بث فيسبوك

## Latest Changes
- **November 14, 2025**:
  - ✅ Applied new 1080p settings (5000kbps, 30fps, 2s keyframe)
  - ✅ Created config.sh with multiple quality modes
  - ✅ Added comprehensive smart error handling
  - ✅ Created control.sh for easy control
  - ✅ Performance optimizations with GPU support
  - ✅ Enhanced security with environment variables
  - ✅ Advanced logging system
  - ✅ Created comprehensive README.md
  - ✅ Changed console output to English
  - ✅ Added audio stream copy (no re-encoding)
  - ✅ Added logo/watermark overlay support

## User Preferences
- Console output in English (better compatibility)
- Focus on simplicity and speed
- Avoid errors and issues
- High quality streaming (1080p)
- Audio stream copy for better performance
