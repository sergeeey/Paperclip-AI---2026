# BlindSpotSec Deployment Runbook

**Purpose:** Step-by-step manual for deploying Paperclip infrastructure and launching first scan

**Estimated Time:** 90 minutes (from zero to first scan)

**Prerequisites:**
- Credit card for Hostinger ($6/month, refundable within 30 days)
- OpenAI account (for Codex)
- Anthropic account (for Claude)
- Email for notifications

---

## Phase 1: VPS Infrastructure (30 min)

### Step 1.1: Register Hostinger Account

1. Navigate to: `https://www.hostinger.com/vps`
2. Click "Get Started"
3. Create account (Email or Google Sign-In)
4. **Important:** Save credentials in password manager immediately

### Step 1.2: Select VPS Plan

**Plan Selection:**
- Plan: **KVM 1** (not KVM 2 - cost optimization, see ADR-006)
- Period: **12 months** (enables discount + free domain)
- Location: Select closest data center for minimum latency
  - EU customers: Amsterdam or London
  - US customers: New York or Los Angeles
  - Asia customers: Singapore

**Apply Discount Code:**
- Partner code: `METICSMEDIA` (if available)
- Verify discount appears in cart

**Specs Confirmed:**
- 2 vCPU
- 4GB RAM
- 100GB SSD
- Price: ~$6/month ($72/year)

**Click:** "Proceed to Payment"

### Step 1.3: Complete Payment

- Enter payment details
- Verify 30-day money-back guarantee displayed
- Complete purchase
- Save order confirmation email

**Wait:** 2-5 minutes for VPS provisioning

### Step 1.4: Deploy Paperclip Template

1. Navigate to: Hostinger Panel → VPS → Manage
2. Click: "Applications" tab
3. Search: "Paperclip" or "Node.js"
4. Select: **Paperclip AI** template (one-click install)
5. Click: "Deploy"

**Configuration Options:**
- Admin Password: **GENERATE STRONG PASSWORD** (20+ chars)
- Domain: Use temporary IP or free subdomain (e.g., `blindspotsec.hostname.com`)
- SSL: Enable (free Let's Encrypt)

**Save Immediately:**
```
VPS IP: [generated_ip_address]
Admin Password: [generated_password]
SSH Port: 22 (default)
Paperclip URL: http://[IP]:3100
```

**Store in password manager** (1Password, Bitwarden, etc.)

**Wait:** 5-10 minutes for Paperclip installation

### Step 1.5: Verify Deployment

1. Open browser: `http://[YOUR_VPS_IP]:3100`
2. Expected: Paperclip login screen
3. Login: Username `admin`, Password [from Step 1.4]
4. Expected: Paperclip dashboard (empty, no companies yet)

**If fails:**
- Check VPS status in Hostinger Panel (should be "Running")
- Verify port 3100 in firewall rules (should be open)
- Wait additional 5 minutes (Docker containers may still be starting)
- Check logs: SSH into VPS → `docker logs paperclip`

---

## Phase 2: API Configuration (20 min)

### Step 2.1: OpenAI Codex Authorization (CRITICAL)

**Pre-requisite Security Setting:**

1. Navigate to: `https://chatgpt.com/settings`
2. Click: "Security" tab
3. Find: "Device Code Authorization for Codex"
4. **Enable this toggle** (required for terminal auth)
5. Save changes

**SSH into VPS:**

```bash
# From your local terminal
ssh root@[YOUR_VPS_IP]
# Enter password from Step 1.4 when prompted
```

**Find Paperclip Container:**

```bash
docker ps
# Look for container with "paperclip" in name
# Copy CONTAINER_ID (first column)
```

**Enter Container:**

```bash
docker exec -it [CONTAINER_ID] bash
# You're now inside Paperclip container
```

**Authorize Codex:**

```bash
openai auth login
```

**Expected Output:**
```
To authorize this device, visit:
  https://platform.openai.com/activate/device?user_code=ABCD-EFGH

Waiting for authorization...
```

**Authorization Steps:**

1. **Copy the URL** exactly as shown
2. **Open in browser** (new tab)
3. **Login to OpenAI** if not already logged in
4. **Enter the code** (e.g., `ABCD-EFGH`)
5. **Click "Authorize"**
6. **Return to terminal**

**Expected Terminal Output:**
```
✅ Successfully logged in as [your-email@example.com]
```

**⚠️ If fails:**
- Error: "Device authorization not enabled"
  → Go back to Step 2.1, verify toggle is ON
- Error: "Invalid code"
  → Code expires in 10 minutes, run `openai auth login` again
- Error: "Network error"
  → Check VPS internet connectivity: `ping platform.openai.com`

**Exit Container:**
```bash
exit
```

**Verify Authorization Persisted:**
```bash
docker exec [CONTAINER_ID] openai models list
# Should show available models without error
```

### Step 2.2: Get API Keys

**Anthropic API Key (for Scanner Bot):**

1. Navigate to: `https://console.anthropic.com/`
2. Create account or login
3. Click: "API Keys" → "Create Key"
4. Name: `BlindSpotSec-Scanner`
5. **Copy key immediately** (starts with `sk-ant-`)
6. **Paste into password manager**
7. Key format: `sk-ant-api03-XXXX...`

**OpenAI API Key (for Codex via API):**

1. Navigate to: `https://platform.openai.com/api-keys`
2. Click: "Create new secret key"
3. Name: `BlindSpotSec-CEO`
4. **Copy key immediately** (starts with `sk-`)
5. **Paste into password manager**
6. **Note:** Different from Codex device auth (this is for programmatic API access)

**Brave Search API Key:**

1. Navigate to: `https://brave.com/search/api/`
2. Click: "Get Started"
3. Select: **$5/month plan** (includes 2000 free queries)
4. **Critical:** Set Usage Limit = $5 (prevents overcharging)
5. Complete payment
6. Copy API key (format: `BSA...`)
7. **Paste into password manager**

**Resend API Key:**

1. Navigate to: `https://resend.com/`
2. Sign up (free tier: 100 emails/day, sufficient for MVP)
3. Verify email address
4. Navigate to: "API Keys" → "Create API Key"
5. Name: `BlindSpotSec-Reports`
6. Copy key (format: `re_...`)
7. **Paste into password manager**

**Verification Checklist:**
- [ ] Anthropic API key saved (sk-ant-...)
- [ ] OpenAI API key saved (sk-...)
- [ ] Brave Search API key saved (BSA...)
- [ ] Resend API key saved (re_...)
- [ ] All keys in password manager
- [ ] No keys in browser history or plain text files

---

## Phase 3: Company Creation (15 min)

### Step 3.1: Create Company

**Access Paperclip UI:**
- URL: `http://[YOUR_VPS_IP]:3100`
- Login as admin

**Create Company:**

1. Click: "Companies" → "New Company"
2. Fill in:
   ```
   Name: BlindSpotSec

   Goal: Automated security audit SaaS producing OWASP Top 10 reports with NIST-backed CVE identifiers

   Budget (monthly): $450
   Currency: USD
   ```
3. Click: "Create Company"

**Why $450 budget?** (See ADR-005)
- Scanner Bot: $300
- Reporter Bot: $200
- CEO: $100
- **Sum:** $600
- **Company budget:** $450 (safety buffer = $150)
- **Reason:** Prevents all agents from maxing out simultaneously

### Step 3.2: Hire CEO

**Navigate to:** BlindSpotSec → Agents → "Hire Agent"

**Configuration:**

```yaml
Name: CEO

Role: Chief Executive Officer

Adapter: codex
  (Note: Use codex, not claude_local, for CEO delegation skills)

Model: v5.3
  (Latest stable Codex model as of 2026-04)

Budget (monthly): $100
  (10000 cents in UI)

Pulse: 600
  (600 seconds = 10 minutes between heartbeats)

Reports To: [None - CEO is root]
```

**Secrets Configuration:**

For CEO, we don't add secrets yet. CEO delegates, doesn't execute tools directly.

**API Integrity Check:**

1. Click: "Test API Connection"
2. Expected: "✅ Connection successful"
3. If fails:
   - Verify Codex authorization completed (Step 2.1)
   - Check: `docker exec [CONTAINER_ID] openai auth status`
   - Re-run authorization if needed

**Click:** "Hire Agent"

**Verify:** CEO appears in Agents list with status "Idle"

### Step 3.3: Configure CEO Files (Optional but Recommended)

**Upload CEO SOUL.md:**

1. Navigate to: CEO → Files → "Upload"
2. Upload: `agents/ceo/SOUL.md` (from this repo)
3. Content includes:
   - "Quality Control Is My Most Important Job"
   - "Idle is success" principle
   - Identity definition

**Upload CEO HEARTBEAT.md:**

1. Navigate to: CEO → Files → "Upload"
2. Upload: `agents/ceo/HEARTBEAT.md`
3. Contains 12-step state machine
4. Step 4 = Quality Control Gate (critical)

*If files not ready yet:* Skip for MVP, add after first scan reveals issues

---

## Phase 4: Worker Agent Hiring (15 min)

### Step 4.1: Hire Scanner Bot

**Navigate to:** BlindSpotSec → Agents → "Hire Agent"

**Configuration:**

```yaml
Name: Scanner Bot

Role: Security Scanner

Adapter: claude_local
  (Claude for code analysis superiority)

Model: claude-sonnet-4-6
  (Anthropic's latest Sonnet)

Budget (monthly): $300
  (30000 cents in UI)

Pulse: 300
  (300 seconds = 5 minutes - faster for critical security tasks)

Reports To: CEO
  (Select CEO from dropdown)
```

**Secrets Configuration:**

1. Click: "Secrets" tab
2. Click: "Add Secret"
3. Configuration:
   ```
   Key Name: BRAVE_SEARCH_API
   Value: [paste from password manager]
   Mode: Plain
   ```
4. Click: **"Seal"** button
   - This encrypts the secret
   - Creates reusable secret for other agents
5. Verify: Mode changes to "Sealed"

**Skills Configuration:**

1. Click: "Skills" tab
2. Click: "Add Skill"
3. Upload: `skills/security-audit/SKILL.md`
4. Verify: Skill appears in list

**Click:** "Hire Agent"

**Verify:** Scanner Bot appears with "Idle" status

### Step 4.2: Hire Reporter Bot

**Navigate to:** BlindSpotSec → Agents → "Hire Agent"

**Configuration:**

```yaml
Name: Reporter Bot

Role: Report Generator

Adapter: codex
  (Fast markdown generation)

Model: v5.3

Budget (monthly): $200
  (20000 cents)

Pulse: 600
  (10 minutes - lower priority than scanner)

Reports To: CEO
```

**Secrets Configuration:**

1. Click: "Secrets" tab
2. Click: "Add Secret"
3. Configuration:
   ```
   Key Name: RESEND_API
   Mode: Secret  ← SELECT THIS (not Plain)
   Value: [SELECT FROM DROPDOWN]
   ```
4. **Select:** `RESEND_API` from dropdown
   - This reuses the secret sealed by Scanner Bot
   - **No duplication, improved security**

**Note on Brave Search:**
Reporter Bot also needs Brave Search for threat intelligence lookup.

5. Click: "Add Secret" (again)
6. Configuration:
   ```
   Key Name: BRAVE_SEARCH_API
   Mode: Secret
   Value: [SELECT FROM DROPDOWN - already sealed by Scanner]
   ```

**Click:** "Hire Agent"

**Verify:** Reporter Bot appears in agents list

---

## Phase 5: First Task Execution (10 min + wait time)

### Step 5.1: Create Test Task

**Navigate to:** BlindSpotSec → Tasks → "New Task"

**Task Configuration:**

```yaml
Title: Tools Test: Scan OWASP NodeGoat and email report

Description: |
  Scan the OWASP NodeGoat vulnerable demo application and deliver
  security report via email.

  Repository: https://github.com/OWASP/NodeGoat
  Target email: [YOUR_EMAIL]@example.com

  Expected deliverables:
  1. JSON report with OWASP Top 10 findings
  2. Markdown summary with remediation steps
  3. All CVEs verified against NIST database
  4. Email delivery confirmation

  Success criteria (Acceptor Results Action):
  - Email received within 30 minutes
  - Report has 5 sections (Intro, Findings, Severity, Remediation, Conclusion)
  - All CVEs have NIST links
  - No "TODO" or placeholders
  - At least 5 vulnerabilities identified (NodeGoat is intentionally vulnerable)

Assign To: CEO

Priority: High

Deadline: [Today + 4 hours]
```

**Click:** "Create Task"

**Task appears in:** "To Do" column

### Step 5.2: Trigger CEO Heartbeat

**Option A: Automatic (wait for next Pulse)**
- CEO Pulse = 600s = 10 minutes
- Task will be picked up automatically
- Wait 10 minutes, refresh dashboard

**Option B: Manual Trigger (faster)**
1. Navigate to: CEO → Settings
2. Click: "Manual Heartbeat" button
3. **Immediate:** CEO wakes up, sees task
4. Expected: Task moves to "In Progress" within 30 seconds

### Step 5.3: Monitor Execution

**Dashboard View:**

Refresh every 30 seconds, watch task progress through columns:

```
To Do → Assigned → In Progress → Review → Done
```

**Expected Flow:**

1. **CEO Analysis** (~2 min)
   - Reads task description
   - Identifies need for Scanner Bot
   - Creates delegation sub-task
   - Assigns to Scanner Bot

2. **Scanner Bot Execution** (~10-15 min)
   - Clones NodeGoat repository
   - Runs semgrep with OWASP ruleset
   - Verifies CVEs against NIST
   - Generates JSON report
   - Self-check (HEARTBEAT Step 5)
   - Hands off to Reporter Bot

3. **Reporter Bot Execution** (~5 min)
   - Reads Scanner JSON
   - Generates markdown summary
   - Formats for email
   - Self-check (no placeholders)
   - Returns to CEO

4. **CEO Quality Gate** (~2 min)
   - Opens report file
   - Verifies CVEs have NIST links
   - Checks for placeholders
   - Approves for delivery

5. **Reporter Bot Delivery** (~1 min)
   - Calls Resend API
   - Sends email
   - Marks task complete

**Total time:** ~20-30 minutes

### Step 5.4: Troubleshooting

**If task stuck in "To Do" > 15 min:**

**Check:** CEO Heartbeat executed?
```bash
docker logs paperclip | grep "CEO"
# Should show heartbeat activity
```

**Fix:** Manual heartbeat trigger (Step 5.2 Option B)

---

**If task stuck in "Blocked":**

**Check:** Task comments for blocker reason
1. Navigate to: Task → Comments
2. Look for agent messages like:
   - "GitHub token invalid"
   - "NIST API rate limited"
   - "Brave Search quota exceeded"

**Common Blockers:**

| Blocker Message | Root Cause | Fix |
|----------------|------------|-----|
| "GitHub API 401" | Token expired | Generate new token, update secrets |
| "NIST API 429" | Rate limit hit | Wait 30 seconds, retry |
| "Brave API 403" | Usage limit exceeded | Check billing, increase limit |
| "Resend API 402" | Free tier exceeded | Upgrade plan or wait for reset |

---

**If report email not received within 30 min:**

**Check 1:** Spam folder

**Check 2:** Resend dashboard (resend.com)
- Navigate to: Logs → Recent Emails
- Verify email sent successfully
- If bounced: check recipient email spelling

**Check 3:** Reporter Bot logs
```bash
docker exec [CONTAINER_ID] tail -f /var/log/reporter-bot.log
# Look for Resend API call success/failure
```

---

**If report received but has issues:**

**Issue:** Placeholders ("TODO", "TBD")
→ **Cause:** Self-check failed to catch
→ **Fix:** Update Scanner HEARTBEAT.md, strengthen self-check

**Issue:** Hallucinated CVE (not in NIST)
→ **Cause:** NIST verification step skipped
→ **Fix:** Check HaluGate logs, verify pre-tool-use hook executed

**Issue:** No CVE links
→ **Cause:** Reporter Bot didn't include NIST URLs
→ **Fix:** Update report-generation skill template

**For all issues:**
1. Add to anti-patterns table (skills/security-audit/SKILL.md)
2. Update relevant HEARTBEAT.md or SKILL.md
3. Re-run same task to verify fix

---

## Phase 6: Post-Deployment Verification (5 min)

### Step 6.1: Budget Check

**Navigate to:** BlindSpotSec → Costs & Budgets

**Verify:**
- Total spent < $10 (first scan should be cheap)
- Scanner Bot: Highest cost (expected)
- CEO: Low cost (delegation is cheap)
- Reporter Bot: Medium cost

**If any agent >$50 spent:**
- Check for infinite loop (task retries)
- Review Pulse settings (may be too frequent)
- Check task comments for failure → retry cycles

### Step 6.2: Memory Bank Check

**Verify files updated:**

```bash
ssh root@[VPS_IP]
docker exec [CONTAINER_ID] cat /app/.paperclip/memory/activeContext.md
# Should show "Last Updated: [today's date]"
# Should mention NodeGoat scan in Recent Topics
```

**If not updated:**
- Memory Bank pattern not enforced yet (acceptable for MVP)
- Add reminder in CEO HEARTBEAT Step 9

### Step 6.3: HaluGate Verification

**Check logs:**

```bash
ssh root@[VPS_IP]
cat /tmp/halugate-$(date +%Y%m%d).log
```

**Expected entries:**
- Pre-tool-use inspections (rm -rf, curl, git commands)
- Post-tool-use verifications (semgrep JSON, NIST responses)

**If no entries:**
- HaluGate hooks not executed (check Paperclip hook configuration)
- Verify hooks are executable: `ls -la .paperclip/hooks/`

**If entries show BLOCKED:**
- Review blocked command in log
- Verify it was legitimate block (hallucinated path) or false positive
- Update hook logic if false positive

### Step 6.4: Success Criteria Checklist

**Deployment Complete when ALL are ✅:**

- [ ] Paperclip UI accessible 24/7 (http://[VPS_IP]:3100)
- [ ] CEO + Scanner + Reporter hired and idle
- [ ] NodeGoat scan completed successfully
- [ ] Report email received with verified CVEs
- [ ] Budget tracking shows <$10 spent
- [ ] Memory Bank files updated (activeContext.md has today's date)
- [ ] HaluGate logs show at least 1 inspection

**If any ❌:**
- Do NOT proceed to customer scans
- Debug failed item using troubleshooting sections above
- Iterate until all ✅

---

## Next Steps After Successful Deployment

### Immediate (Day 2-3):
1. **Update anti-patterns table** with any issues found
2. **Write customer onboarding email template**
3. **Create LinkedIn post** about zero-human security audit

### Week 2:
1. **Recruit 5 beta customers** (free scan offer)
2. **Monitor burn rate** (should stabilize <$300/month)
3. **Tune Pulse settings** if too slow or expensive

### Month 2:
1. **Transition to paid scans** ($100/scan)
2. **Enable auto-hiring** (Manual Approval → Auto)
3. **Consider EchoVault** for semantic memory

---

## Emergency Contacts

**If catastrophic failure:**

1. **Hostinger Support:** Ticket system (24/7)
   - For: VPS downtime, network issues
   - SLA: <4 hours response

2. **Paperclip GitHub Issues:** github.com/paperclipai/paperclip/issues
   - For: Bugs, API issues
   - Tag: `@paperclipai/support`

3. **Budget Auto-Pause Triggered:**
   - Check: Costs & Budgets dashboard
   - Fix: Increase budget OR wait for month reset
   - Resume: Agent Settings → "Resume" button

4. **Data Loss (VPS crash):**
   - Memory Bank lost: Recreate from backup (see docs/BACKUP.md)
   - PostgreSQL corrupted: Hostinger support can restore from snapshot

---

## Appendix: Common Commands

**SSH into VPS:**
```bash
ssh root@[YOUR_VPS_IP]
```

**Find Paperclip container:**
```bash
docker ps | grep paperclip
```

**View Paperclip logs:**
```bash
docker logs -f [CONTAINER_ID]
```

**Restart Paperclip:**
```bash
docker restart [CONTAINER_ID]
```

**Check disk space:**
```bash
df -h
```

**Check RAM usage:**
```bash
free -h
```

**View HaluGate logs:**
```bash
cat /tmp/halugate-$(date +%Y%m%d).log
```

**Manual Heartbeat (from CLI):**
```bash
docker exec [CONTAINER_ID] npx paperclip heartbeat --agent-id=[AGENT_ID]
```

**Backup Memory Bank:**
```bash
docker cp [CONTAINER_ID]:/app/.paperclip/memory ./backup-$(date +%Y%m%d)
```

---

**Deployment Runbook Version:** 1.0.0
**Last Updated:** 2026-04-19
**Tested On:** Hostinger KVM 1, Paperclip v2026.416.0
