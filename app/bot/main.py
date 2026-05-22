import asyncio
import os

from aiogram import Bot, Dispatcher

from app.bot.handlers import router


BOT_TOKEN = os.getenv("BOT_TOKEN")


async def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Export BOT_TOKEN before startup.")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
