# BlindSpotSec Quick Start — Next 90 Minutes

**Current Time:** [Check your clock]
**Target:** First scan complete by [+90 minutes]

---

## 🚀 Phase 1: VPS Setup (Now → +30 min)

### Step 1: Register Hostinger (5 min)

**Open in browser:**
```
https://www.hostinger.com/vps
```

**Actions:**
1. Click "Get Started"
2. Sign up with email or Google
3. **IMMEDIATELY:** Save credentials in password manager
   - Email: [your email]
   - Password: [generated password]
   - Service: Hostinger VPS

### Step 2: Order VPS (3 min)

**Select:**
- Plan: **KVM 1** (NOT KVM 2)
- Period: **12 months** ($72 total)
- Location: [Closest to you]
  - EU: Amsterdam or London
  - US: New York or LA
  - Asia: Singapore

**Discount code:** `METICSMEDIA` (if available)

**Payment:** Complete checkout

### Step 3: Deploy Paperclip (2 min)

**After VPS provisioned:**
1. Hostinger Panel → VPS → Manage
2. Applications tab
3. Search: "Paperclip" or "Node.js"
4. Select: **Paperclip AI** template
5. Click "Deploy"

**Configuration:**
- Generate strong password (20+ chars)
- **IMMEDIATELY SAVE:**

```
VPS IP: [PASTE HERE]
Admin Password: [PASTE HERE]
Paperclip URL: http://[VPS_IP]:3100
SSH Command: ssh root@[VPS_IP]
```

**Paste this into password manager NOW** ← DO NOT SKIP

### Step 4: Wait for Installation (10 min)

**While waiting, get API keys:**

#### Anthropic API Key
1. Open: https://console.anthropic.com/
2. Create account or login
3. API Keys → Create Key
4. Name: `BlindSpotSec-Scanner`
5. **COPY KEY** (starts with `sk-ant-`)
6. **SAVE:** `Anthropic_API_Key: sk-ant-[PASTE]`

#### OpenAI API Key
1. Open: https://platform.openai.com/api-keys
2. Create new secret key
3. Name: `BlindSpotSec-CEO`
4. **COPY KEY** (starts with `sk-`)
5. **SAVE:** `OpenAI_API_Key: sk-[PASTE]`

#### Brave Search API
1. Open: https://brave.com/search/api/
2. Sign up → $5/month plan
3. **CRITICAL:** Set Usage Limit = $5
4. **COPY KEY** (starts with `BSA`)
5. **SAVE:** `Brave_API_Key: BSA[PASTE]`

#### Resend API
1. Open: https://resend.com/
2. Sign up (free tier)
3. Verify email
4. API Keys → Create
5. Name: `BlindSpotSec-Reports`
6. **COPY KEY** (starts with `re_`)
7. **SAVE:** `Resend_API_Key: re_[PASTE]`

### Step 5: Verify Deployment (2 min)

**Open browser:**
```
http://[YOUR_VPS_IP]:3100
```

**Expected:** Paperclip login screen

**Login:**
- Username: `admin`
- Password: [from Step 3]

**Expected:** Empty dashboard

**If fails:** Wait 5 more minutes (Docker still starting)

---

## 🔐 Phase 2: Codex Authorization (Now + 30 min → +50 min)

### Step 1: Enable Device Code Auth (1 min)

**Open:** https://chatgpt.com/settings

**Actions:**
1. Click "Security" tab
2. Find: "Device Code Authorization for Codex"
3. **ENABLE** toggle
4. Save

**⚠️ THIS IS REQUIRED** — auth will fail without it

### Step 2: SSH into VPS (2 min)

**Open terminal on your computer:**

```bash
ssh root@[YOUR_VPS_IP]
# Paste IP from Step 1 Phase 3

# When prompted for password:
# Paste admin password from password manager
```

**Expected:** Root shell prompt: `root@vps-hostname:~#`

### Step 3: Find Paperclip Container (1 min)

```bash
docker ps
```

**Expected output:**
```
CONTAINER ID   IMAGE              COMMAND       CREATED        STATUS
abc123def456   paperclip:latest   "npm start"   10 minutes ago Up 10 minutes
```

**Copy the CONTAINER ID** (first column, e.g., `abc123def456`)

**Save for future use:**
```bash
# Set variable for convenience
export PAPERCLIP_CONTAINER=abc123def456
# Replace abc123def456 with YOUR container ID
```

### Step 4: Authorize Codex (5 min)

```bash
docker exec -it $PAPERCLIP_CONTAINER bash
# You're now INSIDE the container

openai auth login
```

**Expected output:**
```
To authorize this device, visit:
  https://platform.openai.com/activate/device?user_code=ABCD-EFGH

Waiting for authorization...
```

**Actions:**
1. **COPY the URL** (highlight and copy)
2. **Open in NEW browser tab**
3. **Login to OpenAI** (if not already)
4. **Enter code:** ABCD-EFGH (your code will be different)
5. **Click "Authorize"**
6. **Return to terminal**

**Expected terminal output:**
```
✅ Successfully logged in as [your-email]
```

**Exit container:**
```bash
exit
```

### Step 5: Verify Authorization (1 min)

```bash
docker exec $PAPERCLIP_CONTAINER openai models list
```

**Expected:** List of models without errors

**If error:** Re-run Step 4

---

## 🏢 Phase 3: Create Company (Now + 50 min → +65 min)

### Step 1: Create Company (3 min)

**Paperclip UI:** http://[VPS_IP]:3100

**Navigate:** Companies → New Company

**Fill in:**
```
Name: BlindSpotSec

Goal: Automated security audit SaaS producing OWASP Top 10 reports with NIST-backed CVE identifiers

Monthly Budget: $450
(enter 45000 cents)
```

**Click:** Create Company

### Step 2: Hire CEO (5 min)

**Navigate:** BlindSpotSec → Agents → Hire Agent

**Configuration:**
```
Name: CEO
Role: Chief Executive Officer
Adapter: codex
Model: v5.3
Monthly Budget: $100 (10000 cents)
Pulse: 600
Reports To: [None]
```

**Click:** "Test API Connection"
**Expected:** ✅ Connection successful

**Click:** "Hire Agent"

**Verify:** CEO appears in agents list, status "Idle"

### Step 3: Hire Scanner Bot (4 min)

**Navigate:** Agents → Hire Agent

**Configuration:**
```
Name: Scanner Bot
Role: Security Scanner
Adapter: claude_local
Model: claude-sonnet-4-6
Monthly Budget: $300 (30000 cents)
Pulse: 300
Reports To: CEO
```

**Secrets tab:**
1. Add Secret → Name: `BRAVE_SEARCH_API`
2. Mode: Plain
3. Value: [Paste from password manager]
4. Click **"Seal"** ← IMPORTANT

**Click:** "Hire Agent"

### Step 4: Hire Reporter Bot (3 min)

**Navigate:** Agents → Hire Agent

**Configuration:**
```
Name: Reporter Bot
Role: Report Generator
Adapter: codex
Model: v5.3
Monthly Budget: $200 (20000 cents)
Pulse: 600
Reports To: CEO
```

**Secrets tab:**
1. Add Secret → Name: `RESEND_API`
2. Mode: **Secret** (not Plain)
3. Value: [Select `RESEND_API` from dropdown]
4. Add Secret (again) → Name: `BRAVE_SEARCH_API`
5. Mode: **Secret**
6. Value: [Select from dropdown]

**Click:** "Hire Agent"

**Verify:** 3 agents hired (CEO, Scanner Bot, Reporter Bot)

---

## 🎯 Phase 4: First Scan (Now + 65 min → +90 min)

### Step 1: Create Task (2 min)

**Navigate:** Tasks → New Task

**Copy-paste this:**
```
Title: Tools Test: Scan OWASP NodeGoat

Description:
Scan OWASP NodeGoat vulnerable demo application.

Repository: https://github.com/OWASP/NodeGoat
Email report to: [YOUR_EMAIL]

Expected:
- JSON report with OWASP Top 10 findings
- All CVEs verified against NIST
- Email delivery within 30 minutes
- At least 5 vulnerabilities found

Success criteria:
✅ Email received
✅ Report has 5 sections
✅ All CVEs have NIST links
✅ No placeholders (TODO, TBD)

Assign To: CEO
Priority: High
Deadline: [Today + 4 hours]
```

**Replace `[YOUR_EMAIL]` with your actual email**

**Click:** Create Task

### Step 2: Trigger Execution (1 min)

**Option A: Manual (faster)**
1. Navigate: CEO → Settings
2. Click: "Manual Heartbeat"
3. Refresh dashboard

**Option B: Automatic (wait 10 min)**
- CEO Pulse = 600s
- Task picked up automatically

### Step 3: Monitor (20-30 min)

**Refresh dashboard every 30 seconds**

**Expected flow:**
```
To Do (0 min)
  ↓
Assigned to CEO (2 min)
  ↓
In Progress - Scanner Bot (10-15 min)
  ↓
In Progress - Reporter Bot (5 min)
  ↓
Review - CEO Quality Gate (2 min)
  ↓
Done (20-30 min total)
```

**Check email inbox for report**

### Step 4: Verify Success (2 min)

**Email received?**
- [ ] Subject: "Security Audit Report: OWASP/NodeGoat"
- [ ] Attachment or inline report
- [ ] Contains CVE links to nvd.nist.gov
- [ ] No "TODO" or "TBD"
- [ ] At least 5 vulnerabilities listed

**Dashboard checks:**
- [ ] Task status: Done
- [ ] Costs & Budgets: <$10 spent
- [ ] All agents: Idle (no errors)

---

## ✅ Success Checklist

**Deployment complete when ALL checked:**

- [ ] VPS running 24/7 (http://[VPS_IP]:3100 accessible)
- [ ] Codex authorized (no auth errors)
- [ ] 3 agents hired (CEO, Scanner, Reporter)
- [ ] NodeGoat scan completed
- [ ] Report email received
- [ ] Budget tracking shows <$10
- [ ] All passwords in password manager

**If ANY unchecked:**
→ See DEPLOYMENT.md troubleshooting sections

---

## 🚨 Common Issues & Quick Fixes

### "Codex auth failed"
```bash
# In VPS terminal:
docker exec -it $PAPERCLIP_CONTAINER bash
openai auth login
# Repeat authorization flow
exit
```

### "Task stuck in Blocked"
1. Click task → View comments
2. Read blocker message
3. Common: GitHub token, API quota
4. Fix: Update secrets, wait for quota reset

### "Email not received"
1. Check spam folder
2. Check Resend dashboard: resend.com/logs
3. Verify email spelling in task description

### "Budget exceeded"
1. Navigate: Costs & Budgets
2. Check which agent spent most
3. Increase budget OR wait for month reset
4. Resume agent: Agent Settings → Resume

---

## 📞 Help Resources

**Stuck?**
1. Read: docs/DEPLOYMENT.md (detailed troubleshooting)
2. Check: /tmp/halugate-[date].log (on VPS)
3. Paperclip logs: `docker logs $PAPERCLIP_CONTAINER`

**Hostinger issues:**
- Support ticket: Hostinger panel
- SLA: <4 hours

**Paperclip bugs:**
- GitHub: github.com/paperclipai/paperclip/issues

---

## 🎉 After First Scan

**Celebrate first! Then:**

1. **Update anti-patterns table**
   - Any issues found? Add to skills/security-audit/SKILL.md
   - Scanner made mistakes? Document them

2. **LinkedIn post**
   - "Just deployed a zero-human security audit company"
   - Include NodeGoat scan screenshot
   - Offer 5 free beta scans

3. **Plan Week 2**
   - Recruit 5 beta customers
   - Monitor burn rate (target <$300/month)
   - Iterate on skills based on feedback

---

**Current Status:** Infrastructure ready ✅
**Next Deadline:** First scan complete by [NOW + 90 min]
**Kill Criteria:** May 3, 2026 (if no real customers by then)

**GO! 🚀**
