# API Keys Reference — BlindSpotSec Paperclip

**Безопасность:** в этом файле только **имена** переменных и **куда** их вводить. Секретные значения не хранятся в git.

**Где хранить значения:** менеджер паролей и секреты Paperclip (UI → Agents → Secrets).

---

## Переменные для Paperclip

| Секрет (имя в UI) | Назначение |
|-------------------|------------|
| `ANTHROPIC_API_KEY` | Scanner Bot (Claude) |
| `OPENAI_API_KEY` или auth Codex | CEO / Reporter (по выбранному адаптеру) |
| `BRAVE_SEARCH_API` | Обогащение CVE / поиск |
| `RESEND_API_KEY` | Отправка отчётов по email |
| `GITHUB_TOKEN` | Опционально: приватные репозитории клиента |

Форматы (для проверки при вставке из менеджера паролей):

- Anthropic: `sk-ant-...`
- OpenAI: `sk-proj-...` или `sk-...`
- Brave: `BSA...`
- Resend: `re_...`
- GitHub: `ghp_...` или fine-grained token

---

## VPS / SSH

- **Не храните** пароль root в репозитории.
- Рекомендуется: вход по **SSH-ключу**, `PasswordAuthentication no` после настройки ключа.
- IP и hostname — только в личных заметках или инфраструктурном vault, не в публичном git.

---

## После любой утечки

См. [docs/SECURITY_ROTATION_CHECKLIST.md](docs/SECURITY_ROTATION_CHECKLIST.md).

---

**Last Updated:** 2026-04-19 (sanitized; no secrets in repo)
