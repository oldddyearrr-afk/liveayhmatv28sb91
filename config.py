import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8001928461:AAFH6AXUsWb5BSvRvxT3OZRy9x-TmT7IGKY")
FACEBOOK_RTMP_URL = "rtmps://live-api-s.facebook.com:443/rtmp/"

LOGO_ENABLED = True
LOGO_PATH = "static/logo.png"
LOGO_OFFSET_X = -27
LOGO_OFFSET_Y = -36
LOGO_SIZE = "480:-1"
LOGO_OPACITY = 1.0
