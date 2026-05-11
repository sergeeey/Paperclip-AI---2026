from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .artifact_gate import verify_artifacts, write_event
from .models import CheckResult, GateVerdict, IssueExecutionModel, IssueModel, VerdictStatus
from .security_gate import DEFAULT_SEMGREP_BLOCK_LEVELS, verify_security_scans


class IssueGateRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    issue_id: str
    final: GateVerdict
    gates: tuple[GateVerdict, ...]

    def to_dict(self) -> dict:
        return {
            "issue_id": self.issue_id,
            "status": self.final.status,
            "reason": self.final.reason,
            "final": self.final.to_event(),
            "gates": [gate.to_event() for gate in self.gates],
        }


def run_issue_gates(
    *,
    issue_id: str,
    project_dir: Path,
    min_tests: int = 15,
    min_coverage: float = 80.0,
    semgrep_sarif: Path | None = None,
    trufflehog_json: Path | None = None,
    run_semgrep: bool = False,
    semgrep_config: str | Path | None = None,
    run_trufflehog: bool = False,
    scan_output_dir: Path | None = None,
    semgrep_block_levels: tuple[str, ...] = DEFAULT_SEMGREP_BLOCK_LEVELS,
    block_trufflehog_unknown: bool = True,
    timeout_seconds: int = 120,
    event_log: Path | None = None,
) -> IssueGateRun:
    project_dir = Path(project_dir)
    gates: list[GateVerdict] = []

    artifact_verdict = verify_artifacts(
        issue_id=issue_id,
        project_dir=project_dir,
        min_tests=min_tests,
        min_coverage=min_coverage,
    )
    gates.append(artifact_verdict)
    _write_optional_event(artifact_verdict, event_log)

    if artifact_verdict.status != "pass":
        final = _final_verdict(
            issue_id=issue_id,
            project_dir=project_dir,
            status=artifact_verdict.status,
            reason=f"artifact gate {artifact_verdict.status}",
            gates=gates,
        )
        _write_optional_event(final, event_log)
        return IssueGateRun(issue_id=issue_id, final=final, gates=tuple(gates))

    security_verdict = verify_security_scans(
        issue_id=issue_id,
        project_dir=project_dir,
        semgrep_sarif=semgrep_sarif,
        trufflehog_json=trufflehog_json,
        run_semgrep=run_semgrep,
        semgrep_config=semgrep_config,
        run_trufflehog=run_trufflehog,
        scan_output_dir=scan_output_dir,
        semgrep_block_levels=semgrep_block_levels,
        block_trufflehog_unknown=block_trufflehog_unknown,
        timeout_seconds=timeout_seconds,
    )
    gates.append(security_verdict)
    _write_optional_event(security_verdict, event_log)

    if security_verdict.status != "pass":
        final = _final_verdict(
            issue_id=issue_id,
            project_dir=project_dir,
            status=security_verdict.status,
            reason=f"security gate {_status_verb(security_verdict.status)}",
            gates=gates,
        )
        _write_optional_event(final, event_log)
        return IssueGateRun(issue_id=issue_id, final=final, gates=tuple(gates))

    final = _final_verdict(
        issue_id=issue_id,
        project_dir=project_dir,
        status="pass",
        reason="all issue gates passed",
        gates=gates,
    )
    _write_optional_event(final, event_log)
    return IssueGateRun(issue_id=issue_id, final=final, gates=tuple(gates))


def run_issue_gates_from_issue(
    issue: IssueModel,
    *,
    issue_file: Path | None = None,
    event_log: Path | None = None,
) -> IssueGateRun:
    issue_file = Path(issue_file) if issue_file is not None else None
    base_dir = issue_file.parent if issue_file is not None else Path.cwd()
    execution = issue.execution or IssueExecutionModel()
    project_dir = _resolve_path(issue.output_location, base_dir)
    semgrep_sarif = _resolve_optional_path(
        execution.semgrep_sarif,
        base_dir,
        default=project_dir / "semgrep.sarif",
    )
    trufflehog_json = _resolve_optional_path(
        execution.trufflehog_json,
        base_dir,
        default=project_dir / "trufflehog.jsonl",
    )
    scan_output_dir = _resolve_optional_path(execution.scan_output_dir, base_dir, default=None)
    resolved_event_log = _resolve_optional_path(execution.event_log, base_dir, default=None)

    return run_issue_gates(
        issue_id=issue.issue_id,
        project_dir=project_dir,
        min_tests=execution.min_tests,
        min_coverage=execution.min_coverage,
        semgrep_sarif=semgrep_sarif,
        trufflehog_json=trufflehog_json,
        run_semgrep=execution.run_semgrep,
        semgrep_config=execution.semgrep_config,
        run_trufflehog=execution.run_trufflehog,
        scan_output_dir=scan_output_dir,
        semgrep_block_levels=tuple(execution.semgrep_block_levels),
        block_trufflehog_unknown=execution.block_trufflehog_unknown,
        timeout_seconds=execution.timeout_seconds,
        event_log=event_log or resolved_event_log,
    )


def _final_verdict(
    *,
    issue_id: str,
    project_dir: Path,
    status: VerdictStatus,
    reason: str,
    gates: list[GateVerdict],
) -> GateVerdict:
    return GateVerdict(
        issue_id=issue_id,
        project_dir=project_dir,
        status=status,
        reason=reason,
        stage="issue_gates",
        checks=tuple(_gate_check(gate) for gate in gates),
    )


def _gate_check(gate: GateVerdict) -> CheckResult:
    return CheckResult(
        name=gate.stage,
        status=gate.status,
        message=gate.reason,
        observed={
            "status": gate.status,
            "reason": gate.reason,
            "check_count": len(gate.checks),
        },
    )


def _write_optional_event(verdict: GateVerdict, event_log: Path | None) -> None:
    if event_log is None:
        return
    write_event(verdict, Path(event_log))


def _status_verb(status: VerdictStatus) -> str:
    if status == "pass":
        return "passed"
    if status == "fail":
        return "failed"
    return "blocked"


def _resolve_path(value: str, base_dir: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base_dir / path).resolve(strict=False)


def _resolve_optional_path(value: str | None, base_dir: Path, *, default: Path | None) -> Path | None:
    if value is None:
        return default
    return _resolve_path(value, base_dir)
