import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8476070935:AAHADgmTDVTErkm25hVUt4dWjf6g37sZKEM")

# FFmpeg Settings
FFMPEG_CMD = "ffmpeg"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Default RTMP URL - استخدام RTMPS للأمان وتجنب الحظر
FACEBOOK_RTMP_URL = "rtmps://live-api-s.facebook.com:443/rtmp/"

# Logging Settings
LOG_FILE = "stream_bot.log"

# Logo Position Settings (Simple XP Format)
# Format: "Xxp:Yyp" where X is horizontal offset (px from right), Y is vertical offset (px from top)
# Examples: "-4xp:-13yp", "-10xp:5yp", "0xp:0yp"
LOGO_POSITION = "-8xp:-13yp"  # Default: 4px from right, 13px from top

def parse_logo_position(pos_str):
    """Convert simple xp format to FFmpeg overlay filter
    Input: "-32xp:5yp" or similar
    Output: "main_w-overlay_w-32:5"
    """
    try:
        parts = pos_str.split(':')
        x = int(parts[0].replace('xp', '').strip()) if 'xp' in parts[0] else 0
        y = int(parts[1].replace('yp', '').strip()) if len(parts) > 1 and 'yp' in parts[1] else 0
        
        # Convert to FFmpeg format: main_w-overlay_w-X:Y
        ffmpeg_x = f"main_w-overlay_w-({x})" if x < 0 else f"main_w-overlay_w+{x}"
        return f"{ffmpeg_x}:{y}"
    except:
        return "main_w-overlay_w-4:-13"  # Fallback to default
