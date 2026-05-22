import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.config import BOT_TOKEN
from app.db import init_db

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Бот работает. Заявки будем подключать следующим шагом.")


@dp.message()
async def any_message(message: Message):
    await message.answer("Сообщение получил.")


async def main():
    await init_db()

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