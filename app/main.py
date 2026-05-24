import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import BOT_TOKEN, PUBLIC_BASE_URL
from app.db import init_db
from app.handlers_admin import router as admin_router
from app.handlers_client import router as client_router
from app.api import router as api_router
from app.reminders import reminder_loop

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

WEBHOOK_PATH = "/telegram/webhook"


async def webhook_guard_loop() -> None:
    while True:
        try:
            expected_url = f"{PUBLIC_BASE_URL.rstrip('/')}{WEBHOOK_PATH}"
            info = await bot.get_webhook_info()

            if info.url != expected_url:
                print(f"WEBHOOK MISMATCH: current={info.url!r}, expected={expected_url!r}")
                await bot.delete_webhook(drop_pending_updates=False)
                await bot.set_webhook(url=expected_url, drop_pending_updates=False)
                print(f"WEBHOOK RESTORED: {expected_url}")

        except Exception as e:
            print(f"WEBHOOK GUARD ERROR: {e!r}")

        await asyncio.sleep(300)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    dp.include_router(admin_router)
    dp.include_router(client_router)

    webhook_url = f"{PUBLIC_BASE_URL.rstrip('/')}{WEBHOOK_PATH}"

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=webhook_url, drop_pending_updates=True)

    me = await bot.get_me()
    print(f"BOT CONNECTED: @{me.username}")
    print(f"WEBHOOK SET: {webhook_url}")

    reminder_task = asyncio.create_task(reminder_loop(bot))
    webhook_guard_task = asyncio.create_task(webhook_guard_loop())

    try:
        yield
    finally:
        reminder_task.cancel()
        webhook_guard_task.cancel()

        try:
            await reminder_task
        except asyncio.CancelledError:
            pass

        try:
            await webhook_guard_task
        except asyncio.CancelledError:
            pass

        await bot.session.close()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request) -> dict:
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/")
async def miniapp() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
