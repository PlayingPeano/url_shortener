import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.methods import SendMessage
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


def _reply(message: Message, text: str) -> SendMessage:
    return SendMessage(chat_id=message.chat.id, text=text)


@router.message(Command("start"))
async def cmd_start(message: Message) -> SendMessage:
    return _reply(
        message,
        "Привет! Я бот-сокращатель.\n"
        "Команды:\n"
        "/shorten <url> - создать короткую ссылку\n"
        "/get <id> - получить ссылку по id\n"
        "/delete <id> - удалить ссылку",
    )


@router.message(Command("shorten"))
async def cmd_shorten(message: Message) -> SendMessage:
    url = _extract_single_arg(message)
    if not url:
        return _reply(message, "Использование: /shorten https://example.com")

    try:
        data = await api_client.create_link(url)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        return _reply(
            message,
            f"API вернул ошибку: {exc.response.status_code}\n{detail}",
        )
    except httpx.HTTPError:
        return _reply(
            message,
            "Не могу достучаться до API. Проверь, что FastAPI запущен.",
        )

    short_code = data["short_code"]
    link_id = data["id"]
    short_link = f"{public_base_url}/r/{short_code}"
    return _reply(message, f"Готово!\nid={link_id}\nshort={short_link}")


@router.message(Command("get"))
async def cmd_get(message: Message) -> SendMessage:
    arg = _extract_single_arg(message)
    if not arg or not arg.isdigit():
        return _reply(message, "Использование: /get <числовой id>")

    link_id = int(arg)
    try:
        data = await api_client.get_link(link_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return _reply(message, "Ссылка с таким id не найдена.")
        return _reply(message, f"API вернул ошибку: {exc.response.status_code}")
    except httpx.HTTPError:
        return _reply(
            message,
            "Не могу достучаться до API. Проверь, что FastAPI запущен.",
        )

    return _reply(
        message,
        f"id={data['id']}\n"
        f"original_url={data['original_url']}\n"
        f"short_code={data['short_code']}",
    )


@router.message(Command("delete"))
async def cmd_delete(message: Message) -> SendMessage:
    arg = _extract_single_arg(message)
    if not arg or not arg.isdigit():
        return _reply(message, "Использование: /delete <числовой id>")

    link_id = int(arg)
    try:
        await api_client.delete_link(link_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return _reply(message, "Ссылка с таким id не найдена.")
        return _reply(message, f"API вернул ошибку: {exc.response.status_code}")
    except httpx.HTTPError:
        return _reply(
            message,
            "Не могу достучаться до API. Проверь, что FastAPI запущен.",
        )

    return _reply(message, "Ссылка удалена.")
