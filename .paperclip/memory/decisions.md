# Architecture Decision Records (ADR)

**Project:** BlindSpotSec
**Format:** Each decision is immutable record. Superseded decisions marked with [SUPERSEDED] but not deleted.

---

## ADR-001: NIST CVE Verification as Mandatory Quality Gate

**Date:** 2026-04-19
**Status:** Active
**Context:**

Security audit reports containing hallucinated CVEs would destroy customer trust and lead to immediate churn. Academic review (line 78) warns about "structural reward hacking" where agents satisfy formal criteria without actual correctness.

Semgrep rulesets occasionally reference CVE IDs that:
- Were proposed but never formally assigned
- Contain typos (CVE-2024-1234 vs CVE-2024-12345)
- Are syntactically valid but don't exist in NIST database

**Decision:**

Every CVE mentioned in scan results MUST be verified against `https://services.nvd.nist.gov/rest/json/cves/2.0` before inclusion in customer report.

**Implementation:**
- Scanner Bot: After semgrep execution, extract all CVE IDs
- For each CVE: Query NIST API
- If `resultsPerPage == 0` → mark as `[HYPOTHESIS]`, move to report appendix
- If `resultsPerPage > 0` → mark as `[VERIFIED]`, include NIST link in main findings

**Alternatives Considered:**

1. **Trust semgrep output directly**
   - Rejected: High false positive risk (observed in practice by Paperclip Playbook author)
   - Cost: Reputational death after first hallucinated CVE

2. **Manual human verification**
   - Rejected: Defeats "zero-human company" value prop
   - Cost: Can't scale beyond 5 scans/week

3. **Use paid CVE database API (VulnDB, CVE Details)**
   - Rejected: NIST NVD is authoritative source, free, sufficient rate limits
   - Cost: Unnecessary $50/month expense

**Consequences:**

✅ **Positive:**
- Fabricated or mistyped CVE IDs are caught before they are presented as NVD-confirmed facts
- Customer trust maintained when expectations are set correctly (NIST checks IDs, not exploitability in customer code)
- Audit trail (all NIST queries logged)

⚠️ **Negative:**
- Adds 0.2s per CVE (rate limit compliance)
- NIST API downtime blocks report generation → need fallback (mark as PENDING)

**Metrics:**
- False positive rate: Target <1% (vs industry average 15-20%)
- NIST API success rate: Monitor, escalate if <95%

**Review Trigger:** After first customer complaint about CVE validity

---

## ADR-002: Narrow Bridge Model for security-audit Skill

**Date:** 2026-04-19
**Status:** Active
**Context:**

Skills 2.0 methodology (academic review lines 122-127) defines two extremes:
- **Narrow Bridge:** Step-by-step instructions for critical/fragile processes
- **Open Field:** Principles + success criteria for creative processes

Security scanning is CRITICAL process:
- Error cost = customer churn + reputation damage
- Price of error >> price of rigidity

**Decision:**

`security-audit/SKILL.md` uses Narrow Bridge approach:
- Exact bash commands for each step
- No creative freedom for Scanner Bot
- All decisions pre-made (which ruleset, which verification steps, which confidence formula)

**Implementation:**
- SKILL.md structured as numbered execution protocol
- Each step has expected output documented
- Validation cycle (Plan → Confirm → Execute) for destructive operations

**Alternatives Considered:**

1. **Open Field (let Claude choose approach)**
   - Rejected: Too much variance scan-to-scan
   - Risk: Customer A gets different methodology than Customer B → inconsistent quality

2. **Medium approach (pseudocode + principles)**
   - Rejected: Still allows interpretation → variance risk
   - Example failure mode: Claude might skip NIST check if "it looks obvious"

**Consequences:**

✅ **Positive:**
- Predictable scan quality
- Easy debugging (follow exact steps)
- Low training cost for new Scanner Bot instances

⚠️ **Negative:**
- Less flexibility (can't adapt to novel vulnerability types without SKILL.md update)
- Longer SKILL.md file (currently 350 lines, close to 500 line limit)

**Metrics:**
- Scan-to-scan consistency: Target >95% (same repo, same findings)
- SKILL.md update frequency: Track if >1/week → too rigid, need Open Field sections

**Review Trigger:** After 50 scans, evaluate if rigidity causing issues

---

## ADR-003: Two-Layer Quality Gate (Agent + CEO)

**Date:** 2026-04-19
**Status:** Active
**Context:**

Paperclip Company Playbook (production-tested) showed single biggest failure mode: **CEO as postman** (forwarding agent output unchecked).

Real production evidence:
> "CEO with quality rule written down but zero verification checks over 8 days → Founder found 15+ issues on live site"

Implementing two verification layers eliminated ~60% of rework.

**Decision:**

**Layer 1 (Scanner Bot self-check):**
- HEARTBEAT Step 5: Self-check before marking task "done"
- Checklist: JSON valid, CVEs verified, no placeholders, links clickable
- If ANY check fails → do NOT mark done, add comment, fix, re-check

**Layer 2 (CEO quality gate):**
- HEARTBEAT Step 4: CEO verifies EVERY deliverable before emailing customer
- Open report file directly, check with own "eyes" (tool calls)
- Verify against anti-patterns table
- If red flags → reject, reassign with feedback
- Only after pass → approve for Resend API delivery

**Implementation:**
- Scanner Bot AGENTS.md: "Communication protocol: Paperclip only, no direct customer contact"
- CEO SOUL.md: "Quality Control Is My Most Important Job" (explicit belief)
- Execution Policy: "Publish Report" requires CEO approval (not Board, CEO is sufficient)

**Alternatives Considered:**

1. **Single layer (Scanner only)**
   - Rejected: 60% rework rate (proven in production)
   - Risk: First customer gets broken report → churn

2. **Three layers (Scanner → Reviewer Agent → CEO)**
   - Rejected: Overhead too high for $100/scan price point
   - Cost: Extra agent = +$150/month budget

3. **Board (human) approval for every report**
   - Rejected: Defeats 24/7 automation
   - Bottleneck: Human asleep → customer waits 8 hours

**Consequences:**

✅ **Positive:**
- <1% defect rate reaching customers (vs 15% single-layer)
- CEO learns from corrections → improves over time
- Clear accountability (CEO reputation tied to approval quality)

⚠️ **Negative:**
- Adds ~2 minutes to delivery pipeline (CEO verification)
- CEO token cost increases (reads every report)

**Metrics:**
- Defects reaching customer: Target <1/100 scans
- CEO rejection rate: Track, should decrease over time as Scanner improves

**Review Trigger:** If CEO rejection rate <5% for 30 days → potentially over-engineered

---

## ADR-004: Memory Bank Pattern for Context Persistence

**Date:** 2026-04-19
**Status:** Active
**Context:**

Heartbeat pattern (academic review lines 42-52) discards session context after each cycle to prevent token burn and "lost-in-the-middle" effect.

Problem: Pure Heartbeat = amnesia. Agent forgets why decisions were made.

Solution from theory: Memory Bank = 3 markdown files updated via "Document & Clear" process before context reset.

**Decision:**

Implement Memory Bank in `.paperclip/memory/`:
1. `activeContext.md` — current focus, recent topics, data flows
2. `decisions.md` — this file (immutable ADRs)
3. `progress.md` — sprint goals, metrics, milestone tracking

**Process:**
- Pre-Heartbeat: Agent reads Memory Bank (30-50 tokens overhead)
- Post-Heartbeat: Agent updates Memory Bank with delta changes
- Context reset: Paperclip clears session, next Heartbeat loads from Memory Bank

**Implementation:**
- CEO HEARTBEAT Step 1 (Orient): Read all 3 files before any action
- CEO HEARTBEAT Step 9 (Feedback Loop): Update Memory Bank after corrections
- Compaction: activeContext.md archived when >200 lines

**Alternatives Considered:**

1. **No persistence (pure Heartbeat)**
   - Rejected: Architectural drift observed in practice
   - Example: Agent forgets why NIST verification was added, skips it

2. **EchoVault semantic memory**
   - Deferred: Month 2 optimization (need MCP integration)
   - Reason: Memory Bank simpler for MVP, EchoVault adds vector search for scale

3. **Paperclip native memory layer**
   - Not available: Roadmap feature (mid-term), not released yet

**Consequences:**

✅ **Positive:**
- Continuity across Heartbeats
- Institutional knowledge accumulates (anti-patterns table)
- New agent instances can bootstrap from Memory Bank

⚠️ **Negative:**
- 50 token overhead per Heartbeat (acceptable)
- Manual discipline required (agents must update files)

**Metrics:**
- Memory Bank staleness: Check "Last Updated" dates, flag if >7 days
- Context recovery success: After server restart, agent should remember current focus

**Review Trigger:** After first Heartbeat-induced amnesia incident

---

## ADR-005: API-Billing for Scanner Bot, Subscription OK for Reporter Bot

**Date:** 2026-04-19
**Status:** Active
**Context:**

Subscription billing tracking (academic review lines 222-230) is broken in v2026.416.0:
- ChatGPT Plus subscription → cost_cents = 0
- Budget enforcement = useless (no auto-pause)
- Risk: Infinite loop → rate limits → blocks all agents

**Decision:**

**Scanner Bot:** API-billing ONLY (Anthropic Claude Sonnet 4.6 via API)
- Reason: Critical agent, prone to loops (semgrep + NIST verification cycles)
- Budget: $300/month enforced
- Auto-pause protects against runaway

**Reporter Bot:** Subscription OK (OpenAI Codex via ChatGPT Plus)
- Reason: Non-critical, fast task (markdown generation)
- Risk: Lower (report generation = single-pass, no loops)
- Manual monitoring: Check token counts weekly

**CEO:** Subscription OK (OpenAI Codex)
- Reason: Delegation is low-cost operation
- Pulse: 600s (10 min) = ~144 wakeups/day = manageable token usage

**Implementation:**
- Scanner Bot adapterConfig: `"provider": "anthropic", "billing": "api"`
- Reporter/CEO adapterConfig: `"provider": "openai", "billing": "subscription"`
- Weekly check: Reporter + CEO token counts (manual until fix released)

**Alternatives Considered:**

1. **All agents on API billing**
   - Rejected: Increases cost ~30% ($200 → $260 for Reporter)
   - Benefit doesn't justify cost (Reporter rarely loops)

2. **All agents on subscription**
   - Rejected: Scanner Bot loops = catastrophic (no auto-pause)
   - Real risk of rate limit → customer scans blocked

3. **Custom MCP script for subscription token tracking**
   - Deferred: Month 2 (complexity not justified for MVP)

**Consequences:**

✅ **Positive:**
- Scanner Bot protected by budget enforcement
- Cost optimization (subscription cheaper where safe)

⚠️ **Negative:**
- Hybrid billing = more complex monitoring
- Manual tracking needed for subscription agents

**Metrics:**
- Scanner Bot budget: Should stay <$300/month (alert if approaching)
- Reporter/CEO tokens: Weekly check, alert if >100K tokens/day

**Review Trigger:** When Paperclip fixes subscription billing tracking (check release notes)

---

## ADR-006: Hostinger VPS KVM 1 (not KVM 2)

**Date:** 2026-04-19
**Status:** Active
**Context:**

Practical guide mentions downgrade from KVM 2 to KVM 1 as cost optimization.

Paperclip requirements (from PRODUCT.md):
- Node.js v18+ runtime
- PostgreSQL (embedded PGlite supported)
- ~2GB RAM for base deployment

KVM 1 specs (verified):
- 2 vCPU
- 4GB RAM
- 100GB SSD
- $6/month (12-month plan)

KVM 2 specs:
- 4 vCPU
- 8GB RAM
- $12/month

**Decision:**

Use KVM 1 for initial deployment.

**Rationale:**
- 4GB RAM sufficient for Paperclip + 3 agents (observed in practice)
- 100GB SSD sufficient (scans are ephemeral, deleted after reporting)
- Can upgrade to KVM 2 if performance issues observed

**Implementation:**
- Provision Hostinger VPS KVM 1
- 12-month commitment (enables discount + free domain)
- Monitor RAM usage first week, upgrade if consistently >80%

**Alternatives Considered:**

1. **KVM 2 from start**
   - Rejected: Premature optimization (no evidence need >4GB)
   - Cost: +$72/year wasted if KVM 1 sufficient

2. **AWS/GCP/DigitalOcean**
   - Rejected: More expensive ($10-15/month equivalent tier)
   - Complexity: No one-click Paperclip template

3. **Local machine (no VPS)**
   - Rejected: Breaks 24/7 requirement
   - Failure mode: Laptop closes → scans stop

**Consequences:**

✅ **Positive:**
- Lowest cost option ($72/year vs $144/year)
- 30-day money-back guarantee (risk-free test)
- Hostinger template = zero config

⚠️ **Negative:**
- If need to upgrade → migration effort
- Performance unknown until tested

**Metrics:**
- RAM usage: Monitor via `free -h`, alert if avg >3.2GB (80%)
- CPU usage: Monitor via `top`, alert if sustained >80%
- Response time: Heartbeat execution <30s (healthy)

**Review Trigger:** End of Week 1, decide upgrade if performance issues

---

## Decision Log Summary

| ADR | Title | Status | Impact |
|-----|-------|--------|--------|
| 001 | NIST CVE Verification | Active | CRITICAL (blocks nonexistent CVE IDs as facts) |
| 002 | Narrow Bridge Skill | Active | HIGH (ensures consistency) |
| 003 | Two-Layer Quality Gate | Active | CRITICAL (60% rework reduction) |
| 004 | Memory Bank Pattern | Active | MEDIUM (prevents drift) |
| 005 | Hybrid Billing Strategy | Active | MEDIUM (cost + safety balance) |
| 006 | VPS KVM 1 Selection | Active | LOW (infrastructure cost) |

---

## Decision Workflow

### When to create ADR:
- Architectural choice with long-term impact
- Tradeoff between alternatives (document why chosen)
- Security or compliance decision
- Technology selection

### When NOT to create ADR:
- Temporary workarounds (put in activeContext.md)
- Implementation details (code comments sufficient)
- Obvious choices (no alternatives considered)

### ADR Review Process:
- All active ADRs reviewed after 50 customer scans
- Superseded ADRs kept for historical context
- Metrics checked quarterly

---

**Last Updated:** 2026-04-19
**Next Review:** After first 50 scans or major incident
