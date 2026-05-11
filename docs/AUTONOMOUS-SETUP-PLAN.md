# Autonomous Development System — Setup Plan

**Goal:** 7 days from requirement to deployed product using multi-agent orchestration.

**Timeline:** Day 1-2 Builder Bot → Day 3-4 DevOps Bot → Day 5-6 Workflow → Day 6-7 TERAG MVP

---

## Architecture Overview

```
User (Issue) → Architect (plans) → Builder (codes) → Scanner (audits) → DevOps (deploys) → Done
                    ↓                   ↓                  ↓                ↓
                Planning           Code + Tests      Security Report    Production
```

**Current Status:**
- ✅ Scanner Bot configured (OWASP Top 10 scanner)
- ⏳ Builder Bot — needs creation (CRITICAL PATH)
- ⏳ DevOps Bot — needs creation
- ❌ Architect Bot — defer to Phase 2 (manual planning for MVP)

---

## Phase 1: Builder Bot Setup (Day 1-2)

### 1.1 Upload Instructions to Server

```bash
# From local machine
scp "E:\Paperclip AI - 2026\docs\agent-instructions\BUILDER.md" \
    root@46.224.28.128:/tmp/

# On server (SSH)
ssh root@46.224.28.128

# Create builder bot directory (will be created by UI, but prepare instructions)
# We'll upload after creating agent in UI
```

### 1.2 Configure Claude API in Paperclip Secrets

1. Open Paperclip UI: http://46.224.28.128:3100/BLI/dashboard
2. Navigate to **Settings** → **Secrets** (or Company settings)
3. Add secret:
   - Name: `ANTHROPIC_API_KEY`
   - Value: `<from "АПИ различные чтоб не забыть.txt" line X>`
4. Save

### 1.3 Create Builder Bot Agent

**Via Paperclip UI:**

1. Go to: http://46.224.28.128:3100/BLI/dashboard
2. Click **Agents** → **Create New Agent**
3. Fill form:
   - **Name:** `Builder Bot`
   - **Description:** `Code implementation agent - writes Python/JS/TS code with tests`
   - **Adapter Type:** `claude` (or `anthropic` depending on available adapters)
   - **Model:** `claude-sonnet-4` (best balance of speed/quality for code)
   - **Instructions Entry File:** `BUILDER.md`
   - **Adapter Config (JSON):**
     ```json
     {
       "instructionsEntryFile": "BUILDER.md",
       "apiKey": "${ANTHROPIC_API_KEY}"
     }
     ```
4. Click **Create**
5. Copy Agent ID (will look like: `a1b2c3d4-...`)

**Via PostgreSQL (if UI doesn't support claude adapter):**

```sql
ssh root@46.224.28.128
sudo -u postgres psql paperclip

INSERT INTO agents (
    id,
    name,
    company_id,
    adapter_type,
    adapter_config,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'Builder Bot',
    'f0f6a9e5-e4e8-4de0-b1ec-1fdc646f4b9e',
    'claude',  -- or 'anthropic'
    '{
        "instructionsEntryFile": "BUILDER.md",
        "model": "claude-sonnet-4",
        "apiKey": "${ANTHROPIC_API_KEY}"
    }'::jsonb,
    NOW(),
    NOW()
) RETURNING id;
```

Save the returned ID.

### 1.4 Upload BUILDER.md to Agent Directory

```bash
# Get Agent ID from previous step (example: abc123...)
AGENT_ID="<paste-agent-id-here>"
COMPANY_ID="f0f6a9e5-e4e8-4de0-b1ec-1fdc646f4b9e"

# Create instructions directory
ssh root@46.224.28.128 "mkdir -p /home/paperclip/.paperclip/instances/default/companies/${COMPANY_ID}/agents/${AGENT_ID}/instructions"

# Upload BUILDER.md
scp "E:\Paperclip AI - 2026\docs\agent-instructions\BUILDER.md" \
    root@46.224.28.128:/home/paperclip/.paperclip/instances/default/companies/${COMPANY_ID}/agents/${AGENT_ID}/instructions/

# Fix permissions
ssh root@46.224.28.128 "chown -R paperclip:paperclip /home/paperclip/.paperclip/instances/default/companies/${COMPANY_ID}/agents/${AGENT_ID}"
```

### 1.5 Test Builder Bot with Hello World

**Create Issue in Paperclip UI:**

1. Go to: http://46.224.28.128:3100/BLI/issues
2. Click **New Issue**
3. Fill form:
   - **Title:** `BLI-2: Build Flask Hello World`
   - **Description:**
     ```markdown
     Build a simple Flask app with one route returning "Hello World".

     **Requirements:**
     - Flask app in `app.py`
     - One route: `GET /` returns `{"message": "Hello World"}`
     - Tests in `test_app.py` with ≥80% coverage
     - README.md with setup instructions
     - requirements.txt with exact versions

     **Acceptance Criteria:**
     - ✅ `pytest` passes all tests
     - ✅ `curl http://localhost:5000/` returns `{"message": "Hello World"}`
     ```
   - **Assigned To:** Builder Bot
   - **Status:** `todo`
4. Click **Create**

**Expected Outcome:**
- Builder Bot picks up Issue BLI-2
- Generates: `app.py`, `test_app.py`, `requirements.txt`, `README.md`
- Runs tests, posts results in Issue comment
- Marks Issue as `done` within 2-4 hours

**Verification:**
```bash
# Check Issue status
# UI: http://46.224.28.128:3100/BLI/issues/BLI-2

# Check agent logs
ssh root@46.224.28.128
journalctl -u paperclip -n 100 --no-pager | grep -i builder
```

---

## Phase 2: DevOps Bot Setup (Day 3-4)

### 2.1 Configure Gemini API (or reuse Claude)

**Option A: Use Gemini (cheaper for bash operations):**

1. Paperclip UI → Settings → Secrets
2. Add: `GOOGLE_API_KEY` = `<from credentials file>`

**Option B: Reuse Claude API:**
- DevOps Bot can also use Claude (more expensive but better reasoning)

### 2.2 Create DevOps Bot Agent

**Via Paperclip UI:**

1. Agents → Create New Agent
2. Form:
   - **Name:** `DevOps Bot`
   - **Description:** `Deployment and infrastructure agent - systemd, nginx, firewall`
   - **Adapter Type:** `gemini_local` (or `claude`)
   - **Model:** `gemini-2.0-flash` (fast for bash) or `claude-sonnet-4`
   - **Instructions Entry File:** `DEVOPS.md`
   - **Adapter Config:**
     ```json
     {
       "instructionsEntryFile": "DEVOPS.md",
       "apiKey": "${GOOGLE_API_KEY}"
     }
     ```
3. Create → Copy Agent ID

### 2.3 Upload DEVOPS.md

```bash
DEVOPS_AGENT_ID="<paste-agent-id>"
COMPANY_ID="f0f6a9e5-e4e8-4de0-b1ec-1fdc646f4b9e"

ssh root@46.224.28.128 "mkdir -p /home/paperclip/.paperclip/instances/default/companies/${COMPANY_ID}/agents/${DEVOPS_AGENT_ID}/instructions"

scp "E:\Paperclip AI - 2026\docs\agent-instructions\DEVOPS.md" \
    root@46.224.28.128:/home/paperclip/.paperclip/instances/default/companies/${COMPANY_ID}/agents/${DEVOPS_AGENT_ID}/instructions/

ssh root@46.224.28.128 "chown -R paperclip:paperclip /home/paperclip/.paperclip/instances/default/companies/${COMPANY_ID}/agents/${DEVOPS_AGENT_ID}"
```

### 2.4 Test DevOps Bot with Hello World Deployment

**Create Issue in UI:**

- **Title:** `BLI-3: Deploy Flask Hello World to ape-2026:8001`
- **Description:**
  ```markdown
  Deploy BLI-2 Flask app to production server.

  **Requirements:**
  - Clone code from (provide repo URL or local path)
  - Deploy to `/opt/hello-world`
  - Run on port 8001
  - systemd service `hello-world.service`
  - Verify: `curl http://46.224.28.128:8001/` returns Hello World

  **Dependencies:**
  - Blocked by: BLI-2 (must be done first)

  **Acceptance Criteria:**
  - ✅ Service running: `systemctl status hello-world` → active
  - ✅ Responds: `curl http://46.224.28.128:8001/` → HTTP 200
  - ✅ Logs clean: no errors
  ```
- **Assigned To:** DevOps Bot
- **Status:** `blocked` (until BLI-2 done)
- **Blocked By:** BLI-2

**Expected Outcome:**
- After BLI-2 completes, BLI-3 auto-transitions to `todo`
- DevOps Bot deploys Flask app to ape-2026
- Service accessible at http://46.224.28.128:8001
- Deployment complete in <1 hour

---

## Phase 3: End-to-End Workflow (Day 5-6)

### 3.1 Configure Issue Dependencies

Paperclip may support Issue dependencies via:
- UI: "Blocked By" field
- Database: `issue_dependencies` table (if exists)

**Check database schema:**
```sql
ssh root@46.224.28.128
sudo -u postgres psql paperclip
\d issues
-- Look for: blocked_by, dependencies, or related fields
```

**If no dependency support:**
- Manual coordination: assign Issues to agents in sequence
- Agent checks Issue description for "Blocked by: BLI-X" and waits

### 3.2 Test Full Autonomous Cycle

**Create Issue: BLI-4 Simple CRUD API**

```markdown
**Title:** BLI-4: Build FastAPI CRUD API for Notes

**Description:**
Build a simple note-taking API with FastAPI.

**Requirements:**
- FastAPI app with SQLite database
- CRUD endpoints:
  - `POST /notes` - create note
  - `GET /notes` - list all notes
  - `GET /notes/{id}` - get one note
  - `PUT /notes/{id}` - update note
  - `DELETE /notes/{id}` - delete note
- Pydantic models for validation
- Tests with ≥80% coverage
- OpenAPI docs at `/docs`

**Workflow:**
1. Builder Bot builds API (BLI-4-build)
2. Scanner Bot audits security (BLI-4-scan)
3. DevOps Bot deploys to ape-2026:8002 (BLI-4-deploy)

**Acceptance Criteria:**
- ✅ All tests pass
- ✅ No HIGH security issues
- ✅ Deployed and accessible at http://46.224.28.128:8002/docs
```

**Create 3 Sub-Issues:**

1. **BLI-4-build** → Assigned to: Builder Bot, Status: `todo`
2. **BLI-4-scan** → Assigned to: Scanner Bot, Status: `blocked`, Blocked by: BLI-4-build
3. **BLI-4-deploy** → Assigned to: DevOps Bot, Status: `blocked`, Blocked by: BLI-4-scan

**Expected Timeline:**
- Day 5 14:00 — BLI-4-build starts
- Day 5 18:00 — BLI-4-build done, BLI-4-scan auto-starts
- Day 5 19:00 — BLI-4-scan done, BLI-4-deploy auto-starts
- Day 5 20:00 — BLI-4-deploy done, API live at :8002

**Success Criteria:**
- ✅ No human intervention required
- ✅ All 3 phases complete in <6 hours
- ✅ Working API deployed to production

---

## Phase 4: TERAG MVP (Day 6-7)

### 4.1 Create TERAG Specification

**Title:** `BLI-5: Build TERAG OSINT Scanner MVP`

**Description:**
```markdown
Build TERAG — Time-series Entity Relationship Analysis for OSINT.

**Scope (MVP):**
- Daily scraping 3 news sources (RSS feeds)
- Entity extraction: regex-based (persons, orgs, locations)
- Storage: SQLite (defer Neo4j to v2)
- CLI query tool: search by entity, date range
- Systemd timer for daily scraping

**Requirements:**
- Python 3.11+, FastAPI for API, Click for CLI
- RSS feeds: BBC News, Reuters, AP News
- Entity extraction: spaCy NER or regex patterns
- Database: SQLite with FTS5 for search
- API endpoints:
  - `GET /entities` - list all entities
  - `GET /entities/{name}/timeline` - entity mentions over time
  - `GET /search?q=<query>` - full-text search
- CLI: `terag search "keyword"`, `terag entities`, `terag scrape`
- Tests: ≥80% coverage
- systemd service + timer for daily scraping

**Workflow:**
1. BLI-5-build → Builder Bot (2 days)
2. BLI-5-scan → Scanner Bot (2 hours)
3. BLI-5-deploy → DevOps Bot (2 hours)

**Acceptance Criteria:**
- ✅ Scrapes 3 news sources daily
- ✅ Extracts entities with ≥70% precision
- ✅ API returns results in <500ms
- ✅ CLI tool works: `terag search "Russia"`
- ✅ Deployed to ape-2026:8003
- ✅ No HIGH security issues
```

**Expected Outcome:**
- Day 6 09:00 — BLI-5-build starts
- Day 7 18:00 — BLI-5-deploy done
- Day 7 20:00 — TERAG MVP live at http://46.224.28.128:8003

---

## Monitoring and Observability

### Agent Activity Dashboard

**Check agent status:**
```bash
ssh root@46.224.28.128

# All agents
sudo -u postgres psql paperclip -c "SELECT id, name, adapter_type, created_at FROM agents WHERE company_id = 'f0f6a9e5-e4e8-4de0-b1ec-1fdc646f4b9e';"

# Recent heartbeat runs
sudo -u postgres psql paperclip -c "SELECT agent_id, started_at, status FROM heartbeat_runs ORDER BY started_at DESC LIMIT 10;"

# Issues by status
sudo -u postgres psql paperclip -c "SELECT status, COUNT(*) FROM issues GROUP BY status;"
```

**Watch logs in real-time:**
```bash
ssh root@46.224.28.128
journalctl -u paperclip -f | grep -E '(Builder|DevOps|Scanner)'
```

### Issue Progress Tracking

**Via UI:**
- http://46.224.28.128:3100/BLI/dashboard
- Filter by: Agent, Status, Date

**Via Database:**
```sql
ssh root@46.224.28.128
sudo -u postgres psql paperclip

-- Active issues
SELECT id, title, status, assigned_agent_id, created_at
FROM issues
WHERE status IN ('todo', 'in_progress')
ORDER BY created_at;

-- Recent completions
SELECT id, title, status, updated_at
FROM issues
WHERE status = 'done'
ORDER BY updated_at DESC
LIMIT 5;
```

---

## Troubleshooting

### Builder Bot Not Picking Up Issues

**Check:**
1. Agent exists: `SELECT * FROM agents WHERE name = 'Builder Bot';`
2. API key configured: Check Paperclip Secrets
3. Instructions file exists: `ls /home/paperclip/.paperclip/.../BUILDER.md`
4. Issue assigned: `SELECT assigned_agent_id FROM issues WHERE id = 'BLI-2';`
5. Heartbeat running: `SELECT * FROM heartbeat_runs ORDER BY started_at DESC LIMIT 1;`

**Fix:**
- Restart Paperclip: `systemctl restart paperclip`
- Check logs: `journalctl -u paperclip -n 100 --no-pager`
- Re-assign Issue in UI

### DevOps Bot Deployment Fails

**Common Issues:**
- Port already in use: `ss -tlnp | grep 8001`
- Firewall blocking: `ufw status`, open port with `ufw allow 8001/tcp`
- Service won't start: `journalctl -u <service-name> -n 50`
- Permissions: `ls -la /opt/<app-name>`, fix with `chown -R www-data:www-data`

### Scanner Bot Shows "adapter_failed"

**Check:**
- Instructions file: `/home/paperclip/.paperclip/.../SCANNER.md` exists
- `adapter_config.instructionsEntryFile` = `"SCANNER.md"` (not AGENTS.md)
- Update if wrong:
  ```sql
  UPDATE agents
  SET adapter_config = jsonb_set(adapter_config, '{instructionsEntryFile}', '"SCANNER.md"'::jsonb)
  WHERE name = 'Scanner Bot';
  ```

---

## Success Metrics

**Phase 1 (Builder Bot):**
- ✅ Builder Bot creates working Flask app in <4 hours
- ✅ Tests pass (pytest coverage ≥80%)
- ✅ Code quality: ruff + mypy clean

**Phase 2 (DevOps Bot):**
- ✅ DevOps Bot deploys Flask app in <1 hour
- ✅ Service accessible at http://46.224.28.128:8001
- ✅ Zero-downtime restarts work

**Phase 3 (End-to-End):**
- ✅ Full cycle (build → scan → deploy) completes in <6 hours
- ✅ No human intervention required
- ✅ Issue automatically transitions through statuses

**Phase 4 (TERAG MVP):**
- ✅ TERAG deployed in 7 days from spec
- ✅ Scrapes 3 news sources daily
- ✅ API + CLI working
- ✅ No HIGH security issues

---

## Next Steps After TERAG

1. **Add Architect Bot** (optional, for complex projects)
   - Plans architecture before Builder starts
   - Creates ADRs (Architectural Decision Records)
   - Reviews Builder's code for design issues

2. **Add Verifier Bot** (adversarial fact-checker)
   - Challenges [INFERRED] claims from other agents
   - Prevents 17.2x error amplification
   - Runs after each major milestone

3. **Scale to VeriFind** (price alert aggregator)
   - Apply proven workflow
   - 7-day timeline from spec to production

4. **Scale to BlindSpotSec** (security scanner)
   - More complex: multi-agent coordination
   - Integrate with existing Scanner Bot

---

**Timeline Summary:**

| Day | Phase | Deliverable |
|-----|-------|-------------|
| 1-2 | Builder Bot Setup | Flask Hello World working |
| 3-4 | DevOps Bot Setup | Hello World deployed to :8001 |
| 5-6 | E2E Workflow | CRUD API deployed to :8002 |
| 6-7 | TERAG MVP | OSINT scanner live at :8003 |

**Total:** 7 days from zero to three working autonomous projects.

---

**Version:** 1.0.0
**Created:** 2026-04-19
**Maintained By:** Autonomous AI Lab
