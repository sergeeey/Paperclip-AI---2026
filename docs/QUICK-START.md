# Quick Start — доступ к Paperclip

**Цель:** подключиться к своей инсталляции Paperclip и проверить агентов.

Секреты только в локальном `.env` (см. [.env.example](.env.example)) или в менеджере паролей — не в markdown в репозитории.

---

## Шаг 1: Локальный `.env`

```bash
# Текущая конфигурация (ape-2026, Hetzner)
PAPERCLIP_HOST=46.224.28.128
PAPERCLIP_SSH_USER=root
PAPERCLIP_WEB_URL=http://46.224.28.128:3100
PAPERCLIP_COMPANY_ID=f0f6a9e5-e4e8-4de0-b1ec-1fdc646f4b9e
PAPERCLIP_SCANNER_AGENT_ID=0abcb3ed-c0ae-47ce-bc4b-ae38eb8dfac6
```

Порт и путь UI могут отличаться в зависимости от версии Paperclip и способа деплоя.

---

## Шаг 2: SSH

```bash
ssh -i ~/.ssh/your_key root@YOUR_VPS_IP
```

Предпочтительно **вход по ключу**, без хранения пароля root в файлах проекта.

---

## Шаг 3: UI и задачи

Откройте в браузере `PAPERCLIP_WEB_URL`, найдите company/issue/agent по ID из UI.

---

## Справка

- [ACCESS-REFERENCE.md](ACCESS-REFERENCE.md) — куда класть ключи (без значений)
- [CREDENTIALS-TEMPLATE.md](CREDENTIALS-TEMPLATE.md)
- [SECURITY_ROTATION_CHECKLIST.md](SECURITY_ROTATION_CHECKLIST.md)

---

**Обновлено:** 2026-04-19 (убраны реальные IP/ID из репозитория)
