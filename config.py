import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8476070935:AAHADgmTDVTErkm25hVUt4dWjf6g37sZKEM")
FFMPEG_CMD = "ffmpeg"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
FACEBOOK_RTMP_URL = "rtmps://live-api-s.facebook.com:443/rtmp/"
LOG_FILE = "stream_bot.log"

# ═══════════════════════════════════════════════════════════
# 🎯 إعدادات الجودة - Quality Settings (نفس myproject)
# ═══════════════════════════════════════════════════════════

# الوضع الافتراضي: ULTRA (جودة عالية جداً)
QUALITY_MODE = "ultra"

# LOW - جودة منخفضة (720p @ 30fps)
LOW_RESOLUTION = "1280x720"
LOW_FPS = 30
LOW_BITRATE = "2000k"
LOW_MAXRATE = "2500k"
LOW_BUFSIZE = "4000k"
LOW_AUDIO_BITRATE = "96k"

# MEDIUM - جودة متوسطة (720p @ 30fps)
MEDIUM_RESOLUTION = "1280x720"
MEDIUM_FPS = 30
MEDIUM_BITRATE = "3000k"
MEDIUM_MAXRATE = "3500k"
MEDIUM_BUFSIZE = "6000k"
MEDIUM_AUDIO_BITRATE = "128k"

# HIGH - جودة عالية (1080p @ 30fps)
HIGH_RESOLUTION = "1920x1080"
HIGH_FPS = 30
HIGH_BITRATE = "4500k"
HIGH_MAXRATE = "5000k"
HIGH_BUFSIZE = "9000k"
HIGH_AUDIO_BITRATE = "160k"

# ULTRA ⭐ جودة عالية جداً (1080p @ 30fps) - الأفضل للبث
ULTRA_RESOLUTION = "1920x1080"
ULTRA_FPS = 30
ULTRA_BITRATE = "5000k"
ULTRA_MAXRATE = "6000k"
ULTRA_BUFSIZE = "10000k"
ULTRA_AUDIO_BITRATE = "192k"

# ═══════════════════════════════════════════════════════════
# ⚙️ إعدادات FFmpeg المتقدمة
# ═══════════════════════════════════════════════════════════

# معالج الفيديو (مثل myproject)
PRESET = "ultrafast"  # أسرع + أقل استهلاك CPU
TUNE = "zerolatency"  # للبث المباشر
PIXEL_FORMAT = "yuv420p"

# معالج الصوت
AUDIO_CODEC = "aac"  # AAC codec
AUDIO_RATE = 44100  # معيار عام
AUDIO_BITRATE = "192k"

# إعادة الاتصال (Reconnection)
RECONNECT_ENABLED = True
RECONNECT_DELAY_MAX = 2  # ثانيتين كحد أقصى
RECONNECT_ATTEMPTS = -1  # محاولات غير محدودة

# ═══════════════════════════════════════════════════════════
# 🎨 اعدادات اللوجو - Logo Settings
# ═══════════════════════════════════════════════════════════

LOGO_ENABLED = True
LOGO_PATH = "static/logo.png"
LOGO_POSITION = "topright"  # في أعلى اليمين

# الإزاحة (نفس الإعدادات من myproject)
LOGO_OFFSET_X = -27  # من الحافة اليمنى
LOGO_OFFSET_Y = -36  # من الحافة العليا

# حجم اللوجو
LOGO_SIZE = "480:-1"  # 480 بكسل عرض، حافظ على النسبة

# شفافية اللوجو (0.0 - 1.0)
LOGO_OPACITY = 1.0  # معتم بالكامل
