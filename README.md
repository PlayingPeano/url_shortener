# URL Shortener

[![CI](https://github.com/PlayingPeano/url_shortener/actions/workflows/ci.yml/badge.svg)](https://github.com/PlayingPeano/url_shortener/actions/workflows/ci.yml)

Простой URL-shortener с REST API на FastAPI, PostgreSQL и HTML-клиентом.
Развёрнут на Yandex Cloud VM, доступ по HTTPS через Nginx и Let's Encrypt.

## Возможности

- REST API с CRUD-операциями над ссылками
- Редирект `/r/{code}` на оригинальный URL
- Простая HTML-страничка на `/`
- (Опционально) Telegram-бот для тех же операций

## Стек

- Python 3.12, FastAPI, SQLAlchemy 2.x
- PostgreSQL 16
- Docker + Docker Compose
- Nginx + Let's Encrypt (на VM)
- pytest

## Запуск локально

Требуется Docker.

```bash
cp .env.example .env
# отредактировать значения в .env
docker compose up -d --build
```

После старта:

- HTML-клиент: <http://localhost:8000/>
- Swagger UI: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

Telegram-бот не стартует по умолчанию (профиль `bot`). Чтобы запустить:

```bash
docker compose --profile bot up -d
```

## Тесты

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

Тесты используют SQLite, Postgres не требуется.

## API

| Метод  | Путь               | Описание                          |
|--------|--------------------|-----------------------------------|
| GET    | `/health`          | Health-check                      |
| GET    | `/links`           | Список последних ссылок           |
| POST   | `/links`           | Создать короткую ссылку           |
| GET    | `/links/{id}`      | Получить ссылку по ID             |
| PUT    | `/links/{id}`      | Обновить оригинальный URL         |
| DELETE | `/links/{id}`      | Удалить ссылку                    |
| GET    | `/r/{code}`        | Редирект по короткому коду        |

## Деплой

Деплой выполняется на VM в Yandex Cloud. Подробности — в `docker-compose.yml`
и Nginx-конфиге на VM (`/etc/nginx/sites-enabled/shortener-bot`).
