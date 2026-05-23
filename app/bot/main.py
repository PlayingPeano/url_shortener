import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.bot.handlers import router


BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_MODE = os.getenv("BOT_MODE", "polling").strip().lower()
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "").rstrip("/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8443"))


def _normalized_webhook_path(path: str) -> str:
    if not path:
        return "/webhook"
    return path if path.startswith("/") else f"/{path}"


async def _run_polling(bot: Bot, dp: Dispatcher):
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)


async def _run_webhook(bot: Bot, dp: Dispatcher):
    if not WEBHOOK_BASE_URL:
        raise RuntimeError("WEBHOOK_BASE_URL is required when BOT_MODE=webhook.")

    webhook_path = _normalized_webhook_path(WEBHOOK_PATH)
    webhook_url = f"{WEBHOOK_BASE_URL}{webhook_path}"

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=WEBHOOK_HOST, port=WEBHOOK_PORT)
    await site.start()

    await bot.set_webhook(url=webhook_url, drop_pending_updates=False)

    try:
        await asyncio.Event().wait()
    finally:
        await bot.delete_webhook(drop_pending_updates=False)
        await runner.cleanup()


async def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Export BOT_TOKEN before startup.")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    if BOT_MODE == "webhook":
        await _run_webhook(bot, dp)
        return
    if BOT_MODE == "polling":
        await _run_polling(bot, dp)
        return

    raise RuntimeError("BOT_MODE must be 'polling' or 'webhook'.")


if __name__ == "__main__":
    asyncio.run(run_bot())
