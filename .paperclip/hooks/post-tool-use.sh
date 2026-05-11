#!/bin/bash
#
# HaluGate Post-Tool-Use Hook
# Verifies tool execution results and enforces TDD workflow
#
# Purpose:
# - Verify tool execution produced expected output
# - Enforce Test-Driven Development (Red → Green → Refactor)
# - Block progression to next task if tests fail
#
# Exit Codes:
# 0 = PASS (result verified, proceed)
# 1 = BLOCK (verification failed, do NOT mark task done)
#
# Usage: Paperclip calls this after every tool execution
# Input:
#   $1 = tool name (e.g., "bash", "python", "semgrep")
#   $2 = exit code from tool
#   $3 = stdout (truncated if >1KB)
#   $4 = stderr (truncated if >1KB)
#

set -euo pipefail

TOOL_NAME="$1"
EXIT_CODE="${2:-0}"
STDOUT="${3:-}"
STDERR="${4:-}"
LOG_FILE="/tmp/halugate-post-$(date +%Y%m%d).log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🔍 HaluGate Post-Verification: Tool=$TOOL_NAME, Exit=$EXIT_CODE"

# ============================================================================
# VERIFIER 1: Test Execution (TDD Enforcement)
# ============================================================================

if [[ "$TOOL_NAME" == "pytest" ]] || [[ "$TOOL_NAME" == "npm test" ]] || [[ "$TOOL_NAME" == "jest" ]]; then
    log "⚠️  Verifier 1: Test execution detected"

    if [[ "$EXIT_CODE" != "0" ]]; then
        log "🚫 BLOCKED: Tests failed (exit code $EXIT_CODE)"
        log "   Tool: $TOOL_NAME"
        log "   Stderr: $STDERR"
        log ""
        log "   TDD Protocol Violation: Cannot proceed to next task with failing tests"
        log "   Required Actions:"
        log "     1. Read the full stack trace (stderr)"
        log "     2. Identify root cause of failure"
        log "     3. Fix the code (do NOT modify tests to pass)"
        log "     4. Re-run tests until they pass"
        log "     5. ONLY THEN mark task as done"
        log ""
        log "   Reminder: A failing test means the CODE is broken, not the test"
        exit 1
    else
        log "✅ Verifier 1: All tests passed"

        # Extract test count if available
        if [[ "$STDOUT" == *"passed"* ]]; then
            TEST_COUNT=$(echo "$STDOUT" | grep -oP '\d+(?= passed)' | head -1)
            log "   Tests passed: $TEST_COUNT"
        fi
    fi
fi

# ============================================================================
# VERIFIER 2: Semgrep Security Scan
# ============================================================================

if [[ "$TOOL_NAME" == "semgrep" ]]; then
    log "⚠️  Verifier 2: Security scan result verification"

    if [[ "$EXIT_CODE" != "0" ]] && [[ "$EXIT_CODE" != "1" ]]; then
        # semgrep returns 1 when findings detected (expected)
        # Returns >1 for actual errors
        log "🚫 BLOCKED: Semgrep execution error (exit code $EXIT_CODE)"
        log "   Stderr: $STDERR"
        log "   Action: Check semgrep syntax, verify ruleset exists"
        exit 1
    fi

    # Verify JSON output is valid
    if [[ "$STDOUT" == "{"* ]]; then
        # Attempt to parse JSON
        if ! echo "$STDOUT" | jq . > /dev/null 2>&1; then
            log "🚫 BLOCKED: Semgrep output is not valid JSON"
            log "   Action: Re-run semgrep with --json flag"
            exit 1
        fi

        FINDING_COUNT=$(echo "$STDOUT" | jq '.results | length' 2>/dev/null || echo "unknown")
        log "✅ Verifier 2: Semgrep output valid (findings: $FINDING_COUNT)"
    else
        log "⚠️  Warning: Semgrep output is not JSON (may be formatted for terminal)"
        log "   Proceeding (verify --json flag was used)"
    fi
fi

# ============================================================================
# VERIFIER 3: NIST CVE API Response
# ============================================================================

if [[ "$STDOUT" == *"nvd.nist.gov"* ]] || [[ "$STDERR" == *"nvd.nist.gov"* ]]; then
    log "⚠️  Verifier 3: NIST CVE API response verification"

    # Check for rate limiting (HTTP 429)
    if [[ "$STDERR" == *"429"* ]] || [[ "$STDOUT" == *"429"* ]]; then
        log "🚫 BLOCKED: NIST API rate limit exceeded (HTTP 429)"
        log "   Action: Wait 30 seconds and retry"
        log "   Note: Consider getting NIST API key for higher limits"
        exit 1
    fi

    # Check for API downtime (HTTP 503)
    if [[ "$STDERR" == *"503"* ]] || [[ "$STDOUT" == *"503"* ]]; then
        log "⚠️  Warning: NIST API temporarily unavailable (HTTP 503)"
        log "   Action: Mark findings as [PENDING_VERIFICATION], retry later"
        log "   Proceeding (non-blocking, fallback allowed)"
    fi

    # Verify JSON response
    if echo "$STDOUT" | jq . > /dev/null 2>&1; then
        RESULTS=$(echo "$STDOUT" | jq -r '.resultsPerPage' 2>/dev/null || echo "unknown")
        if [[ "$RESULTS" == "0" ]]; then
            log "✅ Verifier 3: CVE not found in NIST (expected for some findings)"
            log "   Action: Mark finding as [HYPOTHESIS] in report"
        elif [[ "$RESULTS" == "1" ]]; then
            log "✅ Verifier 3: CVE verified in NIST database"
        else
            log "   NIST response: resultsPerPage=$RESULTS"
        fi
    fi
fi

# ============================================================================
# VERIFIER 4: Git Operations
# ============================================================================

if [[ "$TOOL_NAME" == "git" ]]; then
    log "⚠️  Verifier 4: Git operation result verification"

    if [[ "$EXIT_CODE" != "0" ]]; then
        log "🚫 BLOCKED: Git operation failed (exit code $EXIT_CODE)"
        log "   Stderr: $STDERR"

        # Specific error patterns
        if [[ "$STDERR" == *"conflict"* ]]; then
            log "   Reason: Merge conflict detected"
            log "   Action: Resolve conflicts manually, then retry"
        elif [[ "$STDERR" == *"Permission denied"* ]]; then
            log "   Reason: Permission denied (SSH key or token issue)"
            log "   Action: Verify GitHub token is valid"
        elif [[ "$STDERR" == *"fatal: not a git repository"* ]]; then
            log "   Reason: Not a git repository"
            log "   Action: Run 'git init' first or check working directory"
        else
            log "   Generic git error, check stderr for details"
        fi

        exit 1
    else
        log "✅ Verifier 4: Git operation successful"
    fi
fi

# ============================================================================
# VERIFIER 5: File Creation/Modification
# ============================================================================

if [[ "$TOOL_NAME" == "write" ]] || [[ "$TOOL_NAME" == "edit" ]]; then
    log "⚠️  Verifier 5: File operation verification"

    # Extract filename from stdout (assuming format: "File created: /path/to/file")
    FILENAME=$(echo "$STDOUT" | grep -oP '(?<= )(/[^ ]+)' | head -1)

    if [[ -n "$FILENAME" ]] && [[ -f "$FILENAME" ]]; then
        FILESIZE=$(stat -f%z "$FILENAME" 2>/dev/null || stat -c%s "$FILENAME" 2>/dev/null || echo "unknown")
        log "✅ Verifier 5: File created successfully"
        log "   Path: $FILENAME"
        log "   Size: $FILESIZE bytes"

        # Check for empty files (potential error)
        if [[ "$FILESIZE" == "0" ]]; then
            log "⚠️  Warning: File is empty (0 bytes)"
            log "   Action: Verify this is intentional"
        fi
    else
        log "   Note: Could not verify file creation (path not detected in output)"
    fi
fi

# ============================================================================
# VERIFIER 6: Placeholder Detection
# ============================================================================

# Check output for common placeholders that indicate incomplete work
PLACEHOLDERS=("TODO" "TBD" "FIXME" "XXX" "Lorem ipsum" "placeholder" "CHANGEME")

for PLACEHOLDER in "${PLACEHOLDERS[@]}"; do
    if [[ "$STDOUT" == *"$PLACEHOLDER"* ]]; then
        log "🚫 BLOCKED: Placeholder detected in output: $PLACEHOLDER"
        log "   Tool: $TOOL_NAME"
        log "   Output contains: $PLACEHOLDER"
        log ""
        log "   Quality Gate Violation: Incomplete work detected"
        log "   Action: Replace all placeholders with actual content"
        log "   Do NOT mark task as done with placeholders present"
        exit 1
    fi
done

# ============================================================================
# VERIFIER 7: API Key Leakage Detection
# ============================================================================

# Patterns that might be API keys/secrets
SECRET_PATTERNS=("sk-" "api_key=" "apiKey:" "API_KEY=" "token=" "password=")

for PATTERN in "${SECRET_PATTERNS[@]}"; do
    if [[ "$STDOUT" == *"$PATTERN"* ]] || [[ "$STDERR" == *"$PATTERN"* ]]; then
        log "🚨 SECURITY ALERT: Potential API key detected in output"
        log "   Pattern: $PATTERN"
        log "   Tool: $TOOL_NAME"
        log ""
        log "   CRITICAL: Secret may have been leaked in logs"
        log "   Immediate Actions:"
        log "     1. Check if this is actual secret or false positive"
        log "     2. If real: ROTATE the key immediately"
        log "     3. Remove from logs: rm $LOG_FILE"
        log "     4. Update code to use environment variables"
        log ""
        log "   Proceeding (manual review required)"
        # Don't block - just alert (false positives common)
    fi
done

# ============================================================================
# ALL VERIFIERS PASSED
# ============================================================================

log "✅ HaluGate Post-Verification: All checks passed"
exit 0
