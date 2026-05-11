# Verified Assumptions — Autonomous Development System

**Date:** 2026-04-20
**Status:** PARTIAL — некоторые assumptions проверены, критические требуют проверки через UI

---

## ✅ Assumption 1: Agent Directory Structure

**Hypothesis:** Agents хранят instructions в `/home/paperclip/.paperclip/instances/default/companies/{COMPANY_ID}/agents/{AGENT_ID}/instructions/`

**Verification:**
```bash
ssh root@46.224.28.128 "ls -la /home/paperclip/.paperclip/instances/default/companies/f0f6a9e5-e4e8-4de0-b1ec-1fdc646f4b9e/agents/0abcb3ed-c0ae-47ce-bc4b-ae38eb8dfac6/"
# Result: instructions/ directory exists
```

**Result:** ✅ VERIFIED
**Evidence:** Scanner Bot (0abcb3ed-c0ae-47ce-bc4b-ae38eb8dfac6) имеет директорию `instructions/` с файлом `SCANNER.md`

**Conclusion:** BUILDER.md нужно загрузить в `{AGENT_ID}/instructions/` после создания агента

---

## ⚠️ Assumption 2: Claude Adapter Exists

**Hypothesis:** Paperclip поддерживает `adapter_type: "claude"` или `"anthropic"`

**Attempted Verification:**
```bash
# Попытка подключиться к PostgreSQL для проверки доступных adapter_types
ssh root@46.224.28.128 "psql -h localhost -p 54329 -d paperclip -c 'SELECT DISTINCT adapter_type FROM agents;'"
# Result: Password required, credentials не найдены в .env
```

**Result:** ⚠️ UNKNOWN — требует проверки через UI
**Evidence:**
- Scanner Bot использует `gemini_local` [VERIFIED из предыдущей сессии]
- PostgreSQL embedded требует password, credentials не найдены
- API endpoint `/api/companies/{id}/agents` требует authorization

**Fallback Plan:**
1. Открыть Paperclip UI: http://46.224.28.128:3100/BLI/dashboard
2. Agents → Create New Agent → проверить dropdown "Adapter Type"
3. **If "claude" or "anthropic" доступен:** использовать его (лучше для кода)
4. **If only "gemini_local" доступен:** использовать Gemini + добавить Verifier Bot сразу

**Mitigation:**
- Gemini работает для Scanner Bot → значит работает в принципе
- Builder с Gemini будет медленнее и менее точным чем с Claude
- Компенсация: добавить **Verifier Bot** (adversarial review) сразу в workflow

---

## ❌ Assumption 3: Issue Dependencies (Auto-transition)

**Hypothesis:** Paperclip автоматически переводит Issues из "blocked" в "todo" когда dependency resolves

**Attempted Verification:**
```bash
ssh root@46.224.28.128 "psql -h localhost -p 54329 -d paperclip -c '\\d issues' | grep -E '(blocked|depend)'"
# Result: Password required
```

**Result:** ❌ UNKNOWN — критический assumption не проверен

**Evidence:**
- В UI видели поле "Status" с опциями: todo, in_progress, blocked, done
- Не видели поле "Blocked By" или "Depends On"
- Paperclip может НЕ поддерживать автоматические dependencies

**Impact:** HIGH — если dependencies ручные, "автономная разработка" становится "полуавтономной"

**Fallback Plan:**
1. **Short-term (MVP):** Manual coordination
   - Assign Issues к агентам последовательно
   - После BLI-4-build done → вручную изменить BLI-4-scan status на "todo"
   - После BLI-4-scan done → вручную изменить BLI-4-deploy status на "todo"

2. **Long-term:** Build Dependency Watcher
   - Python service который мониторит Issue statuses
   - Когда Issue transitions to "done" → проверяет blocked Issues
   - Auto-updates статус blocked → todo для зависимых Issues
   - Деплоится как отдельный systemd service

**Proof of Concept (Watcher Service):**
```python
# /opt/paperclip-watcher/watcher.py
import time
import requests

PAPERCLIP_API = "http://localhost:3100/api"
COMPANY_ID = "f0f6a9e5-e4e8-4de0-b1ec-1fdc646f4b9e"

def check_dependencies():
    issues = requests.get(f"{PAPERCLIP_API}/companies/{COMPANY_ID}/issues").json()

    for issue in issues:
        if issue['status'] == 'blocked' and 'blocked_by' in issue.get('description', ''):
            # Parse "Blocked by: BLI-X" from description
            blocked_by_id = extract_blocked_by(issue['description'])

            # Check if blocking issue is done
            blocking_issue = next((i for i in issues if i['id'] == blocked_by_id), None)
            if blocking_issue and blocking_issue['status'] == 'done':
                # Unblock
                requests.patch(f"{PAPERCLIP_API}/issues/{issue['id']}",
                              json={'status': 'todo'})
                print(f"Unblocked {issue['id']}")

while True:
    check_dependencies()
    time.sleep(60)  # Check every minute
```

---

## ⚠️ Assumption 4: Git Workflow for Code Transfer

**Hypothesis:** Builder создаёт код → пушит в Git repo → DevOps клонирует оттуда

**Result:** ⚠️ UNCLEAR — не определён механизм

**Options:**

### Option A: GitHub Integration (Complex)
- Builder пушит код в GitHub repo после генерации
- Требует: GITHUB_TOKEN с write access
- Требует: Builder умеет работать с git CLI
- DevOps клонирует: `git clone https://github.com/user/project.git`

**Pros:** Standard workflow, code versioning
**Cons:** Сложная настройка, требует GitHub credentials

### Option B: Local Filesystem (Simple - RECOMMENDED для MVP)
- Builder пишет код в `/tmp/projects/{issue-id}/`
- DevOps копирует оттуда в `/opt/{app-name}/`
- Нет git, только filesystem

**Pros:** Простота, работает сразу
**Cons:** Нет версионирования, нет backup

### Option C: Manual Git Step (Hybrid)
- Builder генерирует код в Issue comment или `/tmp/`
- **Human step:** создать git repo, скопировать код, push
- DevOps клонирует из repo

**Pros:** Минимальная автоматизация, максимальный контроль
**Cons:** Не fully autonomous

**Recommendation для Phase 1:** **Option B** (local filesystem)
- Builder instructions: "Write code to `/tmp/projects/{issue_id}/`"
- DevOps instructions: "Copy code from `/tmp/projects/{issue_id}/` to `/opt/{app_name}/`"
- После Phase 1 успешен → upgrade to Option A (GitHub)

---

## ✅ Assumption 5: Paperclip Process and Storage

**Result:** ✅ VERIFIED

**Evidence:**
```bash
ps aux | grep paperclip
# papercl+ 1544843 node /usr/bin/paperclipai run
# Embedded PostgreSQL on port 54329
# User: paperclip
# Home: /home/paperclip/.paperclip/
```

**Storage Structure:**
```
/home/paperclip/.paperclip/instances/default/
├── db/                    # PostgreSQL data
├── companies/{COMPANY_ID}/
│   └── agents/{AGENT_ID}/
│       └── instructions/  # Agent instruction files
└── ...
```

---

## 📊 Summary Table

| Assumption | Status | Impact if Wrong | Mitigation |
|------------|--------|----------------|------------|
| Agent directory structure | ✅ VERIFIED | None | - |
| Claude adapter exists | ⚠️ UNKNOWN | HIGH - use Gemini instead | Check UI dropdown |
| Issue dependencies auto | ❌ UNKNOWN | HIGH - need manual coordination | Build watcher service |
| Git workflow defined | ⚠️ UNCLEAR | MEDIUM - code transfer blocks | Use local filesystem (Option B) |
| Paperclip storage | ✅ VERIFIED | None | - |

---

## 🎯 Next Actions (Priority Order)

### 1. CHECK (5 минут)
Open Paperclip UI: http://46.224.28.128:3100/BLI/dashboard

**Agents → Create New Agent → Check dropdown:**
- [ ] Claude adapter available? (best)
- [ ] Anthropic adapter available? (good)
- [ ] Only gemini_local? (fallback)

**Issues → Check any existing Issue:**
- [ ] "Blocked By" field exists? (dependency support)
- [ ] Only "Status" field? (manual coordination needed)

### 2. DECIDE (2 минуты)
Based on UI check:

**If Claude available:**
- ✅ Use Claude Sonnet-4 for Builder
- ✅ Follow AUTONOMOUS-SETUP-PLAN.md as written

**If only Gemini:**
- ⚠️ Use Gemini for Builder (lower quality)
- ✅ Add Verifier Bot to workflow IMMEDIATELY
- ⚠️ Adjust timeline: +50% time (Gemini slower)

### 3. CREATE (15 минут)
Create Builder Bot через UI с найденным adapter type

### 4. UPLOAD (5 минут)
```bash
AGENT_ID="<from-step-3>"
scp "E:\Paperclip AI - 2026\docs\agent-instructions\BUILDER.md" \
    root@46.224.28.128:/home/paperclip/.paperclip/instances/default/companies/f0f6a9e5-e4e8-4de0-b1ec-1fdc646f4b9e/agents/${AGENT_ID}/instructions/

ssh root@46.224.28.128 "chown -R paperclip:paperclip /home/paperclip/.paperclip/instances/default/companies/f0f6a9e5-e4e8-4de0-b1ec-1fdc646f4b9e/agents/${AGENT_ID}"
```

### 5. TEST (create BLI-2: Flask Hello World)

---

## 🔄 Continuous Verification

После каждого agent deployment:
- [ ] Check agent logs: `ssh root@46.224.28.128 "cat /tmp/paperclip.log | grep -i builder"`
- [ ] Verify Issue picked up: UI → Issues → check status transition
- [ ] Monitor for errors: Look for "adapter_failed" in logs

---

**Conclusion:**
- 2/5 assumptions verified
- 3/5 require UI check (5 минут работы)
- Critical path: открыть UI → проверить adapter dropdown → создать Builder Bot
- Fallback готов для всех failure сценариев

**Confidence:** 0.70 (pragmatic - знаем что работает, готовы адаптироваться к тому что найдём в UI)
