from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from .tool_policy import PolicyDecision, ToolPolicy

CheckStatus: TypeAlias = Literal["pass", "fail", "blocked"]
VerdictStatus: TypeAlias = Literal["pass", "fail", "blocked"]
IssueStatus: TypeAlias = Literal["todo", "in_progress", "blocked", "done"]
IssuePriority: TypeAlias = Literal["P0", "P1", "P2", "P3"]
FlowStage: TypeAlias = Literal["ceo", "builder", "scanner", "reporter", "devops"]
FlowStepStatus: TypeAlias = Literal["pending", "active", "complete", "blocked"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CheckResult(StrictModel):
    name: str = Field(min_length=1)
    status: CheckStatus
    message: str = Field(min_length=1)
    observed: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"name"})


class EventModel(StrictModel):
    timestamp: datetime
    stage: str = Field(min_length=1)
    issue_id: str = Field(min_length=1)
    status: VerdictStatus
    reason: str = Field(min_length=1)
    checks: dict[str, CheckResult]
    project_dir: str | None = None
    blocked_reason: str | None = None


class GateVerdict(StrictModel):
    issue_id: str = Field(min_length=1)
    project_dir: Path
    status: VerdictStatus
    reason: str = Field(min_length=1)
    checks: tuple[CheckResult, ...]
    stage: str = "artifact_gate"

    @field_serializer("project_dir")
    def _serialize_project_dir(self, value: Path) -> str:
        return str(value)

    def to_event_model(self, *, timestamp: datetime | None = None) -> EventModel:
        return EventModel(
            timestamp=timestamp or datetime.now(timezone.utc),
            stage=self.stage,
            issue_id=self.issue_id,
            project_dir=str(self.project_dir),
            status=self.status,
            reason=self.reason,
            blocked_reason=self.reason if self.status == "blocked" else None,
            checks={check.name: check for check in self.checks},
        )

    def to_event(self) -> dict[str, Any]:
        return self.to_event_model().model_dump(mode="json", exclude_none=True)


class IssueExecutionModel(StrictModel):
    min_tests: int = Field(default=15, ge=0)
    min_coverage: float = Field(default=80.0, ge=0.0, le=100.0)
    semgrep_sarif: str | None = None
    trufflehog_json: str | None = None
    run_semgrep: bool = False
    semgrep_config: str = "auto"
    run_trufflehog: bool = False
    scan_output_dir: str | None = None
    semgrep_block_levels: list[str] = Field(default_factory=lambda: ["error", "warning"])
    block_trufflehog_unknown: bool = True
    timeout_seconds: int = Field(default=120, ge=1)
    event_log: str | None = None
    last_run_status: VerdictStatus | None = None
    last_run_reason: str | None = None
    last_event_log: str | None = None


class IssueModel(StrictModel):
    issue_id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]*-\d+$")
    title: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    requirements: list[str] = Field(min_length=1)
    tech_stack: dict[str, str] = Field(default_factory=dict)
    output_location: str = Field(min_length=1)
    acceptance_criteria: list[str] = Field(min_length=1)
    required_artifacts: list[str] = Field(min_length=1)
    assigned_to: str = Field(min_length=1)
    status: IssueStatus
    priority: IssuePriority | None = None
    deployment: dict[str, Any] | None = None
    kill_criteria: list[str] = Field(default_factory=list)
    execution: IssueExecutionModel | None = None


class IssueFlowStepModel(StrictModel):
    stage: FlowStage
    owner: str = Field(min_length=1)
    action: str = Field(min_length=1)
    status: FlowStepStatus
    reason: str = Field(min_length=1)
    dependencies: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()


class IssueFlowPlanModel(StrictModel):
    issue_id: str = Field(min_length=1)
    issue_status: IssueStatus
    next_stage: FlowStage | None = None
    next_owner: str | None = None
    next_action: str | None = None
    summary: str = Field(min_length=1)
    steps: tuple[IssueFlowStepModel, ...]


SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "check-result": CheckResult,
    "event": EventModel,
    "gate-verdict": GateVerdict,
    "issue-flow-plan": IssueFlowPlanModel,
    "issue-flow-step": IssueFlowStepModel,
    "issue": IssueModel,
    "issue-execution": IssueExecutionModel,
    "policy-decision": PolicyDecision,
    "tool-policy": ToolPolicy,
}


def export_json_schemas(output_dir: Path) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for name, model in SCHEMA_MODELS.items():
        path = output_dir / f"{name}.schema.json"
        schema = model.model_json_schema()
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)

    return paths
