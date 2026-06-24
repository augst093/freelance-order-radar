import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Config variables with defaults
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "0")) if os.getenv("TELEGRAM_USER_ID") else 0
SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES", "5"))
MIN_SCORE_TO_NOTIFY = int(os.getenv("MIN_SCORE_TO_NOTIFY", "7"))
MAX_NOTIFICATIONS_PER_SCAN = int(os.getenv("MAX_NOTIFICATIONS_PER_SCAN", "5"))
FRESHNESS_MAX_MINUTES = int(os.getenv("FRESHNESS_MAX_MINUTES", "60"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "freelance_radar.db")

import sys

# Ensure database path is absolute or relative to base dir
if not os.path.isabs(DATABASE_PATH):
    if os.path.exists("/data") and sys.platform != "win32":
        DATABASE_PATH = "/data/freelance_radar.db"
    else:
        DATABASE_PATH = str(BASE_DIR / DATABASE_PATH)

# Default high-priority keywords
DEFAULT_HIGH_PRIORITY_KEYWORDS = [
    "landing page",
    "лендинг",
    "сайт",
    "website",
    "web design",
    "сделать сайт",
    "нужен сайт",
    "нужна страница",
    "сайт под ключ",
    "html css",
    "javascript",
    "frontend",
    "telegram bot",
    "телеграм бот",
    "бот",
    "automation",
    "автоматизация",
    "python script",
    "python бот",
    "AI video",
    "AI images",
    "нейросеть",
    "reels",
    "shorts",
    "tiktok",
    "ugc",
    "ai ugc",
    "content creation",
    "генерация видео",
    "генерация изображений",
    "дизайн",
    "презентация",
    "product page",
    "portfolio website",
    "business website"
]

# Default negative keywords
DEFAULT_NEGATIVE_KEYWORDS = [
    "senior full-time",
    "full time office",
    "relocation",
    "5 years experience",
    "unpaid",
    "internship unpaid",
    "only agency",
    "casino",
    "adult",
    "gambling",
    "crypto scam",
    "dropshipping spam",
    "need free",
    "бесплатно",
    "за отзыв",
    "без оплаты"
]

# Default list of sources
DEFAULT_SOURCES = [
    {"name": "mock", "enabled": 0},
    {"name": "telegram", "enabled": 1},
    {"name": "freelancehunt", "enabled": 1},
    {"name": "kwork", "enabled": 1},
    {"name": "flru", "enabled": 0},
    {"name": "reddit", "enabled": 0}
]
