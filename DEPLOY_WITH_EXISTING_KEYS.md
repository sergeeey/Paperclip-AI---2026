# BlindSpotSec — быстрый деплой при уже имеющихся ключах

**Время:** порядка 45–60 минут (если VPS и ключи API уже есть).

Секреты **не** копируйте в этот файл — только в Paperclip UI и менеджер паролей.

---

## Что должно быть заранее

1. VPS с SSH-доступом (предпочтительно **по ключу**, не по паролю из документа)
2. Ключи: Anthropic, OpenAI (или Codex), Brave Search, Resend
3. Опционально: GitHub token для приватных репозиториев

---

## Шаг 1: Подключение к серверу

```bash
ssh -i ~/.ssh/your_key root@YOUR_VPS_IP
```

Замените `YOUR_VPS_IP` и путь к ключу на свои.

---

## Шаг 2: Paperclip

```bash
mkdir -p /root/paperclip && cd /root/paperclip
curl -L https://raw.githubusercontent.com/paperclipai/paperclip/main/docker-compose.yml -o docker-compose.yml
ADMIN_PASSWORD=$(openssl rand -base64 32)
echo "SAVE THIS PASSWORD IN PASSWORD MANAGER ONLY: $ADMIN_PASSWORD"
export PAPERCLIP_ADMIN_PASSWORD="$ADMIN_PASSWORD"
docker compose up -d
# подождать старт контейнеров, затем:
docker ps
```

Откройте UI: `http://YOUR_VPS_IP:3100`, войдите как `admin` с сохранённым паролем.

---

## Шаг 3: Codex / OpenAI

Включите device code authorization в настройках аккаунта (актуальная инструкция в [QUICKSTART.md](QUICKSTART.md)). В контейнере при необходимости:

```bash
docker exec -it YOUR_PAPERCLIP_CONTAINER bash
openai auth login
openai models list
exit
```

---

## Шаг 4: Компания и агенты

**Company:** BlindSpotSec, цель и бюджет — как в [QUICKSTART.md](QUICKSTART.md).

**Секреты агентов** (значения из менеджера паролей):

- Scanner: `ANTHROPIC_API_KEY`, `BRAVE_SEARCH_API` — Seal
- Reporter: `RESEND_API_KEY`, `BRAVE_SEARCH_API` (из dropdown)

---

## Шаг 5: Первая задача

Создайте задачу на демо-репозиторий (например OWASP NodeGoat), укажите **email получателя** в описании задачи. Назначьте CEO, запустите heartbeat.

---

## Документация

- [API_KEYS_REFERENCE.md](API_KEYS_REFERENCE.md) — имена переменных без значений
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — troubleshooting
- [docs/SECURITY_ROTATION_CHECKLIST.md](docs/SECURITY_ROTATION_CHECKLIST.md) — если ключи когда-либо светились в git
