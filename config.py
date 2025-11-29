import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8476070935:AAHADgmTDVTErkm25hVUt4dWjf6g37sZKEM")

# FFmpeg Settings
FFMPEG_CMD = "ffmpeg"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Default RTMP URL - استخدام RTMP بدون SSL لأن FFmpeg في Replit لا يدعم RTMPS
FACEBOOK_RTMP_URL = "rtmp://live-api-s.facebook.com:80/rtmp/"

# Logging Settings
LOG_FILE = "stream_bot.log"
