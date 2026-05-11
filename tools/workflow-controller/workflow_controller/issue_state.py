from __future__ import annotations

import json
from pathlib import Path

from .issue_runner import IssueGateRun
from .models import IssueExecutionModel, IssueModel, IssueStatus, VerdictStatus


def sync_issue_state(
    issue: IssueModel,
    *,
    final_run: IssueGateRun,
    event_log: Path | None = None,
) -> IssueModel:
    execution = issue.execution or IssueExecutionModel()
    updated_execution = execution.model_copy(
        update={
            "last_run_status": final_run.final.status,
            "last_run_reason": final_run.final.reason,
            "last_event_log": str(event_log) if event_log is not None else execution.last_event_log,
        }
    )
    return issue.model_copy(
        update={
            "status": _issue_status_from_verdict(final_run.final.status),
            "execution": updated_execution,
        }
    )


def write_issue_state(issue: IssueModel, *, issue_file: Path) -> None:
    issue_file = Path(issue_file)
    issue_file.write_text(issue.model_dump_json(indent=2, exclude_none=True) + "\n", encoding="utf-8")


def _issue_status_from_verdict(status: VerdictStatus) -> IssueStatus:
    if status == "pass":
        return "done"
    if status == "blocked":
        return "blocked"
    return "in_progress"
