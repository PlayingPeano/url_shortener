import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import httpx

from app.bot.client import ApiClient


router = Router()
api_client = ApiClient()
public_base_url = os.getenv("PUBLIC_BASE_URL", api_client.base_url).rstrip("/")


def _extract_single_arg(message: Message) -> str | None:
    if not message.text:
        return None
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return None
    return parts[1].strip()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот-сокращатель.\n"
        "Команды:\n"
        "/shorten <url> - создать короткую ссылку\n"
        "/get <id> - получить ссылку по id\n"
        "/delete <id> - удалить ссылку"
    )


@router.message(Command("shorten"))
async def cmd_shorten(message: Message):
    url = _extract_single_arg(message)
    if not url:
        await message.answer("Использование: /shorten https://example.com")
        return

    try:
        data = await api_client.create_link(url)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        await message.answer(f"API вернул ошибку: {exc.response.status_code}\n{detail}")
        return
    except httpx.HTTPError:
        await message.answer("Не могу достучаться до API. Проверь, что FastAPI запущен.")
        return

    short_code = data["short_code"]
    link_id = data["id"]
    short_link = f"{public_base_url}/r/{short_code}"
    await message.answer(f"Готово!\nid={link_id}\nshort={short_link}")


@router.message(Command("get"))
async def cmd_get(message: Message):
    arg = _extract_single_arg(message)
    if not arg or not arg.isdigit():
        await message.answer("Использование: /get <числовой id>")
        return

    link_id = int(arg)
    try:
        data = await api_client.get_link(link_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            await message.answer("Ссылка с таким id не найдена.")
            return
        await message.answer(f"API вернул ошибку: {exc.response.status_code}")
        return
    except httpx.HTTPError:
        await message.answer("Не могу достучаться до API. Проверь, что FastAPI запущен.")
        return

    await message.answer(
        f"id={data['id']}\n"
        f"original_url={data['original_url']}\n"
        f"short_code={data['short_code']}"
    )


@router.message(Command("delete"))
async def cmd_delete(message: Message):
    arg = _extract_single_arg(message)
    if not arg or not arg.isdigit():
        await message.answer("Использование: /delete <числовой id>")
        return

    link_id = int(arg)
    try:
        await api_client.delete_link(link_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            await message.answer("Ссылка с таким id не найдена.")
            return
        await message.answer(f"API вернул ошибку: {exc.response.status_code}")
        return
    except httpx.HTTPError:
        await message.answer("Не могу достучаться до API. Проверь, что FastAPI запущен.")
        return

    await message.answer("Ссылка удалена.")
