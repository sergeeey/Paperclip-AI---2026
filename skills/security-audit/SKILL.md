---
name: security-audit
description: OWASP Top 10 vulnerability scanning with mandatory NIST NVD checks for CVE identifiers (reduces fabricated CVE IDs; not a guarantee against all scanner FPs)
type: skill
version: 1.0.0
model: narrow-bridge
error-cost: CRITICAL (false positive = customer churn, reputational death)
---

# Security Audit Skill

## Level 0: Metadata

**Trigger:** When task contains "security audit", "scan", "OWASP", "vulnerability"
**Owner:** Scanner Bot
**Dependencies:** Brave Search API, NIST CVE Database access
**Output:** JSON report + markdown summary

---

## Primary Question Check (Skills 2.0)

❌ **DO NOT include in this skill:**
- How to scan for SQL injection → Claude knows natively
- How to use semgrep → Claude knows natively
- Generic OWASP Top 10 definitions → Claude knows natively

✅ **ONLY include BlindSpotSec-specific knowledge:**
- NIST CVE verification protocol (our anti-hallucination measure)
- Customer report format requirements
- Confidence scoring methodology
- False positive tracking via anti-patterns table

---

## Model: Narrow Bridge (Critical Process)

**Why Narrow Bridge:**
This is a **critical, fragile process** where errors destroy customer trust. A single hallucinated CVE in a report can lead to:
- Customer questions legitimacy → refund request
- Negative review on G2/Capterra → reputation damage
- Lost contract renewals → revenue loss

Therefore: **Zero creativity allowed. Follow exact steps.**

---

## Acceptor Results Action (Anokhin's Functional Systems Theory)

**BEFORE starting any scan, formalize success criteria:**

```yaml
Expected Result Specification:
  format: JSON + Markdown
  sections:
    - Executive Summary
    - Findings (grouped by severity)
    - Detailed Analysis
    - Remediation Steps
    - Conclusion

  quality_gates:
    - Every CVE has NIST database link
    - Every CVE has confidence score ≥ 0.85
    - Zero placeholders ("TODO", "TBD", "Lorem ipsum")
    - No syntactically-valid-but-nonexistent CVE IDs
    - All code snippets have file:line references

  failure_conditions:
    - NIST API returns 404 for any CVE → mark as [HYPOTHESIS]
    - Confidence score < 0.85 → flag for manual review
    - Report generation fails → do NOT email customer
```

**Scope note:** NIST verification validates that a **CVE record exists**, not that the customer’s code is exploitable. Semantic false positives (overly broad rules, misread context) are handled by confidence scores, anti-patterns table, Scanner self-check, and CEO gate—not by NVD alone.

**Document this specification in task comment BEFORE scanning.**

---

## Execution Protocol (Step-by-Step)

### Phase 1: Pre-Scan Validation

**Step 1.1: Verify Access**
```bash
# Check GitHub token is valid
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
# Expected: HTTP 200 + user data
# If 401: STOP, request Board to refresh token
```

**Step 1.2: Check Repository Size**
```bash
# Clone would fail if repo > 100MB (scanner limit)
REPO_SIZE=$(curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO | jq '.size')

if [ $REPO_SIZE -gt 102400 ]; then
  echo "⚠️ Repo size $REPO_SIZE KB exceeds 100MB limit"
  # Create task: "Manual review required: large repository"
  exit 1
fi
```

**Step 1.3: Confirm OWASP Category**
Check task description for specific vulnerability types requested:
- "Full scan" → all OWASP Top 10
- "SQL injection only" → use targeted ruleset
- "PQC readiness" → post-quantum cryptography audit

**Document findings in task comment:**
```
✅ Pre-scan validation complete:
- Repo: owner/repo-name
- Size: 45MB
- Access: verified
- Scope: Full OWASP Top 10 scan
```

---

### Phase 2: Scanning Execution

**Step 2.1: Clone Repository**
```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
WORK_DIR="/tmp/scan-$TIMESTAMP"
git clone https://github.com/$OWNER/$REPO $WORK_DIR
cd $WORK_DIR
```

**Step 2.2: Run Semgrep with OWASP Ruleset**
```bash
# Install if not present
pip install semgrep --quiet

# Run scan with JSON output
semgrep --config=p/owasp-top-ten \
  --json \
  --output=/tmp/scan-$TIMESTAMP-raw.json \
  .

# Capture exit code
SCAN_EXIT_CODE=$?
```

**Step 2.3: Parse Results**
```bash
# Extract findings
FINDINGS=$(cat /tmp/scan-$TIMESTAMP-raw.json | jq '.results')
FINDING_COUNT=$(echo $FINDINGS | jq 'length')

echo "🔍 Scan complete: $FINDING_COUNT potential findings"
```

---

### Phase 3: NIST CVE Verification (CRITICAL)

**For each finding that references a CVE:**

**Step 3.1: Extract CVE ID**
```bash
CVE_ID=$(echo $FINDING | grep -oP 'CVE-\d{4}-\d{4,7}')
```

**Step 3.2: Verify Against NIST Database**
```bash
NIST_RESPONSE=$(curl -s "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=$CVE_ID")
NIST_STATUS=$(echo $NIST_RESPONSE | jq -r '.resultsPerPage')

if [ "$NIST_STATUS" == "0" ]; then
  echo "🚫 CVE $CVE_ID NOT FOUND in NIST database"
  # Mark as HYPOTHESIS, not confirmed vulnerability
  FINDING_STATUS="[HYPOTHESIS] Potential issue, CVE not verified"
else
  echo "✅ CVE $CVE_ID verified in NIST"
  NIST_LINK="https://nvd.nist.gov/vuln/detail/$CVE_ID"
  FINDING_STATUS="[VERIFIED] Known vulnerability"
fi
```

**Step 3.3: Rate Limiting Protection**
```bash
# NIST API limit: 5 requests/second without API key
sleep 0.2  # 200ms delay between requests
```

**WHY THIS IS MANDATORY:**
Semgrep rulesets sometimes reference CVE IDs that:
- Were proposed but never assigned
- Have typos (CVE-2024-12345 vs CVE-2024-1234)
- Are syntactically valid but nonexistent

Shipping these to customers = instant credibility loss.

---

### Phase 4: Confidence Scoring

**For each verified finding, calculate confidence score:**

```python
def calculate_confidence(finding):
    score = 0.0

    # Exact pattern match (high confidence)
    if finding['check_id'].startswith('javascript.lang.security'):
        score += 0.6

    # Has CVE reference + NIST verified
    if finding.get('metadata', {}).get('cve') and nist_verified:
        score += 0.3

    # Multiple occurrences in codebase
    occurrence_count = finding.get('extra', {}).get('metadata', {}).get('occ_count', 1)
    if occurrence_count > 1:
        score += 0.1

    return min(score, 1.0)  # Cap at 1.0

# Threshold for inclusion in report
if confidence >= 0.85:
    findings_verified.append(finding)
else:
    findings_manual_review.append(finding)
```

---

### Phase 5: Report Generation

**Step 5.1: Structure JSON Report**
```json
{
  "scan_metadata": {
    "repository": "owner/repo-name",
    "scan_date": "2026-04-20T15:30:00Z",
    "scanner_version": "1.0.0",
    "owasp_ruleset": "p/owasp-top-ten",
    "total_findings": 12,
    "verified_findings": 8,
    "hypothesis_findings": 4
  },
  "executive_summary": {
    "severity_breakdown": {
      "critical": 2,
      "high": 3,
      "medium": 3,
      "low": 0
    },
    "primary_risks": [
      "SQL Injection in authentication endpoint",
      "XSS in user profile rendering"
    ]
  },
  "findings": [
    {
      "id": "finding-001",
      "severity": "CRITICAL",
      "category": "A03:2021 Injection",
      "title": "SQL Injection in login.php",
      "cve": "CVE-2023-12345",
      "nist_link": "https://nvd.nist.gov/vuln/detail/CVE-2023-12345",
      "confidence_score": 0.93,
      "location": {
        "file": "src/auth/login.php",
        "line": 47,
        "code_snippet": "SELECT * FROM users WHERE username='$username'"
      },
      "description": "User input directly concatenated into SQL query without parameterization",
      "impact": "Attacker can bypass authentication or extract sensitive data",
      "remediation": "Use prepared statements with parameterized queries",
      "references": [
        "https://owasp.org/www-community/attacks/SQL_Injection",
        "https://nvd.nist.gov/vuln/detail/CVE-2023-12345"
      ]
    }
  ]
}
```

**Step 5.2: Generate Markdown Summary**
```markdown
# Security Audit Report: owner/repo-name

**Scan Date:** 2026-04-20
**Scanner:** BlindSpotSec v1.0.0
**Methodology:** OWASP Top 10 (2021)

## Executive Summary

This scan identified **12 potential security issues**, of which **8 are verified** against NIST CVE database.

### Severity Breakdown
- 🔴 Critical: 2
- 🟠 High: 3
- 🟡 Medium: 3
- 🟢 Low: 0

### Top Risks
1. **SQL Injection** in authentication endpoint → Data breach risk
2. **XSS** in user profile → Account takeover risk

## Detailed Findings

### [CRITICAL] Finding-001: SQL Injection in login.php

**CVE:** [CVE-2023-12345](https://nvd.nist.gov/vuln/detail/CVE-2023-12345) ✅ Verified
**Confidence:** 93%
**Location:** `src/auth/login.php:47`

**Vulnerable Code:**
```php
SELECT * FROM users WHERE username='$username'
```

**Impact:** Attacker can bypass authentication by injecting `' OR '1'='1`

**Remediation:**
```php
$stmt = $pdo->prepare("SELECT * FROM users WHERE username = ?");
$stmt->execute([$username]);
```

---

## Appendix: Unverified Findings

The following findings could not be verified against NIST database and require manual review:

- [HYPOTHESIS] Potential CSRF in /api/transfer endpoint
- [HYPOTHESIS] Weak cryptography (MD5 hash usage)

---

**Report generated by:** BlindSpotSec Scanner Bot
**Review required:** YES (unverified findings present)
```

---

### Phase 6: Self-Check (Worker HEARTBEAT Step 5)

**BEFORE marking task as done, verify:**

```bash
# Checklist (all must pass)
[ ] Report file exists at expected path
[ ] JSON is valid (jq . report.json)
[ ] Markdown is valid (no broken syntax)
[ ] All CVEs have NIST links
[ ] No placeholders ("TODO", "TBD", "Lorem ipsum")
[ ] No broken links (curl -I each URL returns 200)
[ ] Confidence scores present for all findings
[ ] File:line references are accurate

# Anti-patterns check
[ ] No hallucinated CVE IDs (all verified via NIST)
[ ] No vague descriptions ("security issue" without specifics)
[ ] No missing remediation steps
```

**If ANY check fails:**
1. Do NOT mark task as done
2. Add comment to task: "Self-check failed: [specific issue]"
3. Fix the issue
4. Re-run self-check

**Only after ALL checks pass:**
```bash
# Document self-check completion in task comment
echo "✅ Self-check complete. All quality gates passed."
```

---

## Anti-Patterns Table (Institutional Memory)

**Purpose:** Track recurring mistakes to prevent repetition

| Mistake | Date | Root Cause | Fix Applied | Verified |
|---------|------|------------|-------------|----------|
| Hallucinated CVE-2024-99999 | 2026-04-20 | Semgrep rule referenced nonexistent CVE | Added NIST verification step | ✅ 2026-04-21 |
| Report sent with "TODO: add remediation" | 2026-04-22 | Skipped self-check | Made self-check mandatory in HEARTBEAT | ✅ 2026-04-23 |
| SQL injection false positive (prepared statement misidentified) | 2026-04-25 | Semgrep pattern too broad | Lowered confidence score, flagged for manual review | ✅ 2026-04-26 |

**Process:**
1. When CEO reports error in scanner output → add row to this table
2. Increment occurrence counter if same mistake repeats: [×2], [×3]
3. If [×3] → escalate to Board (systemic issue, need SKILL.md rewrite)

---

## Validation Cycle: Plan → Confirm → Execute

**For destructive operations (e.g., deleting temp files, sending report):**

### Plan
```bash
# Before deletion
echo "Plan: Delete /tmp/scan-$TIMESTAMP directory (324MB)"
echo "Impact: Free disk space, remove customer code from server"
echo "Risks: Accidental deletion of wrong directory if $TIMESTAMP variable empty"
```

### Confirm
```bash
# Validate variable is set
if [ -z "$TIMESTAMP" ]; then
  echo "🚫 BLOCKED: TIMESTAMP variable empty, would delete /tmp/scan-/"
  exit 1
fi

# Validate path exists
if [ ! -d "/tmp/scan-$TIMESTAMP" ]; then
  echo "🚫 BLOCKED: Directory does not exist"
  exit 1
fi

# Request human confirmation for destructive action
echo "Confirm deletion? (requires Board approval via Execution Policy)"
```

### Execute
```bash
# Only after confirmation
rm -rf "/tmp/scan-$TIMESTAMP"
echo "✅ Cleanup complete"
```

---

## Integration with CEO Quality Gate

**After scanner completes, CEO must verify BEFORE emailing customer:**

CEO HEARTBEAT Step 4 (Quality Control Gate):
```yaml
4a. Open report at /tmp/scan-$TIMESTAMP-report.json
4b. Verify:
    - JSON parses without errors
    - All CVEs have https://nvd.nist.gov links
    - No placeholders or "TODO" markers
    - Confidence scores ≥ 0.85 for all findings
4c. Check Scanner Bot's self-check comment in task
4d. If any red flags → reject, reassign to Scanner Bot with feedback
4e. If all pass → approve for delivery
```

**CEO must NEVER forward scanner output unchecked.**

---

## References (Level 2)

For detailed information, see:
- `owasp-top-10-detailed.md` — Full OWASP category descriptions
- `cve-verification-protocol.md` — NIST API usage, rate limiting, fallback strategies
- `semgrep-ruleset-guide.md` — Which rulesets for which languages
- `confidence-scoring-methodology.md` — How we calculate confidence scores

---

## Update Log

| Version | Date | Change | Reason |
|---------|------|--------|--------|
| 1.0.0 | 2026-04-20 | Initial release | Skills 2.0 compliance |
| 1.0.1 | TBD | (Future updates tracked here) | |

---

**Skill Owner:** Scanner Bot
**Review Frequency:** After every 10 scans or when false positive reported
**Last Reviewed:** 2026-04-20
