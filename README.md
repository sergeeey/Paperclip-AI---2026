# BlindSpotSec — Paperclip AI Company

> Automated security audit SaaS powered by Paperclip multi-agent orchestration

## Project Status

**Phase:** Infrastructure Setup (Day 1)
**Target:** First customer scan within 14 days
**Kill Criteria:** If no real workflow after 14 days → rollback to Claude Code direct usage

## What This Is

BlindSpotSec is a zero-human security audit company running on Paperclip. The system:
- Scans customer repositories for OWASP Top 10 vulnerabilities
- Verifies **CVE identifiers** against the NIST NVD API so nonexistent IDs are not sold as facts (does not remove all scanner false positives; see Key Features)
- Generates professional security reports
- Delivers reports via email automatically
- Operates 24/7 without human intervention

## Architecture

```
Board (You)
  │
  └─ CEO Agent (Claude Code / Codex)
      ├─ Scanner Bot → OWASP scanning + NIST verification
      ├─ Reporter Bot → Report generation + email delivery
      └─ (Future) PQC Auditor, GDPR Compliance Bot
```

## Directory Structure

```
.paperclip/
  ├── memory/              # Memory Bank (prevents architectural drift)
  │   ├── activeContext.md # Current focus + recent changes
  │   ├── decisions.md     # Architecture Decision Records (ADR)
  │   └── progress.md      # Sprint goals + metrics
  │
  └── hooks/               # HaluGate pipeline (anti-hallucination)
      ├── pre-tool-use.sh  # Block hallucinated paths/endpoints
      └── post-tool-use.sh # Verify tool execution results

skills/
  └── security-audit/      # Skills 2.0 compliant
      ├── SKILL.md                      # Main operational directives
      └── cve-verification-protocol.md  # Level 2 reference (NIST protocol)

agents/
  ├── ceo/
  │   ├── SOUL.md          # CEO identity + quality control mandate
  │   ├── HEARTBEAT.md     # 12-step state machine
  │   └── AGENTS.md        # Worker delegation rules
  │
  ├── scanner-bot/
  │   ├── AGENTS.md        # Scanner role definition
  │   └── HEARTBEAT.md     # Self-check protocol (Step 5)
  │
  └── reporter-bot/
      ├── AGENTS.md        # Reporter role definition
      └── HEARTBEAT.md     # Format verification protocol

docs/
  ├── DEPLOYMENT.md                  # VPS setup runbook
  ├── BUDGET.md                      # Cost tracking + burn notes
  ├── SECURITY.md                    # Repo + ops security
  ├── SECURITY_ROTATION_CHECKLIST.md # After any secret exposure
  ├── PRODUCT_ROADMAP.md             # Metrics, SARIF, B2B legal outline
  ├── CREDENTIALS-TEMPLATE.md        # Local .env shape (no values)
  ├── ACCESS-REFERENCE.md            # Where secrets live (no values)
  └── QUICK-START.md                 # Reconnecting to your instance
```

## Budget

| Item | Monthly Cost |
|------|-------------|
| **Company Budget** | $450 (safety buffer) |
| CEO Agent | $100 |
| Scanner Bot | $300 |
| Reporter Bot | $200 |
| **Sum (agents)** | $600 |
| **Safety Buffer** | $150 (company stops at $450 before agents max out) |

## Technology Stack

- **Orchestrator:** Paperclip v2026.416.0+
- **Hosting:** Hostinger VPS KVM 1 (24/7 uptime)
- **AI Models:**
  - OpenAI Codex v5.3 (CEO, Reporter)
  - Anthropic Claude Sonnet 4.6 (Scanner)
- **External APIs:**
  - Brave Search API ($5/month plan)
  - Resend API (email delivery)
  - NIST CVE Database (free, verification)

## Security

- ✅ GHSA-68qg-g8mg-6pr7 patched (v2026.416.0)
- ✅ API keys and SSH credentials must live in a password manager / Paperclip Secrets only — see [docs/SECURITY_ROTATION_CHECKLIST.md](docs/SECURITY_ROTATION_CHECKLIST.md) if they ever touched git
- ✅ Customer code isolation (AWS Bedrock for EU clients)
- ✅ Execution Policy: "Publish Report" requires human approval
- ✅ HaluGate hooks (`.paperclip/hooks/`): block unsafe/hallucinated shell patterns; wire them in Paperclip per upstream docs

## Key Features

### 1. NIST CVE Verification (fabricated CVE IDs)
Every **CVE ID** cited from tool output is checked against `https://services.nvd.nist.gov/rest/json/cves/2.0` before being presented as a confirmed database entry. IDs that do not resolve are labeled `[HYPOTHESIS]` (or similar). This does **not** guarantee that a finding is exploitable in the customer’s code—only that the identifier is not invented. Semantic false positives from rules or LLM interpretation still require Scanner self-check + CEO gate.

### 2. Two-Layer Quality Gate
- **Layer 1:** Scanner Bot self-check (HEARTBEAT Step 5)
- **Layer 2:** CEO verification before email delivery

### 3. Memory Bank Pattern
Prevents "amnesia" across Heartbeat cycles:
- `activeContext.md` — what we're doing now
- `decisions.md` — why we chose this architecture
- `progress.md` — where we are vs sprint goals

### 4. Acceptor Results Action (Anokhin's Theory)
Before executing any scan, Scanner Bot formalizes success criteria:
- "Successful result = JSON report with 5 sections"
- "Each CVE has NIST link + confidence score ≥0.85"
- "No placeholders (TODO, TBD)"

## Next Steps

### Manual Steps Required (You)

1. **VPS Setup** (30 min)
   - Register Hostinger KVM 1 (12 months for discount)
   - Deploy Paperclip template
   - Save admin password

2. **Codex Authorization** (15 min)
   - chatgpt.com → Settings → Enable device code auth
   - `docker exec -it [CONTAINER_ID] bash`
   - `openai auth login`
   - Paste URL + code in browser

3. **API Keys** (20 min)
   - Get Brave Search API key ($5 plan)
   - Get Resend API key
   - Configure in Paperclip Secrets UI

4. **Company Creation** (10 min)
   - Name: BlindSpotSec
   - Goal: "Automated security audit SaaS producing OWASP Top 10 reports"
   - Hire CEO (Codex v5.3, Pulse 600s, Budget $100)

5. **First Task** (5 min)
   - Create: "Tools Test: scan OWASP/NodeGoat and email report"
   - Assign to CEO
   - Trigger heartbeat

**Total time to first scan:** ~90 minutes

## Success Metrics

| Milestone | Target | Status |
|-----------|--------|--------|
| Infrastructure deployed | Day 1 | 🟡 In Progress |
| First demo scan (NodeGoat) | Day 2 | ⬜ Pending |
| First customer scan | Week 2 | ⬜ Pending |
| 5 scans/week automated | Week 3 | ⬜ Pending |
| $1K MRR (10 customers) | Month 2 | ⬜ Pending |

## Resources

- [docs/PRODUCT_ROADMAP.md](docs/PRODUCT_ROADMAP.md) — метрики, SARIF, B2B
- [Paperclip Documentation](https://paperclipai-paperclip.mintlify.app/)
- [Obsidian: Repo Intel — Paperclip](C:\Users\serge\.claude\memory\knowledge\research\repo-intel\Repo Intel — Paperclip.md)
- [Obsidian: BlindSpotSec Plan](C:\Users\serge\.claude\memory\projects\blindspotsec-paperclip-plan.md)
- [Academic Review](./Paperclip AI_ Методология Оркестрации AI (1).md)

## License

Proprietary — BlindSpotSec SaaS
Paperclip framework: MIT License

---

**Last Updated:** 2026-04-19
**Version:** 0.1.0-alpha
