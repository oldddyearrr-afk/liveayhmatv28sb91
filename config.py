import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
FACEBOOK_RTMP_URL = "rtmps://live-api-s.facebook.com:443/rtmp/"

# إعدادات الدقة - 720p لتوفير الذاكرة على 512MB
# غيّر إلى 1080 إذا كان لديك RAM أكثر من 1GB
RESOLUTION_WIDTH = 1280
RESOLUTION_HEIGHT = 720

# تعطيل اللوجو مؤقتاً - غيّر إلى True عندما تريد تفعيله
LOGO_ENABLED = False
LOGO_PATH = "static/logo.png"
LOGO_OFFSET_X = -27
LOGO_OFFSET_Y = -36
LOGO_SIZE = "200:-1"
LOGO_OPACITY = 1.0
