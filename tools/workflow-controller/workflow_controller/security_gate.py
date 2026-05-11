from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .models import CheckResult, GateVerdict

DEFAULT_SEMGREP_BLOCK_LEVELS = ("error", "warning")


def verify_security_scans(
    *,
    issue_id: str,
    project_dir: Path,
    semgrep_sarif: Path | None = None,
    trufflehog_json: Path | None = None,
    run_semgrep: bool = False,
    semgrep_config: str | Path | None = None,
    run_trufflehog: bool = False,
    scan_output_dir: Path | None = None,
    semgrep_block_levels: tuple[str, ...] = DEFAULT_SEMGREP_BLOCK_LEVELS,
    block_trufflehog_unknown: bool = True,
    timeout_seconds: int = 120,
) -> GateVerdict:
    project_dir = Path(project_dir)
    checks: list[CheckResult] = []

    if not project_dir.is_dir():
        return GateVerdict(
            issue_id=issue_id,
            project_dir=project_dir,
            status="blocked",
            reason="project directory missing",
            stage="security_gate",
            checks=(
                CheckResult(
                    name="project_dir",
                    status="blocked",
                    message=f"directory not found: {project_dir}",
                ),
            ),
        )

    checks.append(
        CheckResult(
            name="project_dir",
            status="pass",
            message=f"directory exists: {project_dir}",
        )
    )

    if run_semgrep or run_trufflehog:
        scan_output_dir = Path(scan_output_dir) if scan_output_dir else project_dir / ".paperclip-security"
        scan_output_dir.mkdir(parents=True, exist_ok=True)

    if run_semgrep:
        semgrep_sarif = Path(semgrep_sarif) if semgrep_sarif else scan_output_dir / "semgrep.sarif"
        checks.append(
            _run_semgrep(
                project_dir=project_dir,
                output_path=semgrep_sarif,
                semgrep_config=semgrep_config or "auto",
                timeout_seconds=timeout_seconds,
            )
        )

    if run_trufflehog:
        trufflehog_json = (
            Path(trufflehog_json) if trufflehog_json else scan_output_dir / "trufflehog.jsonl"
        )
        checks.append(
            _run_trufflehog(
                project_dir=project_dir,
                output_path=trufflehog_json,
                timeout_seconds=timeout_seconds,
            )
        )

    if semgrep_sarif is None and trufflehog_json is None:
        checks.append(
            CheckResult(
                name="security_artifacts",
                status="blocked",
                message="no security scan artifacts configured",
            )
        )
    else:
        if semgrep_sarif is not None:
            checks.append(
                _check_semgrep_sarif(
                    Path(semgrep_sarif),
                    block_levels={level.lower() for level in semgrep_block_levels},
                )
            )
        if trufflehog_json is not None:
            checks.append(
                _check_trufflehog_jsonl(
                    Path(trufflehog_json),
                    block_unknown=block_trufflehog_unknown,
                )
            )

    if any(check.status == "blocked" for check in checks):
        return GateVerdict(
            issue_id=issue_id,
            project_dir=project_dir,
            status="blocked",
            reason="security scans blocked",
            stage="security_gate",
            checks=tuple(checks),
        )

    if any(check.status == "fail" for check in checks):
        return GateVerdict(
            issue_id=issue_id,
            project_dir=project_dir,
            status="fail",
            reason="security scan checks failed",
            stage="security_gate",
            checks=tuple(checks),
        )

    return GateVerdict(
        issue_id=issue_id,
        project_dir=project_dir,
        status="pass",
        reason="all security checks passed",
        stage="security_gate",
        checks=tuple(checks),
    )


def _run_semgrep(
    *,
    project_dir: Path,
    output_path: Path,
    semgrep_config: str | Path,
    timeout_seconds: int,
) -> CheckResult:
    executable = shutil.which("semgrep")
    if executable is None:
        return CheckResult(
            name="semgrep.run",
            status="blocked",
            message="semgrep executable not found in PATH",
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        executable,
        "scan",
        "--metrics=off",
        "--config",
        str(semgrep_config),
        "--sarif",
        "--sarif-output",
        str(output_path),
        str(project_dir),
    ]

    completed = _run_command(command, timeout_seconds=timeout_seconds)
    observed = {
        "returncode": completed.returncode,
        "output_path": str(output_path),
    }

    if not output_path.is_file():
        return CheckResult(
            name="semgrep.run",
            status="blocked",
            message="semgrep did not produce SARIF output",
            observed=observed,
        )

    status = "pass" if completed.returncode == 0 else "fail"
    return CheckResult(
        name="semgrep.run",
        status=status,
        message=f"semgrep completed with exit code {completed.returncode}",
        observed=observed,
    )


def _run_trufflehog(
    *,
    project_dir: Path,
    output_path: Path,
    timeout_seconds: int,
) -> CheckResult:
    executable = shutil.which("trufflehog")
    if executable is None:
        return CheckResult(
            name="trufflehog.run",
            status="blocked",
            message="trufflehog executable not found in PATH",
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        executable,
        "filesystem",
        str(project_dir),
        "--results=verified,unknown",
        "--json",
    ]
    completed = _run_command(command, timeout_seconds=timeout_seconds)
    output_path.write_text(_sanitize_trufflehog_jsonl(completed.stdout), encoding="utf-8")

    observed = {
        "returncode": completed.returncode,
        "output_path": str(output_path),
    }
    status = "pass" if completed.returncode == 0 else "fail"
    return CheckResult(
        name="trufflehog.run",
        status=status,
        message=f"trufflehog completed with exit code {completed.returncode}",
        observed=observed,
    )


def _run_command(command: list[str], *, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            check=False,
            shell=False,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(command, returncode=124, stdout="", stderr="timeout")


def _sanitize_trufflehog_jsonl(raw_output: str) -> str:
    sanitized_lines: list[str] = []
    for line_number, line in enumerate(raw_output.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = {"ParseError": "invalid trufflehog JSON output", "LineNumber": line_number}
        sanitized_lines.append(json.dumps(_redact_secret_fields(payload), sort_keys=True))

    if not sanitized_lines:
        return ""
    return "\n".join(sanitized_lines) + "\n"


def _redact_secret_fields(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            if _is_sensitive_key(key):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = _redact_secret_fields(child)
        return redacted
    if isinstance(value, list):
        return [_redact_secret_fields(item) for item in value]
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in {
        "raw",
        "rawv2",
        "secret",
        "token",
        "password",
        "api_key",
        "apikey",
        "access_key",
        "private_key",
    }


def _check_semgrep_sarif(path: Path, *, block_levels: set[str]) -> CheckResult:
    if not path.is_file():
        return CheckResult(
            name="semgrep.sarif",
            status="blocked",
            message=f"artifact missing: {path}",
            observed={"path": str(path)},
        )

    payload = _read_json(path, artifact_name="semgrep.sarif")
    if isinstance(payload, CheckResult):
        return payload

    if payload.get("version") != "2.1.0":
        return CheckResult(
            name="semgrep.sarif",
            status="fail",
            message="SARIF version must be 2.1.0",
            observed={"version": payload.get("version")},
        )

    runs = payload.get("runs")
    if not isinstance(runs, list):
        return CheckResult(
            name="semgrep.sarif",
            status="fail",
            message="SARIF payload missing runs list",
        )

    results: list[dict[str, Any]] = []
    for run in runs:
        if isinstance(run, dict) and isinstance(run.get("results"), list):
            results.extend(result for result in run["results"] if isinstance(result, dict))

    blocking = [
        result
        for result in results
        if str(result.get("level", "warning")).lower() in block_levels
    ]
    observed = {
        "total_results": len(results),
        "blocking_results": len(blocking),
        "block_levels": sorted(block_levels),
        "rule_ids": _rule_ids(blocking),
    }

    if blocking:
        return CheckResult(
            name="semgrep.sarif",
            status="fail",
            message=f"semgrep reported {len(blocking)} blocking finding(s)",
            observed=observed,
        )

    return CheckResult(
        name="semgrep.sarif",
        status="pass",
        message="semgrep SARIF has no blocking findings",
        observed=observed,
    )


def _check_trufflehog_jsonl(path: Path, *, block_unknown: bool) -> CheckResult:
    if not path.is_file():
        return CheckResult(
            name="trufflehog.jsonl",
            status="blocked",
            message=f"artifact missing: {path}",
            observed={"path": str(path)},
        )

    total_results = 0
    verified_results = 0
    unknown_results = 0

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            return CheckResult(
                name="trufflehog.jsonl",
                status="fail",
                message=f"invalid JSONL at line {line_number}: {exc.msg}",
            )

        total_results += 1
        if payload.get("Verified") is True:
            verified_results += 1
        else:
            unknown_results += 1

    observed = {
        "total_results": total_results,
        "verified_results": verified_results,
        "unknown_results": unknown_results,
        "block_unknown": block_unknown,
    }

    if verified_results > 0 or (block_unknown and unknown_results > 0):
        return CheckResult(
            name="trufflehog.jsonl",
            status="fail",
            message="trufflehog reported secret findings",
            observed=observed,
        )

    return CheckResult(
        name="trufflehog.jsonl",
        status="pass",
        message="trufflehog JSONL has no blocking secret findings",
        observed=observed,
    )


def _read_json(path: Path, *, artifact_name: str) -> dict[str, Any] | CheckResult:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return CheckResult(
            name=artifact_name,
            status="fail",
            message=f"invalid JSON: {exc.msg}",
        )

    if not isinstance(payload, dict):
        return CheckResult(
            name=artifact_name,
            status="fail",
            message="JSON artifact must be an object",
        )

    return payload


def _rule_ids(results: list[dict[str, Any]], *, limit: int = 10) -> list[str]:
    rule_ids: list[str] = []
    for result in results:
        rule_id = result.get("ruleId")
        if isinstance(rule_id, str) and rule_id not in rule_ids:
            rule_ids.append(rule_id)
        if len(rule_ids) >= limit:
            break
    return rule_ids
