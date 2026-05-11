from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .models import CheckResult, GateVerdict


def verify_artifacts(
    *,
    issue_id: str,
    project_dir: Path,
    min_tests: int = 15,
    min_coverage: float = 80.0,
) -> GateVerdict:
    project_dir = Path(project_dir)

    if not project_dir.is_dir():
        return GateVerdict(
            issue_id=issue_id,
            project_dir=project_dir,
            status="blocked",
            reason="project directory missing",
            checks=(
                CheckResult(
                    name="project_dir",
                    status="blocked",
                    message=f"directory not found: {project_dir}",
                ),
            ),
        )

    checks: list[CheckResult] = [
        CheckResult(
            name="project_dir",
            status="pass",
            message=f"directory exists: {project_dir}",
        )
    ]

    required_files = ("test-results.json", "coverage.xml", "README.md")
    missing_required = False
    for filename in required_files:
        artifact = project_dir / filename
        if not artifact.is_file():
            missing_required = True
            checks.append(
                CheckResult(
                    name=filename,
                    status="blocked",
                    message=f"artifact missing: {artifact}",
                    observed={"path": str(artifact)},
                )
            )

    if missing_required:
        return GateVerdict(
            issue_id=issue_id,
            project_dir=project_dir,
            status="blocked",
            reason="required artifact missing",
            checks=tuple(checks),
        )

    checks.extend(
        (
            _check_test_results(project_dir / "test-results.json", min_tests),
            _check_coverage(project_dir / "coverage.xml", min_coverage),
            _check_readme(project_dir / "README.md"),
        )
    )

    if any(check.status == "fail" for check in checks):
        return GateVerdict(
            issue_id=issue_id,
            project_dir=project_dir,
            status="fail",
            reason="artifact checks failed",
            checks=tuple(checks),
        )

    return GateVerdict(
        issue_id=issue_id,
        project_dir=project_dir,
        status="pass",
        reason="all artifact checks passed",
        checks=tuple(checks),
    )


def write_event(verdict: GateVerdict, event_log: Path) -> None:
    event_log = Path(event_log)
    event_log.parent.mkdir(parents=True, exist_ok=True)
    with event_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(verdict.to_event(), sort_keys=True))
        handle.write("\n")


def _check_test_results(path: Path, min_tests: int) -> CheckResult:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return CheckResult(
            name="test-results.json",
            status="fail",
            message=f"invalid JSON: {exc.msg}",
        )

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return CheckResult(
            name="test-results.json",
            status="fail",
            message="missing summary object",
        )

    passed = _as_int(summary.get("passed"))
    failed = _as_int(summary.get("failed"), default=0)

    if passed is None:
        return CheckResult(
            name="test-results.json",
            status="fail",
            message="summary.passed is missing or not an integer",
        )

    observed = {"passed": passed, "failed": failed, "min_tests": min_tests}

    if failed > 0:
        return CheckResult(
            name="test-results.json",
            status="fail",
            message=f"test failures present: passed={passed} failed={failed}",
            observed=observed,
        )

    if passed < min_tests:
        return CheckResult(
            name="test-results.json",
            status="fail",
            message=f"not enough passing tests: passed={passed} min_tests={min_tests}",
            observed=observed,
        )

    return CheckResult(
        name="test-results.json",
        status="pass",
        message=f"tests passed: passed={passed} failed={failed}",
        observed=observed,
    )


def _check_coverage(path: Path, min_coverage: float) -> CheckResult:
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError as exc:
        return CheckResult(
            name="coverage.xml",
            status="fail",
            message=f"invalid XML: {exc}",
        )

    line_rate_raw = root.get("line-rate")
    if line_rate_raw is None:
        return CheckResult(
            name="coverage.xml",
            status="fail",
            message="missing coverage line-rate",
        )

    try:
        coverage_percent = float(line_rate_raw) * 100.0
    except ValueError:
        return CheckResult(
            name="coverage.xml",
            status="fail",
            message=f"invalid coverage line-rate: {line_rate_raw}",
        )

    observed = {
        "coverage_percent": round(coverage_percent, 2),
        "min_coverage": min_coverage,
    }

    if coverage_percent < min_coverage:
        return CheckResult(
            name="coverage.xml",
            status="fail",
            message=f"coverage {coverage_percent:.2f}% < {min_coverage:.2f}%",
            observed=observed,
        )

    return CheckResult(
        name="coverage.xml",
        status="pass",
        message=f"coverage {coverage_percent:.2f}% >= {min_coverage:.2f}%",
        observed=observed,
    )


def _check_readme(path: Path) -> CheckResult:
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return CheckResult(
            name="README.md",
            status="fail",
            message="README.md is empty",
        )

    lowered = content.lower()
    required_terms = ("install", "run", "test")
    missing_terms = [term for term in required_terms if term not in lowered]
    if missing_terms:
        return CheckResult(
            name="README.md",
            status="fail",
            message=f"README.md missing required sections: {', '.join(missing_terms)}",
            observed={"missing_terms": missing_terms},
        )

    return CheckResult(
        name="README.md",
        status="pass",
        message="README.md includes install, run, and test guidance",
    )


def _as_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
