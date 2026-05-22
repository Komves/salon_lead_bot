import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/bot.db").strip()

if not BOT_TOKEN:
    raise RuntimeError(f"BOT_TOKEN is empty. Create .env in project root: {ENV_PATH}")

if not ADMIN_CHAT_ID:
    print("WARNING: ADMIN_CHAT_ID is empty. Admin notifications will not work.")
