import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/bot.db").strip()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip()
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Europe/Moscow").strip()
REMINDER_MINUTES_BEFORE = int(os.getenv("REMINDER_MINUTES_BEFORE", "60"))
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not BOT_TOKEN:
    raise RuntimeError(f"BOT_TOKEN is empty. Create .env in project root: {ENV_PATH}")

if not ADMIN_CHAT_ID:
    print("WARNING: ADMIN_CHAT_ID is empty. Admin notifications will not work.")
