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

# Default high-priority keywords (Vibe Coding, AI tools, MVPs, fast websites)
DEFAULT_HIGH_PRIORITY_KEYWORDS = [
    "vibe coding",
    "вайбкодинг",
    "vibe coder",
    "landing page",
    "лендинг",
    "одностраничник",
    "сайт визитка",
    "простой сайт",
    "сделать сайт",
    "нужен сайт",
    "prototype",
    "прототип",
    "mvp",
    "минимальный продукт",
    "quick website",
    "быстрый сайт",
    "bolt.new",
    "lovable.dev",
    "v0.dev",
    "cursor",
    "cursor.sh",
    "windsurf",
    "prompt",
    "промпт",
    "промпт инжиниринг",
    "next.js",
    "react",
    "tailwind",
    "vite",
    "html css",
    "ai website",
    "ai-генерация сайта",
    "сайт на нейросети",
    "нейросеть сайт",
    "web design",
    "дизайн сайта",
    "figma в сайт",
    "figma to html",
    "figma to react",
    "speed development",
    "сайт за день",
    "сайт за 2 часа"
]

# Default negative keywords (Enterprise, Full-Time, heavy backends)
DEFAULT_NEGATIVE_KEYWORDS = [
    "senior",
    "5+ years",
    "10+ years",
    "lead developer",
    "unpaid",
    "free",
    "бесплатно",
    "без оплаты",
    "за отзыв",
    "relocation",
    "office full-time",
    "работа в офисе",
    "штат",
    "angular",
    "java backend",
    "c# net",
    "c++",
    "kubernetes",
    "devops",
    "cloud architect",
    "casino",
    "gambling",
    "crypto scam",
    "adult"
]

# Default list of sources
DEFAULT_SOURCES = [
    {"name": "mock", "enabled": 0},
    {"name": "telegram", "enabled": 1},
    {"name": "freelancehunt", "enabled": 0},
    {"name": "kwork", "enabled": 1},
    {"name": "flru", "enabled": 0},
    {"name": "reddit", "enabled": 0}
]
