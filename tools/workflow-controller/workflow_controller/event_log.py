from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .artifact_gate import write_event
from .models import CheckResult, EventModel, GateVerdict


def verify_event_log(*, event_log: Path, expected_issue_id: str | None = None) -> GateVerdict:
    event_log = Path(event_log)

    if not event_log.is_file():
        return GateVerdict(
            issue_id=expected_issue_id or "unknown",
            project_dir=event_log.parent,
            status="blocked",
            reason="event log missing",
            stage="event_log_gate",
            checks=(
                CheckResult(
                    name="event_log",
                    status="blocked",
                    message=f"file not found: {event_log}",
                    observed={"path": str(event_log)},
                ),
            ),
        )

    raw_lines = [line.strip() for line in event_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not raw_lines:
        return GateVerdict(
            issue_id=expected_issue_id or "unknown",
            project_dir=event_log.parent,
            status="blocked",
            reason="event log empty",
            stage="event_log_gate",
            checks=(
                CheckResult(
                    name="event_log",
                    status="blocked",
                    message=f"no events found in {event_log}",
                    observed={"path": str(event_log)},
                ),
            ),
        )

    events: list[EventModel] = []
    for index, line in enumerate(raw_lines, start=1):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            return _failed(
                event_log=event_log,
                issue_id=expected_issue_id or "unknown",
                message=f"invalid JSON at line {index}: {exc.msg}",
                observed={"line": index},
            )

        try:
            event = EventModel.model_validate(payload)
        except Exception as exc:  # pydantic ValidationError or TypeError
            return _failed(
                event_log=event_log,
                issue_id=expected_issue_id or "unknown",
                message=f"invalid event payload at line {index}: {exc}",
                observed={"line": index},
            )

        events.append(event)

    issue_id = expected_issue_id or events[0].issue_id
    if any(event.issue_id != issue_id for event in events):
        return _failed(
            event_log=event_log,
            issue_id=issue_id,
            message="issue_id mismatch in event log",
            observed={"issue_id": issue_id},
        )

    sequence_check = _validate_sequence(events)
    if sequence_check is not None:
        return _failed(
            event_log=event_log,
            issue_id=issue_id,
            message=sequence_check,
            observed={"stages": [event.stage for event in events]},
        )

    consistency_check = _validate_consistency(events)
    if consistency_check is not None:
        return _failed(
            event_log=event_log,
            issue_id=issue_id,
            message=consistency_check,
            observed={"stages": [event.stage for event in events]},
        )

    final_event = events[-1]
    checks = tuple(
        CheckResult(
            name=event.stage,
            status=event.status,
            message=event.reason,
            observed={
                "issue_id": event.issue_id,
                "reason": event.reason,
                "status": event.status,
            },
        )
        for event in events[:-1]
    )
    checks = checks + (
        CheckResult(
            name=final_event.stage,
            status=final_event.status,
            message=final_event.reason,
            observed={
                "issue_id": final_event.issue_id,
                "reason": final_event.reason,
                "status": final_event.status,
            },
        ),
    )

    return GateVerdict(
        issue_id=issue_id,
        project_dir=event_log.parent,
        status="pass",
        reason="event log passed validation",
        stage="event_log_gate",
        checks=checks,
    )


def _validate_sequence(events: list[EventModel]) -> str | None:
    stages = [event.stage for event in events]
    allowed_sequences = [
        ["artifact_gate", "issue_gates"],
        ["artifact_gate", "security_gate", "issue_gates"],
    ]
    if stages not in allowed_sequences:
        return "invalid stage sequence"
    return None


def _validate_consistency(events: list[EventModel]) -> str | None:
    final_event = events[-1]
    prior_events = events[:-1]

    if final_event.stage != "issue_gates":
        return "final event must be issue_gates"

    if final_event.status == "pass":
        if len(prior_events) != 2 or prior_events[0].status != "pass" or prior_events[1].status != "pass":
            return "final pass does not match prior gate statuses"
        if final_event.reason != "all issue gates passed":
            return "final pass reason mismatch"
        if final_event.blocked_reason is not None:
            return "final pass should not include blocked_reason"
        return None

    if len(prior_events) == 1:
        artifact = prior_events[0]
        if final_event.status != artifact.status:
            return "final status does not match artifact gate"
        if final_event.reason != "artifact gate blocked":
            return "artifact-gate final reason mismatch"
        if final_event.status != "blocked" or final_event.blocked_reason != "artifact gate blocked":
            return "artifact-gate blocked_reason mismatch"
        return None

    security = prior_events[-1]
    if final_event.status != security.status:
        return "final status does not match security gate"
    expected_reason = f"security gate {_status_verb(final_event.status)}"
    if final_event.reason != expected_reason:
        return "security-gate final reason mismatch"
    if final_event.status == "blocked" and final_event.blocked_reason != final_event.reason:
        return "security-gate blocked_reason mismatch"
    if final_event.status != "blocked" and final_event.blocked_reason is not None:
        return "non-blocked final event should not include blocked_reason"
    return None


def _failed(
    *,
    event_log: Path,
    issue_id: str,
    message: str,
    observed: dict[str, Any] | None = None,
) -> GateVerdict:
    return GateVerdict(
        issue_id=issue_id,
        project_dir=event_log.parent,
        status="fail",
        reason=message,
        stage="event_log_gate",
        checks=(
            CheckResult(
                name="event_log",
                status="fail",
                message=message,
                observed=observed,
            ),
        ),
    )


def _status_verb(status: str) -> str:
    if status == "pass":
        return "passed"
    if status == "fail":
        return "failed"
    return "blocked"
