# Security — репозиторий и операции

## Версия Paperclip

Следите за advisory (пример: GHSA, упомянутый в README) и обновляйте инстанс по инструкции Paperclip.

## Секреты

- В git не коммитить: `.env`, реальные ключи, пароли SSH.
- Шаблоны: [.env.example](.env.example), [API_KEYS_REFERENCE.md](../API_KEYS_REFERENCE.md).
- После любой утечки: [SECURITY_ROTATION_CHECKLIST.md](SECURITY_ROTATION_CHECKLIST.md).
- Локальная проверка: `gitleaks detect --source . --verbose` (конфиг [.gitleaks.toml](../.gitleaks.toml)).

## Данные клиентов

- Клонировать репозитории во временный каталог; удалять после отчёта.
- Токены GitHub — минимальные scope; хранить только в Secrets.

## EU / GDPR

Для клиентов с требованием резидентности данных — отдельная политика (например изолированный inference); в этом репозитории только указатель, реализация на стороне инфраструктуры.

## HaluGate

Скрипты: [.paperclip/hooks/](../.paperclip/hooks/). Подключение к агентам Paperclip — по документации продукта (путь к pre/post hook).
