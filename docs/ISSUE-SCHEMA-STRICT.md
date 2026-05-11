# Strict Issue Schema — Evidence-Based Pipeline

**Purpose:** Every Issue must include these fields to enable artifact-driven autonomous workflow.

**Without this schema, agents cannot verify success → pipeline stalls.**

---

## Required Fields

### 1. Title
```
{PROJECT_ID}-{ISSUE_NUMBER}: {Brief Description}

Examples:
- BLI-2: Build Flask Hello World API
- TERAG-1: Implement RSS Feed Scraper
- VFN-3: Create Price Alert Notification System
```

### 2. Description (Strict Format)

```markdown
## Goal
[1-2 sentences: what this Issue creates]

## Requirements
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]

## Tech Stack
- Language: [Python 3.11+ / Node.js 20+ / etc]
- Framework: [FastAPI / Express / etc]
- Database: [PostgreSQL / SQLite / etc]
- Testing: [pytest / jest / etc]

## Output Location
Code and artifacts: `/tmp/projects/{issue_id}/`

## Acceptance Criteria
- ✅ [Criterion 1: testable condition]
- ✅ [Criterion 2: testable condition]
- ✅ [Criterion 3: testable condition]

## Required Artifacts
- test-results.json (pytest/jest output)
- coverage.xml (coverage report)
- README.md (setup instructions)

## Deployment (if applicable)
- Port: [8001 / 8002 / 8003]
- URL: http://46.224.28.128:{port}
- Service name: {app-name}

## Kill Criteria
- ❌ No artifacts after {N} hours → mark blocked
- ❌ Tests fail → fix code, not tests
- ❌ Coverage <80% → add more tests
- ❌ HIGH security findings → fix before deploy

## Execution Log

The runner writes a JSONL event log with one event per gate and a final
`issue_gates` verdict. The log is machine-validated by `verify-event-log`.

## State Sync

`sync-issue-state` writes the current structured issue artifact back to disk
after a gate run. This updates:

- `status`
- `execution.last_run_status`
- `execution.last_run_reason`
- `execution.last_event_log`

## Flow Plan

`plan-issue-flow` derives the next deterministic company stage from the strict
issue artifact. It outputs the CEO → Builder → Scanner → Reporter → DevOps
sequence with explicit `next_stage`, `next_owner`, and per-step status.
```

### 3. Assigned To
- Builder Bot (for code generation)
- Scanner Bot (for security audit)
- DevOps Bot (for deployment)

### 4. Status
- `todo` — ready to work
- `in_progress` — agent currently working
- `blocked` — waiting for dependency or human input
- `done` — artifacts verified, all gates passed

### 5. Priority (optional)
- `P0` — critical (blocks other work)
- `P1` — high (important for milestone)
- `P2` — medium (nice to have)
- `P3` — low (backlog)

### 6. Execution Hints (optional, for the runner)

```json
{
  "min_tests": 15,
  "min_coverage": 80.0,
  "semgrep_sarif": "semgrep.sarif",
  "trufflehog_json": "trufflehog.jsonl",
  "run_semgrep": false,
  "run_trufflehog": false,
  "scan_output_dir": ".paperclip-security",
  "semgrep_block_levels": ["error", "warning"],
  "block_trufflehog_unknown": true,
  "timeout_seconds": 120,
  "event_log": "events.jsonl"
}
```

---

## Example Issue: BLI-2 (Flask Hello World)

### Title
```
BLI-2: Build Flask Hello World API
```

### Description
```markdown
## Goal
Create minimal Flask API with one route returning {"message": "Hello World"}.

## Requirements
- Flask app in app.py
- One route: GET / returns {"message": "Hello World"}
- Tests with ≥80% coverage
- README with setup instructions
- requirements.txt with exact versions

## Tech Stack
- Language: Python 3.11+
- Framework: Flask 3.0+
- Testing: pytest + pytest-cov
- Linter: ruff

## Output Location
Code and artifacts: `/tmp/projects/BLI-2/`

## Acceptance Criteria
- ✅ `pytest` passes all tests (≥15 tests)
- ✅ Coverage ≥80% (verified via coverage.xml)
- ✅ `curl http://localhost:5000/` returns {"message": "Hello World"}
- ✅ `ruff check .` returns no errors
- ✅ README.md includes setup steps

## Required Artifacts
- test-results.json (pytest --json-report output)
- coverage.xml (pytest --cov-report=xml output)
- README.md (must include: install, run, test commands)

## Deployment
- Port: 8001
- URL: http://46.224.28.128:8001
- Service name: hello-world

## Kill Criteria
- ❌ No artifacts after 4 hours → mark blocked, review Builder Bot instructions
- ❌ Tests fail → fix code until green
- ❌ Coverage <80% → add tests for uncovered paths
- ❌ `curl` test fails → fix app.py
- ❌ >2 manual interventions needed → pipeline not autonomous
```

### Assigned To
`Builder Bot`

### Status
`todo`

### Priority
`P0` (proof of concept for autonomous pipeline)

---

## Example Issue: BLI-3 (CRUD API)

### Title
```
BLI-3: Build FastAPI CRUD API for Notes
```

### Description
```markdown
## Goal
Create note-taking API with CRUD operations backed by SQLite.

## Requirements
- FastAPI app with 5 endpoints
- SQLite database for persistence
- Pydantic models for validation
- Tests with ≥80% coverage
- OpenAPI docs at /docs

## Tech Stack
- Language: Python 3.11+
- Framework: FastAPI 0.100+
- Database: SQLite (via sqlite3)
- Testing: pytest + pytest-asyncio
- Validation: Pydantic v2

## Output Location
Code and artifacts: `/tmp/projects/BLI-3/`

## Acceptance Criteria
- ✅ POST /notes creates note → returns 201 + note ID
- ✅ GET /notes lists all notes → returns 200 + JSON array
- ✅ GET /notes/{id} returns single note → 200 or 404
- ✅ PUT /notes/{id} updates note → 200 or 404
- ✅ DELETE /notes/{id} deletes note → 204 or 404
- ✅ Coverage ≥80%
- ✅ OpenAPI docs accessible at /docs

## Required Artifacts
- test-results.json
- coverage.xml
- README.md (with API examples)

## Deployment
- Port: 8002
- URL: http://46.224.28.128:8002
- Service name: notes-api

## Kill Criteria
- ❌ Any endpoint returns 500 → fix before deploy
- ❌ Database persists data between restarts (test with systemctl restart)
- ❌ OpenAPI docs broken → verify /docs loads
```

---

## Validation Checklist (before creating Issue)

Before submitting Issue to agent, verify:

- [ ] Title follows format: `{PROJECT}-{N}: {Description}`
- [ ] Goal is 1-2 sentences, clear
- [ ] Requirements are specific, testable
- [ ] Tech stack specified (no "any framework")
- [ ] Output location is `/tmp/projects/{issue_id}/`
- [ ] Acceptance criteria are testable (not "code is good")
- [ ] Required artifacts listed (test-results.json, coverage.xml, README.md)
- [ ] Kill criteria defined (what makes this Issue fail)
- [ ] Assigned to specific agent (Builder/Scanner/DevOps)

**If any item missing → Issue is incomplete, agent will ask for clarification.**

---

## Anti-Patterns (DO NOT DO)

❌ **Vague Goal:** "Make the app better"
✅ **Specific Goal:** "Add pagination to GET /notes endpoint (limit=10, offset=0)"

❌ **Untestable Criterion:** "Code is clean"
✅ **Testable Criterion:** "`ruff check .` returns 0 errors"

❌ **No Artifacts:** "Just commit the code"
✅ **With Artifacts:** "Post test-results.json + coverage.xml in Issue comment"

❌ **No Kill Criteria:** Agents work forever on impossible task
✅ **With Kill Criteria:** "If >4 hours without artifacts, mark blocked"

---

## How Artifacts Enable Autonomy

**Without artifacts:**
- Agent says "done"
- Human has to manually verify
- No way to know if tests actually passed
- Pipeline stalls, waiting for human

**With artifacts:**
- Agent posts test-results.json
- Workflow Controller checks: `results["failed"] == 0`
- If true → auto-create Scanner sub-issue
- If false → keep Issue in "in_progress", agent retries
- Human only intervenes on "blocked" status

**Formula:** Artifacts = Truth, Status = Opinion

---

**Version:** 1.0.0
**Last Updated:** 2026-04-20
**Authority:** Audit Memo + Skeptic Engine v2
