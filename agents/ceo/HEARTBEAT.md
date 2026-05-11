# CEO Agent — HEARTBEAT (цикл)

Упрощённая машина состояний для одного heartbeat Paperclip:

1. **Ingest** — прочитать активные задачи и Memory Bank (`.paperclip/memory/activeContext.md`).
2. **Triage** — выбрать задачу с наивысшим приоритетом; зафиксировать критерии приёмки в комментарии задачи.
3. **Delegate Scanner** — передать скан: репозиторий, scope (OWASP / узкий), токены через Secrets.
4. **Wait / Monitor** — дождаться артефакта Scanner (JSON/логи); при Blocked — эскалация Board.
5. **Delegate Reporter** — формат отчёта, канал доставки (email), шаблон.
6. **Quality gate** — проверить: нет плейсхолдеров; CVE с пометками NIST/`[HYPOTHESIS]` согласно скиллу; структура разделов.
7. **Decide** — Done / Return to Scanner / Return to Reporter.
8. **Update memory** — при архитектурных изменениях — `decisions.md` или комментарий к задаче.

Повторять с периодом Pulse, заданным в UI Paperclip.
