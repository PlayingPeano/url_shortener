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

| Метод  | Путь               | Auth        | Описание                          |
|--------|--------------------|-------------|-----------------------------------|
| GET    | `/health`          | —           | Health-check                      |
| GET    | `/metrics`         | —           | Prometheus-метрики                |
| GET    | `/links`           | —           | Список последних ссылок           |
| POST   | `/links`           | `X-API-Key` | Создать короткую ссылку           |
| GET    | `/links/{id}`      | —           | Получить ссылку по ID             |
| PUT    | `/links/{id}`      | `X-API-Key` | Обновить оригинальный URL         |
| DELETE | `/links/{id}`      | `X-API-Key` | Удалить ссылку                    |
| GET    | `/r/{code}`        | —           | Редирект по короткому коду        |

Если `API_KEY` в окружении не задан — все эндпоинты открыты (удобно для локальной разработки и тестов).
Если задан — мутирующие операции требуют заголовок `X-API-Key: <значение>`.

## Мониторинг

В `docker-compose.yml` подняты Prometheus и Grafana с предварительно настроенным
дашбордом (RPS, latency p50/p95/p99, error rate 5xx, разбивка по handler/status).

- Метрики API: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (логин/пароль из `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD`)
- Дашборд: «URL Shortener — API»

На VM Grafana и Prometheus биндятся на `127.0.0.1`, наружу их пускает только Nginx
(по подпути `/grafana/`).

## Архитектура (prod, на VM)

```
                       Интернет
                          │
                          ▼
              ┌───────────────────────┐
              │   Nginx (443, HTTPS)  │   ← Let's Encrypt
              └───────────┬───────────┘
                          │
        ┌─────────────────┼──────────────────┐
        │                 │                  │
        ▼                 ▼                  ▼
   /  /links*  /r/*   /grafana/         /webhook
        │                 │                  │
        ▼                 ▼                  ▼
  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
  │  FastAPI    │  │   Grafana    │  │ Telegram bot │
  │ (127.0.0.1: │  │ (127.0.0.1:  │  │ (127.0.0.1:  │
  │    8000)    │  │    3000)     │  │    8443)     │
  └──────┬──────┘  └──────┬───────┘  └──────────────┘
         │                │
         ▼                ▼
   ┌───────────┐   ┌──────────────┐
   │ Postgres  │   │  Prometheus  │
   │ (internal │   │ (127.0.0.1:  │
   │  network) │   │    9090)     │
   └───────────┘   └──────────────┘
```

Все backend-сервисы биндятся только на `127.0.0.1` либо вообще не пробрасываются
наружу (только внутренняя docker-сеть). Доступ извне — только через Nginx по HTTPS.

## Безопасность

- HTTPS (Let's Encrypt), редирект HTTP→HTTPS.
- API-ключ (заголовок `X-API-Key`) на все мутирующие операции.
- Прямой доступ к контейнерам API/Postgres/Grafana/Prometheus наружу закрыт.
- Секреты только в `.env` (в `.gitignore`); в GitHub Actions — через Secrets.
- Rate-limit на уровне Nginx (см. `limit_req_zone` в конфиге на VM).

## Деплой

Деплой выполняется на VM в Yandex Cloud. На каждый push в `master` GitHub Actions
гоняет тесты, собирает Docker-образ и через SSH делает `git pull && docker compose up -d --build api`
на VM. Подробности — в `.github/workflows/ci.yml`, `docker-compose.yml` и Nginx-конфиге
на VM (`/etc/nginx/sites-enabled/shortener-bot`).
