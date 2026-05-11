# Active Context — BlindSpotSec

**Last Updated:** 2026-04-19
**Session:** Infrastructure Bootstrap (Day 1)

---

## Current Focus

**Primary Task:** Deploy Paperclip infrastructure and prepare for first customer scan

**Active Work Streams:**
1. Creating Skills 2.0 compliant `security-audit` skill with NIST verification
2. Setting up Memory Bank files to prevent architectural drift
3. Implementing HaluGate pipeline for anti-hallucination
4. Writing deployment runbook for VPS setup

**Blockers:** None currently (all infrastructure files being created locally)

**Next Steps:**
- [ ] Complete HaluGate hooks implementation
- [ ] Write deployment runbook with manual steps
- [ ] Provision Hostinger VPS KVM 1
- [ ] Authorize Codex via device code flow

---

## Recent Topics

### 2026-04-19: Project Inception
- Analyzed three sources:
  - Obsidian Repo Intel (practical architecture)
  - Academic review (theoretical foundations: Anokhin, Skills 2.0, HaluGate)
  - Practical deployment guide (Hostinger VPS, Codex auth, Pulse optimization)
- Decision: Implement BlindSpotSec as first Paperclip company (not VeriFind, GeoScan)
- Rationale: Security audit = highest revenue potential ($100/scan), clearest value prop
- Kill Criteria established: 14 days without real workflow → rollback to Claude Code direct

### Key Architectural Decisions Made Today
1. **NIST CVE Verification** as mandatory quality gate (prevent hallucinated CVEs)
2. **Two-layer quality control:** Scanner self-check → CEO verification
3. **Narrow Bridge model** for security-audit skill (high error cost)
4. **Memory Bank pattern** adopted from theory (prevent amnesia across Heartbeats)

---

## Data Flows

### Customer Scan Flow
```
Customer GitHub token (Board input)
  → Scanner Bot (semgrep + NIST verification)
  → JSON report (temp file /tmp/scan-TIMESTAMP-report.json)
  → Reporter Bot (markdown formatting)
  → Resend API (email delivery)
  → Customer inbox (report@customer.com)
```

### Security Boundaries
- **Customer code never persisted:** Clone to /tmp/, scan, delete after report generation
- **API keys in Secrets UI:** First agent "Seal", others select from dropdown (zero duplication)
- **AWS Bedrock option:** For EU customers requiring GDPR compliance (VPC isolation)

### Token Flow (Budget Tracking)
```
Paperclip tracks:
  - Scanner Bot: Each semgrep run + NIST API calls
  - Reporter Bot: Markdown generation
  - CEO: Delegation + quality verification

Company budget: $450/month (safety buffer)
Auto-pause when: Company budget reached (before agents max out $600 sum)
```

---

## Current Architectural State

### Technology Stack
- **Orchestrator:** Paperclip v2026.416.0 (GHSA-68qg-g8mg-6pr7 patched)
- **Hosting:** Hostinger VPS KVM 1 (not KVM 2 - cost optimization)
- **AI Models:**
  - CEO: OpenAI Codex v5.3 (good at delegation, $100/month)
  - Scanner Bot: Anthropic Claude Sonnet 4.6 (best for code analysis, $300/month)
  - Reporter Bot: OpenAI Codex v5.3 (fast markdown generation, $200/month)

### External Dependencies
- **Brave Search API:** $5/month plan, Usage Limit set to $5 (uses free credits)
- **Resend API:** Email delivery for reports
- **NIST CVE Database:** Public API (free, rate limit: 5 req/30s without key)
- **GitHub API:** Customer repo access (token provided by customer)

### Directory Structure Created
```
.paperclip/
  ├── memory/ (this file + decisions.md + progress.md)
  └── hooks/ (HaluGate pre-tool-use.sh, post-tool-use.sh)

skills/
  └── security-audit/
      ├── SKILL.md (Narrow Bridge, 350 lines, <500 limit)
      └── cve-verification-protocol.md (Level 2 reference)

agents/ (ceo/, scanner-bot/, reporter-bot/ — SOUL/HEARTBEAT/AGENTS)
docs/ (DEPLOYMENT.md, BUDGET.md, SECURITY.md, SECURITY_ROTATION_CHECKLIST.md, PRODUCT_ROADMAP.md, …)
```

---

## Known Issues & Workarounds

### Issue 1: Subscription Billing Tracking
**Status:** Known limitation (v2026.416.0)
**Impact:** Codex on ChatGPT Plus subscription reports cost_cents = 0
**Workaround:** Use API-billing for Scanner Bot (critical agent), subscription OK for Reporter Bot (less critical)
**Monitoring:** Manual token count tracking until fix released

### Issue 2: Single-Agent Overkill
**Status:** Design constraint
**Impact:** Paperclip overhead only justifies itself at 3+ agents
**Mitigation:** Starting with 3 agents (CEO, Scanner, Reporter) from Day 1
**Validation:** If we need to scale down to 1 agent → Paperclip wrong choice, revert to Claude Code

### Issue 3: Manual Hiring Approval Bottleneck
**Status:** Intentional (bootstrap phase)
**Current:** Manual approval enabled for first 3 agents
**Future:** Auto-approval after budget stabilizes (Week 3)
**Reason:** Prevent runaway hiring during learning phase

---

## Environmental Context

### Project Timeline
- **Day 1 (today):** Infrastructure files creation
- **Day 2:** VPS provisioning + Codex authorization
- **Day 3-4:** First demo scan (OWASP/NodeGoat)
- **Week 2:** First paying customer scan
- **Week 3:** 5 scans/week automated
- **Month 2:** $1K MRR target (10 customers @ $100/scan)

### Competition Awareness
- **Snyk, Veracode, Checkmarx:** Enterprise-focused, expensive ($500+/month)
- **BlindSpotSec positioning:** SMB segment, $100/scan one-time, faster turnaround (24h vs 1 week)
- **Differentiation:** AI-powered (zero human labor cost) → pass savings to customer

### Risk Factors
1. **False positive reputation risk:** Mitigated by NIST verification + two-layer quality gate
2. **API cost overrun:** Mitigated by $450 company budget hard cap
3. **Codex auth complexity:** Mitigated by detailed deployment runbook (being written)

---

## Memory Hygiene

**This file updated:**
- After each Heartbeat cycle completion
- When architectural decision made
- When blocker encountered or resolved
- When customer feedback received

**Compaction trigger:**
- When file exceeds 200 lines → archive to `.paperclip/memory/archive/activeContext-YYYY-MM-DD.md`
- Keep only last 30 days context in main file

**Related files:**
- `decisions.md` — permanent ADRs (Architecture Decision Records)
- `progress.md` — sprint goals and metrics
- Task comments in Paperclip UI — granular work notes

---

## Quick Reference

**Board Contact:** Sergey Boyko (you)
**CEO Agent Name:** TBD (will be created during VPS setup)
**Company Goal:** "Automated security audit SaaS producing OWASP Top 10 reports with NIST-backed CVE identifiers"

**Emergency Procedures:**
- Budget exceeded → auto-pause triggers, Board notification
- False positive reported by customer → update anti-patterns table in SKILL.md, re-scan
- API outage (NIST, Brave) → agents mark findings as [PENDING_VERIFICATION], complete after restore

---

**Context Status:** ✅ ACTIVE
**Next Update:** After VPS deployment (Day 2)
