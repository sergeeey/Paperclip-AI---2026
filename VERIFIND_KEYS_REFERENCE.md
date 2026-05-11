# VeriFind — учётные данные

**Этот репозиторий (Paperclip / BlindSpotSec) не должен содержать ключи или пароли проекта VeriFind.**

Учётные данные VeriFind храните:

- в каталоге проекта VeriFind (например `.env`, **в .gitignore**)
- в менеджере паролей

Интеграция Paperclip и VeriFind (если нужна) описывается на уровне архитектуры без копирования секретов между репозиториями.

## Если ранее здесь были реальные ключи

1. Считайте все упомянутые токены скомпрометированными.
2. Выполните [docs/SECURITY_ROTATION_CHECKLIST.md](docs/SECURITY_ROTATION_CHECKLIST.md) для **каждого** затронутого провайдера (включая VeriFind: DeepSeek, Gemini, БД и т.д.).

---

**Last Updated:** 2026-04-19 (sanitized)
