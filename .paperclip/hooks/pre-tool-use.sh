#!/bin/bash
#
# HaluGate Pipeline: Sentinel → Detector → Explainer
# Pre-Tool-Use Hook for Paperclip Agents
#
# Purpose: Block hallucinated commands before execution
# - Prevents deletion of nonexistent paths (rm -rf hallucination)
# - Prevents calls to nonexistent API endpoints (curl hallucination)
# - Prevents execution with undefined/empty variables
#
# Exit Codes:
# 0 = PASS (command safe to execute)
# 1 = BLOCK (hallucination detected, abort)
#
# Usage: Paperclip calls this before every Bash tool execution
# Input: $1 = full command string
#

set -euo pipefail

COMMAND="$1"
LOG_FILE="/tmp/halugate-$(date +%Y%m%d).log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🔍 HaluGate Sentinel: Inspecting command: $COMMAND"

# ============================================================================
# DETECTOR 1: Destructive commands with nonexistent paths
# ============================================================================

if [[ "$COMMAND" == *"rm -rf"* ]] || [[ "$COMMAND" == *"rm -fr"* ]]; then
    log "⚠️  Detector 1: Destructive deletion detected"

    # Extract path being deleted
    # Handle variations: rm -rf PATH, rm -rf "PATH", rm -rf $VAR
    PATH_TO_DELETE=$(echo "$COMMAND" | sed -n 's/.*rm -r[f]*\s*\([^ ]*\).*/\1/p' | sed 's/"//g')

    # Check for empty/undefined variable
    if [[ -z "$PATH_TO_DELETE" ]] || [[ "$PATH_TO_DELETE" == "\$"* ]]; then
        log "🚫 BLOCKED: rm -rf with undefined/empty path variable"
        log "   Command: $COMMAND"
        log "   Reason: Would delete unexpected locations"
        log "   Action: Define variable explicitly before deletion"
        exit 1
    fi

    # Check if path exists
    if [ ! -e "$PATH_TO_DELETE" ]; then
        log "🚫 BLOCKED: rm -rf target does not exist"
        log "   Command: $COMMAND"
        log "   Path: $PATH_TO_DELETE"
        log "   Reason: Attempting to delete hallucinated path"
        log "   Action: Verify path with 'ls' before deletion"
        exit 1
    fi

    # Additional safety: Prevent deletion of critical system paths
    CRITICAL_PATHS=("/" "/bin" "/usr" "/etc" "/var" "/home" "/root")
    for CRITICAL in "${CRITICAL_PATHS[@]}"; do
        if [[ "$PATH_TO_DELETE" == "$CRITICAL" ]] || [[ "$PATH_TO_DELETE" == "${CRITICAL}/"* ]]; then
            log "🚫 BLOCKED: Attempted deletion of critical system path"
            log "   Command: $COMMAND"
            log "   Path: $PATH_TO_DELETE"
            log "   Reason: Would damage system"
            log "   Action: NEVER delete system directories"
            exit 1
        fi
    done

    log "✅ Detector 1: Path exists and is safe to delete"
fi

# ============================================================================
# DETECTOR 2: API Endpoint Hallucinations
# ============================================================================

if [[ "$COMMAND" == *"curl"* ]] && [[ "$COMMAND" != *"curl -I"* ]] && [[ "$COMMAND" != *"curl --head"* ]]; then
    log "⚠️  Detector 2: API call detected"

    # Extract URL from curl command
    # Handle variations: curl URL, curl "URL", curl -X POST URL, curl -H "..." URL
    URL=$(echo "$COMMAND" | grep -oP 'https?://[^\s"]+' | head -1)

    if [[ -z "$URL" ]]; then
        log "⚠️  Warning: Could not extract URL from curl command"
        log "   Command: $COMMAND"
        log "   Proceeding without verification (may be complex curl)"
    else
        log "   Verifying endpoint: $URL"

        # HEAD request to check if endpoint exists (timeout 5s)
        HTTP_CODE=$(curl -I -s -o /dev/null -w "%{http_code}" --max-time 5 "$URL" 2>/dev/null || echo "000")

        if [[ "$HTTP_CODE" == "000" ]]; then
            log "🚫 BLOCKED: API endpoint unreachable"
            log "   Command: $COMMAND"
            log "   URL: $URL"
            log "   Reason: Connection failed (timeout or DNS resolution failure)"
            log "   Action: Verify URL spelling, check network connectivity"
            exit 1
        elif [[ "$HTTP_CODE" == "404" ]]; then
            log "🚫 BLOCKED: API endpoint returns 404 Not Found"
            log "   Command: $COMMAND"
            log "   URL: $URL"
            log "   Reason: Endpoint does not exist (hallucinated URL)"
            log "   Action: Verify API documentation, check URL path"
            exit 1
        elif [[ "$HTTP_CODE" == "5"* ]]; then
            log "⚠️  Warning: API endpoint returns 5xx server error (HTTP $HTTP_CODE)"
            log "   URL: $URL"
            log "   Proceeding anyway (server issue, not hallucination)"
        else
            log "✅ Detector 2: Endpoint reachable (HTTP $HTTP_CODE)"
        fi
    fi
fi

# ============================================================================
# DETECTOR 3: CVE Verification (NIST API specific)
# ============================================================================

# Special handling for NIST CVE verification
if [[ "$COMMAND" == *"services.nvd.nist.gov"* ]]; then
    log "⚠️  Detector 3: NIST CVE verification detected"

    # Extract CVE ID from command
    CVE_ID=$(echo "$COMMAND" | grep -oP 'CVE-\d{4}-\d{4,7}')

    if [[ -z "$CVE_ID" ]]; then
        log "⚠️  Warning: NIST query without CVE ID pattern"
        log "   Command: $COMMAND"
        log "   Proceeding (may be other NIST API usage)"
    else
        # Validate CVE ID format
        if [[ ! "$CVE_ID" =~ ^CVE-[0-9]{4}-[0-9]{4,7}$ ]]; then
            log "🚫 BLOCKED: Invalid CVE ID format"
            log "   Command: $COMMAND"
            log "   CVE ID: $CVE_ID"
            log "   Reason: CVE IDs must match CVE-YYYY-NNNNN format"
            log "   Action: Verify CVE ID from semgrep output"
            exit 1
        fi

        log "✅ Detector 3: CVE ID format valid ($CVE_ID)"
    fi
fi

# ============================================================================
# DETECTOR 4: Git Destructive Operations
# ============================================================================

DESTRUCTIVE_GIT_OPS=("git reset --hard" "git clean -fd" "git push --force" "git branch -D")

for GIT_OP in "${DESTRUCTIVE_GIT_OPS[@]}"; do
    if [[ "$COMMAND" == *"$GIT_OP"* ]]; then
        log "⚠️  Detector 4: Destructive git operation detected"
        log "   Operation: $GIT_OP"
        log "   Command: $COMMAND"

        # Check if Execution Policy should block this
        # (In production, this would query Paperclip Execution Policy API)
        # For now, log warning and allow (Board can configure blocking via Paperclip UI)

        log "⚠️  WARNING: Destructive git operation requires careful review"
        log "   Proceeding (configure Execution Policy in Paperclip to block)"
        # Uncomment to block all destructive git ops:
        # exit 1
    fi
done

# ============================================================================
# DETECTOR 5: Undefined Variable Usage
# ============================================================================

# Check for common patterns of undefined variable usage
if [[ "$COMMAND" == *'$'* ]]; then
    log "⚠️  Detector 5: Variable usage detected"

    # Extract variable names (simplified - catches $VAR, not ${VAR})
    VARS=$(echo "$COMMAND" | grep -oP '\$[A-Za-z_][A-Za-z0-9_]*' | sort -u)

    for VAR in $VARS; do
        VAR_NAME="${VAR#\$}"  # Remove $ prefix

        # Check if variable is set in current environment
        # Note: This only works for exported variables in hook's shell
        # Agent's shell has separate environment
        if [[ -z "${!VAR_NAME:-}" ]]; then
            log "⚠️  Warning: Variable $VAR appears undefined in hook environment"
            log "   Command: $COMMAND"
            log "   Note: Agent shell may have it defined (proceeding)"
            # Don't block - agent may have defined it in their session
        fi
    done
fi

# ============================================================================
# DETECTOR 6: Email/Report Delivery (Resend API)
# ============================================================================

if [[ "$COMMAND" == *"resend"* ]] || [[ "$COMMAND" == *"sendmail"* ]]; then
    log "⚠️  Detector 6: Email delivery detected"

    # Check if this is final report delivery (should have CEO approval)
    # This is a placeholder - real implementation would check Paperclip task status
    log "   Note: Verify CEO quality gate passed before delivery"
    log "   Proceeding (Execution Policy should require approval)"
fi

# ============================================================================
# DETECTOR 7: Customer Data Handling
# ============================================================================

if [[ "$COMMAND" == *"/customer-data/"* ]] || [[ "$COMMAND" == *"customer_"* ]]; then
    log "⚠️  Detector 7: Customer data access detected"

    # Ensure customer data is not persisted permanently
    if [[ "$COMMAND" == *"cp "* ]] || [[ "$COMMAND" == *"mv "* ]]; then
        DEST=$(echo "$COMMAND" | awk '{print $NF}')
        if [[ "$DEST" != "/tmp/"* ]]; then
            log "🚫 BLOCKED: Customer data being copied outside /tmp/"
            log "   Command: $COMMAND"
            log "   Destination: $DEST"
            log "   Reason: Customer code must be ephemeral (GDPR compliance)"
            log "   Action: Use /tmp/ for all customer data storage"
            exit 1
        fi
    fi
fi

# ============================================================================
# ALL DETECTORS PASSED
# ============================================================================

log "✅ HaluGate: All checks passed, command safe to execute"
exit 0
