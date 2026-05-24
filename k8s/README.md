# Kubernetes deployment

Манифесты для деплоя URL-shortener в Yandex Managed K8s.

## Что описано

- **`namespace.yaml`** — отдельный namespace `url-shortener`.
- **`configmap.yaml`** — несекретные env-переменные (имя пользователя БД, имя базы).
- **`secret.example.yaml`** — шаблон Secret (пароль БД, API-ключ). Реальные значения
  кладёшь в `secret.local.yaml` (он в `.gitignore`).
- **`postgres.yaml`** — Postgres 16 как StatefulSet с PVC (5 GiB на Yandex Network SSD).
- **`api.yaml`** — Deployment FastAPI (2 реплики) + ClusterIP-Service на порту 8000.
- **`kustomization.yaml`** — описывает порядок применения через `kubectl apply -k .`.

Образ API хранится в Yandex Container Registry: `cr.yandex/<REGISTRY_ID>/url-shortener:<tag>`.
В этих манифестах `REGISTRY_ID` — плейсхолдер, его нужно подставить (см. ниже).

## Первый деплой — пошагово

Все шаги выполняются с локальной машины, где уже:
- настроен `yc` (`yc init`)
- получен kubeconfig (`yc managed-kubernetes cluster get-credentials --name url-shortener-k8s --external --force`)
- `docker login` сделан для `cr.yandex` (`yc container registry configure-docker`)

### 1. Узнать ID реестра

```bash
cd ../infra/k8s-cluster
REGISTRY_ID=$(terraform output -raw registry_id)
echo $REGISTRY_ID
cd -
```

### 2. Собрать и запушить образ

```bash
cd ..   # корень репозитория url-shortener
TAG=$(git rev-parse --short HEAD)
IMAGE="cr.yandex/${REGISTRY_ID}/url-shortener:${TAG}"

docker build -t "${IMAGE}" -t "cr.yandex/${REGISTRY_ID}/url-shortener:latest" .
docker push "${IMAGE}"
docker push "cr.yandex/${REGISTRY_ID}/url-shortener:latest"
```

### 3. Подготовить секрет

```bash
cd k8s
cp secret.example.yaml secret.local.yaml
# Открой secret.local.yaml и впиши реальные значения:
#   POSTGRES_PASSWORD — сложный пароль (например, openssl rand -base64 24)
#   API_KEY            — например, openssl rand -hex 16
nano secret.local.yaml
```

### 4. Подставить REGISTRY_ID в api.yaml

```bash
sed -i "s|REGISTRY_ID|${REGISTRY_ID}|g" api.yaml
# (Можно потом вернуть обратно: git checkout api.yaml — главное успеть применить.)
```

Альтернатива — использовать `kubectl set image deployment/api ...` после первого apply.

### 5. Применить манифесты

```bash
kubectl apply -k .                # namespace + configmap + postgres + api
kubectl apply -f secret.local.yaml
```

### 6. Проверить, что всё поднялось

```bash
kubectl -n url-shortener get pods
kubectl -n url-shortener get pvc
kubectl -n url-shortener get svc
```

Ожидаем:
- `postgres-0` — Running, Ready 1/1
- `api-...` — 2 пода, Running, Ready 1/1
- PVC `data-postgres-0` — Bound (5Gi)
- Service `postgres` (Headless, без ClusterIP) и `api` (ClusterIP на 8000)

### 7. Локально проверить API

```bash
kubectl -n url-shortener port-forward svc/api 8000:8000
# в другом терминале:
curl http://localhost:8000/health
curl http://localhost:8000/links
```

Должны вернуться `{"status":"ok"}` и `[]`.

## Обновление API после изменений в коде

```bash
# собрать новый образ с новым тегом
TAG=$(git rev-parse --short HEAD)
IMAGE="cr.yandex/${REGISTRY_ID}/url-shortener:${TAG}"
docker build -t "${IMAGE}" .
docker push "${IMAGE}"

# перенаправить deployment на новый образ
kubectl -n url-shortener set image deployment/api api="${IMAGE}"
kubectl -n url-shortener rollout status deployment/api
```

## Публичный HTTPS-домен через Ingress + cert-manager

После того как поды в кластере поднялись и проверены через `port-forward`, можно
открыть API в интернете на отдельном поддомене (например, `myshortbot-k8s.duckdns.org`)
с настоящим Let's Encrypt-сертификатом.

### 1. Поставить ingress-nginx

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.3/deploy/static/provider/cloud/deploy.yaml
kubectl -n ingress-nginx rollout status deploy/ingress-nginx-controller
```

Это создаст `Service` типа `LoadBalancer`. Yandex Managed K8s автоматически
поднимет Yandex Network Load Balancer и выдаст внешний IP.

### 2. Узнать внешний IP

```bash
kubectl -n ingress-nginx get svc ingress-nginx-controller -w
# жди, пока EXTERNAL-IP перестанет быть <pending> (обычно 1–2 минуты)
```

Зафиксируй IP в переменной:

```bash
LB_IP=$(kubectl -n ingress-nginx get svc ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo $LB_IP
```

### 3. Завести DuckDNS-имя на этот IP

DuckDNS не умеет ставить разные IP на сабдомены одного имени, поэтому регистрируем
**отдельное** имя (а не `k8s.myshortbot.duckdns.org`):

1. Открой <https://www.duckdns.org/domains> (там, где регистрировал основной домен).
2. В поле «add domain» впиши, например, `myshortbot-k8s` → Add domain.
3. Сразу под ним в строке `myshortbot-k8s` впиши `current ip = ${LB_IP}` → update ip.

Проверь:

```bash
dig +short myshortbot-k8s.duckdns.org
# должно вернуть тот же IP, что в $LB_IP
```

### 4. Поставить cert-manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.yaml
kubectl -n cert-manager rollout status deploy/cert-manager
kubectl -n cert-manager rollout status deploy/cert-manager-webhook
kubectl -n cert-manager rollout status deploy/cert-manager-cainjector
```

### 5. Применить ClusterIssuer (Let's Encrypt)

Вставь свой email в `cluster-issuer.yaml` (LE использует его для предупреждений
об истечении сертификата):

```bash
sed -i "s|CHANGE_ME_EMAIL|you@example.com|" cluster-issuer.yaml
kubectl apply -f cluster-issuer.yaml
kubectl get clusterissuer letsencrypt-prod
# STATUS должен стать Ready=True через ~10 секунд
```

### 6. Применить Ingress

Подставь домен и примени:

```bash
DOMAIN=myshortbot-k8s.duckdns.org
sed -i "s|CHANGE_ME_DOMAIN|${DOMAIN}|g" ingress.yaml
kubectl apply -f ingress.yaml
```

Подожди, пока cert-manager выпустит сертификат (1–3 минуты — он сделает
HTTP-01 challenge через тот же Ingress):

```bash
kubectl -n url-shortener get certificate
# READY должен стать True
kubectl -n url-shortener describe certificate api-tls | tail -30
```

### 7. Проверка

```bash
curl -si https://myshortbot-k8s.duckdns.org/health
curl -si https://myshortbot-k8s.duckdns.org/links

# создать ссылку
API_KEY=<твой_api_key_из_secret.local.yaml>
curl -s -X POST https://myshortbot-k8s.duckdns.org/links \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{"original_url":"https://example.com"}'
```

Открой в браузере <https://myshortbot-k8s.duckdns.org/> — должна загрузиться
HTML-страница, замок в адресной строке должен показывать валидный сертификат
от Let's Encrypt.

## CI/CD: автодеплой в K8s

После первого ручного применения манифестов дальше образ собирается и
выкатывается автоматически на каждый push в `master`.

Сборка живёт в `.github/workflows/ci.yml`, jobs `push-image` и `deploy-k8s`:

1. `push-image`: после `tests` собирает Docker-образ через Buildx,
   логинится в `cr.yandex` под service account'ом `ci-pusher` (роль
   `container-registry.images.pusher`) и пушит два тэга — `<sha7>` и `latest`.
2. `deploy-k8s`: после `push-image` берёт kubeconfig через
   `yc managed-kubernetes cluster get-credentials --external --force`,
   выполняет `kubectl set image deployment/api api=<новый_образ>` и
   `kubectl rollout status` (таймаут 180 c). У того же SA есть роль
   `k8s.cluster-api.editor` — этого хватает для rollout.

### Что нужно один раз настроить

После `terraform apply` в `infra/k8s-cluster/` (где уже описан `ci_pusher` SA):

```bash
cd infra/k8s-cluster
terraform output ci_pusher_create_key_command
# выведет команду вида: yc iam key create --service-account-id ajeXXXX --output sa-key.json

# создать ключ
$(terraform output -raw ci_pusher_create_key_command)
```

В корне репо на GitHub (Settings → Secrets and variables → Actions → New repository secret)
добавь 4 секрета:

| Имя секрета         | Что внутри                                                                   |
|---------------------|------------------------------------------------------------------------------|
| `YC_SA_JSON_KEY`    | Полное содержимое `sa-key.json` (целиком многострочный JSON)                 |
| `YC_FOLDER_ID`      | `terraform output -raw folder_id` (или `yc config get folder-id`)            |
| `YC_REGISTRY_ID`    | `terraform output -raw registry_id`                                          |
| `YC_K8S_CLUSTER_ID` | `terraform output -raw cluster_id`                                           |

После того как ключ окажется в GitHub Secret, **удалить** локальный файл:

```bash
shred -u sa-key.json
```

### Как проверить

Любой коммит в `master` запустит весь pipeline. После успешного
прохождения `deploy-k8s` в кластере появится новый под с новым образом:

```bash
kubectl -n url-shortener get pods -l app=api -w
kubectl -n url-shortener describe deployment api | grep Image:
```

## Очистка (только если решил снести)

```bash
kubectl delete -k .              # удаляет namespace + всё внутри
# Том БД останется. Чтобы и его удалить:
kubectl -n url-shortener delete pvc data-postgres-0
```
