# BlindSpotSec — готовность к деплою

**Статус:** используйте этот чеклист после того, как все ключи созданы и хранятся вне git.

**Время до первого скана:** зависит от VPS и авторизации Codex (~45–90 мин).

---

## Pre-Deployment Checklist

### API Keys

- [ ] **Anthropic** — Scanner Bot
- [ ] **OpenAI** — CEO + Reporter (или подписка Codex по инструкции Paperclip)
- [ ] **Brave Search** — лимит расхода в дашборде выставлен (например $5/мес)
- [ ] **Resend** — ключ создан, домен/отправитель проверены

### Сервер

- [ ] VPS доступен по SSH **по ключу** (пароль root не документируется в репозитории)
- [ ] Paperclip развёрнут; UI открывается на `http://YOUR_VPS_IP:3100` (или HTTPS, если настроено)

---

## Краткие шаги

1. SSH на сервер: `ssh -i ~/.ssh/your_key root@YOUR_VPS_IP`
2. Развернуть Paperclip (см. [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md))
3. Включить device code auth для Codex в настройках OpenAI/ChatGPT — по актуальной документации
4. В контейнере Paperclip: `openai auth login` при необходимости
5. Создать компанию BlindSpotSec, нанять CEO → Scanner → Reporter
6. Секреты ввести **только** в Paperclip UI (Seal / dropdown), не в markdown

Подробная пошаговая инструкция: [QUICKSTART.md](QUICKSTART.md), [DEPLOY_WITH_EXISTING_KEYS.md](DEPLOY_WITH_EXISTING_KEYS.md).

---

## Успех

- [ ] Три агента наняты, задача NodeGoat (или демо-репо) завершена
- [ ] Отчёт получен по email
- [ ] В отчёте нет плейсхолдеров `TODO` / `TBD`

---

**Важно:** любые реальные IP, пароли и ключи — только в менеджере паролей. См. [docs/SECURITY_ROTATION_CHECKLIST.md](docs/SECURITY_ROTATION_CHECKLIST.md).
