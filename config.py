from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_TOKEN = TELEGRAM_BOT_TOKEN
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
AI_API_URL = os.getenv("AI_API_URL")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL")
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", 19))
SCHEDULE_MIN = int(os.getenv("SCHEDULE_MIN", 30))
TZ = os.getenv("TZ", "Europe/Moscow")
