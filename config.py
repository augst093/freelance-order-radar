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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

import sys

# Ensure database path is absolute or relative to base dir
if not os.path.isabs(DATABASE_PATH):
    if os.path.exists("/data") and sys.platform != "win32":
        DATABASE_PATH = "/data/freelance_radar.db"
    else:
        DATABASE_PATH = str(BASE_DIR / DATABASE_PATH)

# Default high-priority keywords (Vibe Coding, AI tools, MVPs, fast websites)
DEFAULT_HIGH_PRIORITY_KEYWORDS = [
    # --- Русскоязычные: сайты и лендинги ---
    "нужен сайт",
    "нужен лендинг",
    "сделать сайт",
    "сделать лендинг",
    "создать сайт",
    "создать лендинг",
    "разработать сайт",
    "разработать лендинг",
    "сайт под ключ",
    "лендинг под ключ",
    "сайт визитка",
    "промо сайт",
    "промо-сайт",
    "одностраничник",
    "многостраничный сайт",
    "адаптивный сайт",
    "адаптивная верстка",
    "верстка сайта",
    "сверстать сайт",
    "сверстать лендинг",
    "доработать сайт",
    "редизайн сайта",
    "дизайн сайта",
    "ui сайта",
    "ux сайта",
    "figma сайт",
    "figma лендинг",
    # --- Платформы и технологии ---
    "tilda",
    "тильда",
    "zero block",
    "webflow",
    "wordpress сайт",
    "react",
    "next.js",
    "nextjs",
    "tailwind",
    "frontend",
    "front-end",
    "фронтенд",
    "веб-разработчик",
    # --- Англоязычные: сайты ---
    "web developer",
    "landing page",
    "need website",
    "need landing",
    "build website",
    "build landing",
    "website design",
    "website redesign",
    "frontend developer",
    "react developer",
    "next.js developer",
    # --- Телеграм-боты ---
    "telegram bot",
    "телеграм бот",
    "telegram-бот",
    "нужен бот",
    "сделать бота",
    "разработать бота",
    "бот для телеграм",
    "чат бот",
    "чат-бот",
    "ai bot",
    "ии бот",
    "gpt bot",
    # --- Скрипты и автоматизация ---
    "бот на python",
    "python бот",
    "ai automation",
    "ии автоматизация",
    "автоматизация",
    "скрипт",
    "парсер",
    # --- Mini/Web App ---
    "mini app",
    "telegram mini app",
    "web app",
    "tg mini app",
    # --- Vibe Coding / AI генерация ---
    "vibe coding",
    "вайбкодинг",
    "vibe coder",
    "bolt.new",
    "lovable.dev",
    "v0.dev",
    "cursor",
    "windsurf",
    "mvp",
    "прототип",
]

# Default negative keywords (Enterprise, Full-Time, heavy backends, SMM, HR, etc.)
DEFAULT_NEGATIVE_KEYWORDS = [
    # --- Маркетинг / SMM ---
    "smm",
    "смм",
    "smmщик",
    "сммщик",
    "таргетолог",
    "таргет",
    "реклама",
    "директолог",
    "маркетолог",
    "контент",
    "контентщик",
    "контент-менеджер",
    "рилс",
    "reels",
    "shorts",
    "tiktok",
    "тик ток",
    # --- Видео / Текст ---
    "монтажер",
    "монтажёр",
    "видеомонтаж",
    "копирайтер",
    "копирайтинг",
    "редактор",
    "сценарист",
    "сторис",
    # --- Дизайн карточек / Маркетплейсы ---
    "дизайн карточек",
    "карточки wb",
    "wildberries",
    "ozon",
    "маркетплейс менеджер",
    "менеджер маркетплейсов",
    # --- Административные роли ---
    "ассистент",
    "личный ассистент",
    "менеджер",
    "администратор",
    "оператор",
    "колл центр",
    "продажник",
    "sales",
    "hr",
    "рекрутер",
    # --- Формат работы ---
    "офис",
    "в офис",
    "гибрид",
    "full-time",
    "фуллтайм",
    "ставка",
    "зарплата",
    "оклад",
    # --- Уровень / Стажировка ---
    "middle",
    "senior",
    "team lead",
    "тимлид",
    "стажировка",
    "стажер",
    "стажёр",
    # --- Поиск работы (не заказы) ---
    "ищу работу",
    "резюме",
    "ищу заказы",
    "ищу проект",
    # --- Оплата ---
    "unpaid",
    "free",
    "бесплатно",
    "без оплаты",
    "за отзыв",
    # --- Тяжёлые бэкенды / Enterprise ---
    "5+ years",
    "10+ years",
    "lead developer",
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
    "adult",
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
