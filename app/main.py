import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import BOT_TOKEN
from app.db import init_db
from app.handlers_admin import router as admin_router
from app.handlers_client import router as client_router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():
    await init_db()

    dp.include_router(admin_router)
    dp.include_router(client_router)

    try:
        me = await bot.get_me()
        print(f"BOT CONNECTED: @{me.username}")
    except Exception as e:
        print("TELEGRAM API ERROR:", repr(e))
        await bot.session.close()
        raise

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("WEBHOOK DELETED")
    except Exception as e:
        print("DELETE WEBHOOK ERROR:", repr(e))

    print("BOT STARTED")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
