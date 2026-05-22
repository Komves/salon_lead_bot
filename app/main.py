import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram import Bot, Dispatcher
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import BOT_TOKEN
from app.db import init_db
from app.handlers_admin import router as admin_router
from app.handlers_client import router as client_router
from app.api import router as api_router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def run_bot() -> None:
    dp.include_router(admin_router)
    dp.include_router(client_router)

    me = await bot.get_me()
    print(f"BOT CONNECTED: @{me.username}")

    await bot.delete_webhook(drop_pending_updates=True)
    print("WEBHOOK DELETED")
    print("BOT STARTED")

    await dp.start_polling(bot)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    bot_task = asyncio.create_task(run_bot())
    try:
        yield
    finally:
        bot_task.cancel()
        await bot.session.close()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def miniapp() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
