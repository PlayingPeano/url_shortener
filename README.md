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

## Infrastructure as Code (Terraform)

Каталог `infra/terraform/` содержит Terraform-модуль, описывающий всю инфраструктуру:
VPC-сеть, подсеть, security group (открыто только 22/80/443) и саму VM с
cloud-init, который ставит Docker, Nginx, certbot и UFW.

### Что нужно один раз

1. Установить Terraform >= 1.5: <https://developer.hashicorp.com/terraform/downloads>
2. Получить OAuth-токен Yandex Cloud:
   <https://oauth.yandex.ru/authorize?response_type=token&client_id=1a6990aa636648e9b2ef855fa7bec2fb>
3. Экспортировать токен в окружение:

   ```bash
   export YC_TOKEN=<полученный_токен>
   ```

4. Скопировать `terraform.tfvars.example` → `terraform.tfvars` и вписать свой
   `ssh_public_key` (содержимое `~/.ssh/your_key.pub` одной строкой).

### Команды

```bash
cd infra/terraform
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan
# При желании поднять реальную VM (создаст новые ресурсы):
# terraform apply
```

`terraform plan` показывает, что будет создано, ничего не меняя. CI на каждый
push выполняет `terraform fmt -check`, `init -backend=false` и `validate`,
поэтому код всегда «валидируется».

После `terraform apply` нужно вручную: указать новый IP в DNS (DuckDNS),
склонировать репозиторий на VM, заполнить `.env`, выпустить сертификат
`certbot --nginx -d <домен>`, прописать `location` в Nginx — и `docker compose up -d`.

## Kubernetes (Yandex Managed K8s)

Параллельно с docker-compose-деплоем приложение поднимается в Managed K8s-кластере
Yandex Cloud (создаётся через `infra/k8s-cluster/`). Образ хранится в Yandex
Container Registry; ноды K8s достают его без отдельного `imagePullSecret`,
потому что у service account нод дана роль `container-registry.images.puller`.

Манифесты лежат в `k8s/`:

- `namespace.yaml` — namespace `url-shortener`
- `configmap.yaml` — несекретные параметры (имена БД/пользователя)
- `secret.example.yaml` — шаблон Secret (реальные значения в `secret.local.yaml`, он в `.gitignore`)
- `postgres.yaml` — Postgres 16 как StatefulSet + headless Service + PVC на 5 GiB (Yandex Network SSD)
- `api.yaml` — Deployment FastAPI (2 реплики, RollingUpdate, readiness/liveness `/health`) + ClusterIP Service
- `kustomization.yaml` — `kubectl apply -k .` за один заход
- `ingress.yaml` — Ingress (`ingress-nginx`) с TLS через cert-manager
- `cluster-issuer.yaml` — Let's Encrypt ClusterIssuer (HTTP-01 challenge)

Публичная точка входа в K8s-стек — отдельный поддомен `myshortbot-k8s.duckdns.org`,
указывающий на IP Yandex Network Load Balancer'a, который автоматически создаётся
сервисом `ingress-nginx-controller` (типа `LoadBalancer`). Старый docker-compose
стек продолжает работать на `myshortbot.duckdns.org` параллельно.

Пошаговая инструкция по сборке и деплою — в `k8s/README.md`.

## Деплой

Деплой выполняется на VM в Yandex Cloud. На каждый push в `master` GitHub Actions
гоняет тесты, собирает Docker-образ и через SSH делает `git pull && docker compose up -d --build api`
на VM. Подробности — в `.github/workflows/ci.yml`, `docker-compose.yml` и Nginx-конфиге
на VM (`/etc/nginx/sites-enabled/shortener-bot`).
