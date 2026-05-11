from __future__ import annotations

from .models import (
    FlowStage,
    IssueFlowPlanModel,
    IssueFlowStepModel,
    IssueModel,
)


def build_issue_flow_plan(issue: IssueModel) -> IssueFlowPlanModel:
    next_stage = _next_stage(issue)
    steps = _build_steps(issue, next_stage)
    if next_stage is None:
        next_owner = None
        next_action = None
    else:
        next_owner = _owner_for_stage(next_stage)
        next_action = _action_for_stage(next_stage)

    return IssueFlowPlanModel(
        issue_id=issue.issue_id,
        issue_status=issue.status,
        next_stage=next_stage,
        next_owner=next_owner,
        next_action=next_action,
        summary=_summary(issue, next_stage),
        steps=tuple(steps),
    )


def _next_stage(issue: IssueModel) -> FlowStage | None:
    execution = issue.execution
    if issue.status == "done":
        return None
    if issue.status == "blocked":
        return "ceo"
    if execution is None or execution.last_run_status is None:
        return "ceo" if issue.status == "todo" else "builder"
    if execution.last_run_status == "blocked":
        return "ceo"
    if execution.last_run_status == "fail":
        return "builder"
    if execution.last_run_status == "pass":
        return "reporter"
    return "builder"


def _build_steps(issue: IssueModel, next_stage: FlowStage | None) -> list[IssueFlowStepModel]:
    completed = _completed_stages(issue)
    blocked = issue.status == "blocked"
    steps: list[IssueFlowStepModel] = []

    for stage in ("ceo", "builder", "scanner", "reporter", "devops"):
        if stage in completed:
            status = "complete"
            reason = f"{_owner_for_stage(stage)} has completed this stage"
        elif blocked:
            status = "blocked"
            reason = "issue is blocked"
        elif stage == next_stage:
            status = "active"
            reason = f"{_owner_for_stage(stage)} should act next"
        elif _stage_is_before(stage, next_stage):
            status = "complete"
            reason = f"{_owner_for_stage(stage)} stage is already satisfied"
        else:
            status = "pending"
            reason = f"waiting for {_dependency_for_stage(stage)}"

        steps.append(
            IssueFlowStepModel(
                stage=stage,
                owner=_owner_for_stage(stage),
                action=_action_for_stage(stage),
                status=status,
                reason=reason,
                dependencies=_dependencies_for_stage(stage),
                outputs=_outputs_for_stage(stage, issue),
            )
        )

    return steps


def _completed_stages(issue: IssueModel) -> set[FlowStage]:
    execution = issue.execution
    if issue.status == "done":
        return {"ceo", "builder", "scanner", "reporter", "devops"}
    if execution is None:
        return set()
    if execution.last_run_status == "pass":
        return {"ceo", "builder", "scanner"}
    if execution.last_run_status == "fail":
        return {"ceo"}
    if execution.last_run_status == "blocked":
        return set()
    return set()


def _stage_is_before(stage: FlowStage, next_stage: FlowStage | None) -> bool:
    if next_stage is None:
        return False
    order = _stage_order()
    return order.index(stage) < order.index(next_stage)


def _stage_order() -> tuple[FlowStage, ...]:
    return ("ceo", "builder", "scanner", "reporter", "devops")


def _owner_for_stage(stage: FlowStage) -> str:
    return {
        "ceo": "CEO",
        "builder": "Builder Bot",
        "scanner": "Scanner Bot",
        "reporter": "Reporter Bot",
        "devops": "DevOps Bot",
    }[stage]


def _action_for_stage(stage: FlowStage) -> str:
    return {
        "ceo": "review issue, confirm scope, and delegate the next stage",
        "builder": "implement code, tests, and required artifacts",
        "scanner": "audit artifacts and block unsafe findings",
        "reporter": "summarize verified findings for delivery",
        "devops": "deploy only verified artifacts",
    }[stage]


def _dependencies_for_stage(stage: FlowStage) -> tuple[str, ...]:
    return {
        "ceo": (),
        "builder": ("ceo",),
        "scanner": ("builder",),
        "reporter": ("scanner",),
        "devops": ("reporter",),
    }[stage]


def _outputs_for_stage(stage: FlowStage, issue: IssueModel) -> tuple[str, ...]:
    base_outputs = {
        "ceo": ("delegation plan",),
        "builder": tuple(issue.required_artifacts),
        "scanner": ("semgrep.sarif", "trufflehog.jsonl"),
        "reporter": ("report.md",),
        "devops": ("deployment verification",),
    }
    return base_outputs[stage]


def _dependency_for_stage(stage: FlowStage) -> str:
    return {
        "ceo": "issue intake",
        "builder": "CEO review",
        "scanner": "Builder artifacts",
        "reporter": "scanner verification",
        "devops": "reporter handoff",
    }[stage]


def _summary(issue: IssueModel, next_stage: FlowStage | None) -> str:
    if next_stage is None:
        return f"{issue.issue_id} is complete"
    return f"Next stage: {_owner_for_stage(next_stage)} ({_action_for_stage(next_stage)})"
