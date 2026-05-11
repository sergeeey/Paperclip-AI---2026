# Credentials Template

**ВАЖНО:** скопируйте структуру в локальный `.env` в корне проекта (не коммитить). См. корневой [.env.example](.env.example).

`.env` указан в [.gitignore](.gitignore).

---

## 1. SSH (сервер Paperclip)

```bash
HOST=YOUR_VPS_IP
SSH_USER=root
SSH_PORT=22

# Предпочтительно: ключ, без пароля root в файлах
SSH_KEY_PATH=~/.ssh/paperclip_ed25519
```

**Добавление SSH-ключа:**

```bash
ssh-keygen -t ed25519 -f ~/.ssh/paperclip_ed25519 -C "paperclip-access"
ssh-copy-id -i ~/.ssh/paperclip_ed25519.pub root@YOUR_VPS_IP
```

---

## 2. API Keys (локальная разработка / скрипты)

```bash
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
BRAVE_SEARCH_API=
RESEND_API_KEY=
GITHUB_TOKEN=
```

Для production основной источник — **Paperclip UI → Secrets** (Seal).

---

## 3. Идентификаторы Paperclip (после создания в UI)

```bash
PAPERCLIP_WEB_URL=http://YOUR_VPS_IP:3100
PAPERCLIP_COMPANY_ID=
PAPERCLIP_SCANNER_AGENT_ID=
```

Подставьте значения из своей инсталляции; не публикуйте их в git.

---

## Проверка безопасности

- Секреты только в `.env` (локально) или в менеджере паролей / Paperclip Secrets.
- При утечке: [SECURITY_ROTATION_CHECKLIST.md](SECURITY_ROTATION_CHECKLIST.md).
- Локально можно прогнать [gitleaks](https://github.com/gitleaks/gitleaks): `gitleaks detect --source . --verbose`.
