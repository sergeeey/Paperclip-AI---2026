# Workflow Controller

Small deterministic gates for the Paperclip autonomous development pipeline.

## Schemas

The controller uses Pydantic models as the executable source of truth for:

- `IssueModel`
- `IssueExecutionModel`
- `GateVerdict`
- `EventModel`
- `CheckResult`
- `ToolPolicy`
- `PolicyDecision`

Export JSON Schemas for Paperclip/HaluGate validation hooks:

```powershell
python -m workflow_controller.cli export-schemas --output-dir ..\..\.paperclip\schemas
```

## MCP Tool Policy

The MCP wrapper exposes deterministic workflow tools behind a policy layer:

- `workflow_run_issue_gates`
- `workflow_plan_issue_flow`
- `workflow_sync_issue_state`
- `workflow_verify_artifacts`
- `workflow_verify_security`
- `workflow_export_schemas`

The default policy:

- allows only the workflow-controller tools above
- blocks unknown tool names
- checks filesystem arguments against allowed roots
- supports an explicit `require_approval_tools` list

Run the MCP server over stdio:

```powershell
$env:PYTHONPATH='tools\workflow-controller'
python -m workflow_controller.mcp_tools
```

## Artifact Gate

`verify-artifacts` checks a Builder output directory before an issue can move to
Scanner or DevOps.

Default target:

```text
/tmp/projects/{issue_id}/
```

Required artifacts:

- `test-results.json` with `summary.passed` and `summary.failed`
- `coverage.xml` with root `line-rate`
- `README.md` with install, run, and test guidance

Verdicts:

- `pass` - all checks passed
- `fail` - artifacts exist, but tests, coverage, or README validation failed
- `blocked` - required directory or artifacts are missing

## Usage

From this directory:

```powershell
python -m workflow_controller.cli verify-artifacts BLI-2 --project-dir C:\tmp\BLI-2 --json
```

Append a JSONL event log:

```powershell
python -m workflow_controller.cli verify-artifacts BLI-2 --event-log .\events.jsonl
```

## Issue Gate Runner

`run-issue-gates` is the issue-level pipeline command. It runs:

1. artifact gate
2. security gate, only if artifact gate passes
3. final `issue_gates` verdict

Each executed gate and the final verdict can be appended to one JSONL event log.

```powershell
python -m workflow_controller.cli run-issue-gates BLI-2 `
  --project-dir C:\tmp\BLI-2 `
  --semgrep-sarif C:\tmp\BLI-2\semgrep.sarif `
  --trufflehog-json C:\tmp\BLI-2\trufflehog.jsonl `
  --event-log C:\tmp\BLI-2\events.jsonl `
  --json
```

`run-issue-gates-from-issue` loads a strict issue JSON file, resolves relative
paths from that file, and uses `IssueExecutionModel` defaults when execution
hints are omitted.

```powershell
python -m workflow_controller.cli run-issue-gates-from-issue `
  --issue-file .\tests\fixtures\issues\clean-issue.json `
  --json
```

`verify-event-log` validates JSONL stage order and verdict consistency.

```powershell
python -m workflow_controller.cli verify-event-log `
  --event-log C:\tmp\BLI-2\events.jsonl `
  --expected-issue-id BLI-2
```

`sync-issue-state` runs the issue gates and writes the updated structured issue
artifact back to disk.

```powershell
python -m workflow_controller.cli sync-issue-state `
  --issue-file .\tests\fixtures\issues\clean-issue.json `
  --output-file C:\tmp\BLI-2\issue.json `
  --event-log C:\tmp\BLI-2\events.jsonl `
  --json
```

`plan-issue-flow` turns a strict issue JSON file into a deterministic
CEO→Builder→Scanner→Reporter→DevOps plan.

```powershell
python -m workflow_controller.cli plan-issue-flow `
  --issue-file .\tests\fixtures\issues\clean-issue.json `
  --json
```

## Security Gate

`verify-security` validates Scanner outputs before deployment/reporting.

Supported inputs:

- Semgrep SARIF 2.1.0
- TruffleHog JSONL

Validate existing scanner artifacts:

```powershell
python -m workflow_controller.cli verify-security BLI-2 `
  --project-dir C:\tmp\BLI-2 `
  --semgrep-sarif C:\tmp\BLI-2\semgrep.sarif `
  --trufflehog-json C:\tmp\BLI-2\trufflehog.jsonl `
  --json
```

Run Semgrep through the gate and write SARIF under
`{project_dir}\.paperclip-security\`:

```powershell
python -m workflow_controller.cli verify-security BLI-2 `
  --project-dir C:\tmp\BLI-2 `
  --run-semgrep `
  --semgrep-config auto
```

Run TruffleHog if the `trufflehog` binary is available:

```powershell
python -m workflow_controller.cli verify-security BLI-2 `
  --project-dir C:\tmp\BLI-2 `
  --run-trufflehog
```

Missing scanner binaries or missing security artifacts produce `blocked`, not a
false pass.

When TruffleHog is run by the controller, raw secret-like fields are redacted
before the JSONL artifact is written.

Exit codes:

- `0` pass
- `2` fail
- `3` blocked

## Tests

```powershell
python -m unittest discover -s tests
```
