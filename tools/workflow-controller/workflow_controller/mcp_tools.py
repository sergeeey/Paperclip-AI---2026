from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .artifact_gate import verify_artifacts, write_event
from .issue_flow import build_issue_flow_plan
from .issue_runner import run_issue_gates, run_issue_gates_from_issue
from .issue_state import sync_issue_state, write_issue_state
from .models import export_json_schemas
from .security_gate import DEFAULT_SEMGREP_BLOCK_LEVELS, verify_security_scans
from .tool_policy import PolicyDecision, ToolPolicy, default_policy, evaluate_tool_request


class WorkflowToolService:
    def __init__(self, *, policy: ToolPolicy | None = None) -> None:
        self.policy = policy or default_policy()

    def run_issue_gates(
        self,
        *,
        issue_id: str,
        project_dir: str,
        min_tests: int = 15,
        min_coverage: float = 80.0,
        semgrep_sarif: str | None = None,
        trufflehog_json: str | None = None,
        run_semgrep: bool = False,
        semgrep_config: str = "auto",
        run_trufflehog: bool = False,
        scan_output_dir: str | None = None,
        semgrep_block_levels: list[str] | None = None,
        block_trufflehog_unknown: bool = True,
        timeout_seconds: int = 120,
        event_log: str | None = None,
    ) -> dict[str, Any]:
        arguments = {
            "issue_id": issue_id,
            "project_dir": project_dir,
            "semgrep_sarif": semgrep_sarif,
            "trufflehog_json": trufflehog_json,
            "run_semgrep": run_semgrep,
            "semgrep_config": semgrep_config,
            "run_trufflehog": run_trufflehog,
            "scan_output_dir": scan_output_dir,
            "event_log": event_log,
        }
        decision = evaluate_tool_request(
            "workflow_run_issue_gates",
            arguments,
            policy=self.policy,
        )
        if decision.action != "allow":
            return _policy_stop(decision)

        run = run_issue_gates(
            issue_id=issue_id,
            project_dir=Path(project_dir),
            min_tests=min_tests,
            min_coverage=min_coverage,
            semgrep_sarif=Path(semgrep_sarif) if semgrep_sarif else None,
            trufflehog_json=Path(trufflehog_json) if trufflehog_json else None,
            run_semgrep=run_semgrep,
            semgrep_config=semgrep_config,
            run_trufflehog=run_trufflehog,
            scan_output_dir=Path(scan_output_dir) if scan_output_dir else None,
            semgrep_block_levels=tuple(semgrep_block_levels or DEFAULT_SEMGREP_BLOCK_LEVELS),
            block_trufflehog_unknown=block_trufflehog_unknown,
            timeout_seconds=timeout_seconds,
            event_log=Path(event_log) if event_log else None,
        )
        return _success(decision, run.to_dict())

    def sync_issue_state(
        self,
        *,
        issue_file: str,
        output_file: str | None = None,
        event_log: str | None = None,
    ) -> dict[str, Any]:
        arguments = {
            "issue_file": issue_file,
            "output_file": output_file,
            "event_log": event_log,
        }
        decision = evaluate_tool_request(
            "workflow_sync_issue_state",
            arguments,
            policy=self.policy,
        )
        if decision.action != "allow":
            return _policy_stop(decision)

        issue_path = Path(issue_file)
        issue = _load_issue(issue_path)
        run = run_issue_gates_from_issue(issue, issue_file=issue_path, event_log=Path(event_log) if event_log else None)
        synced = sync_issue_state(issue, final_run=run, event_log=Path(event_log) if event_log else None)
        output_path = Path(output_file) if output_file else issue_path
        write_issue_state(synced, issue_file=output_path)
        return _success(decision, {"issue_file": str(output_path), "run": run.to_dict(), "issue": synced.model_dump(mode="json", exclude_none=True)})

    def plan_issue_flow(self, *, issue_file: str) -> dict[str, Any]:
        arguments = {"issue_file": issue_file}
        decision = evaluate_tool_request(
            "workflow_plan_issue_flow",
            arguments,
            policy=self.policy,
        )
        if decision.action != "allow":
            return _policy_stop(decision)

        issue = _load_issue(Path(issue_file))
        plan = build_issue_flow_plan(issue)
        return _success(decision, plan.model_dump(mode="json", exclude_none=True))

    def verify_artifacts(
        self,
        *,
        issue_id: str,
        project_dir: str,
        min_tests: int = 15,
        min_coverage: float = 80.0,
        event_log: str | None = None,
    ) -> dict[str, Any]:
        arguments = {
            "issue_id": issue_id,
            "project_dir": project_dir,
            "min_tests": min_tests,
            "min_coverage": min_coverage,
            "event_log": event_log,
        }
        decision = evaluate_tool_request(
            "workflow_verify_artifacts",
            arguments,
            policy=self.policy,
        )
        if decision.action != "allow":
            return _policy_stop(decision)

        verdict = verify_artifacts(
            issue_id=issue_id,
            project_dir=Path(project_dir),
            min_tests=min_tests,
            min_coverage=min_coverage,
        )
        if event_log:
            write_event(verdict, Path(event_log))
        return _success(decision, verdict.to_event())

    def verify_security(
        self,
        *,
        issue_id: str,
        project_dir: str,
        semgrep_sarif: str | None = None,
        trufflehog_json: str | None = None,
        run_semgrep: bool = False,
        semgrep_config: str = "auto",
        run_trufflehog: bool = False,
        scan_output_dir: str | None = None,
        semgrep_block_levels: list[str] | None = None,
        block_trufflehog_unknown: bool = True,
        timeout_seconds: int = 120,
        event_log: str | None = None,
    ) -> dict[str, Any]:
        arguments = {
            "issue_id": issue_id,
            "project_dir": project_dir,
            "semgrep_sarif": semgrep_sarif,
            "trufflehog_json": trufflehog_json,
            "run_semgrep": run_semgrep,
            "semgrep_config": semgrep_config,
            "run_trufflehog": run_trufflehog,
            "scan_output_dir": scan_output_dir,
            "event_log": event_log,
        }
        decision = evaluate_tool_request(
            "workflow_verify_security",
            arguments,
            policy=self.policy,
        )
        if decision.action != "allow":
            return _policy_stop(decision)

        verdict = verify_security_scans(
            issue_id=issue_id,
            project_dir=Path(project_dir),
            semgrep_sarif=Path(semgrep_sarif) if semgrep_sarif else None,
            trufflehog_json=Path(trufflehog_json) if trufflehog_json else None,
            run_semgrep=run_semgrep,
            semgrep_config=semgrep_config,
            run_trufflehog=run_trufflehog,
            scan_output_dir=Path(scan_output_dir) if scan_output_dir else None,
            semgrep_block_levels=tuple(semgrep_block_levels or DEFAULT_SEMGREP_BLOCK_LEVELS),
            block_trufflehog_unknown=block_trufflehog_unknown,
            timeout_seconds=timeout_seconds,
        )
        if event_log:
            write_event(verdict, Path(event_log))
        return _success(decision, verdict.to_event())

    def export_schemas(self, *, output_dir: str) -> dict[str, Any]:
        arguments = {"output_dir": output_dir}
        decision = evaluate_tool_request(
            "workflow_export_schemas",
            arguments,
            policy=self.policy,
        )
        if decision.action != "allow":
            return _policy_stop(decision)

        paths = export_json_schemas(Path(output_dir))
        return _success(decision, {"paths": [str(path) for path in paths]})


def create_mcp_server(*, policy: ToolPolicy | None = None) -> FastMCP:
    service = WorkflowToolService(policy=policy)
    server = FastMCP("paperclip-workflow-controller")

    @server.tool(
        name="workflow_run_issue_gates",
        description="Run artifact and security gates as one issue-level pipeline.",
        structured_output=True,
    )
    def workflow_run_issue_gates(
        issue_id: str,
        project_dir: str,
        min_tests: int = 15,
        min_coverage: float = 80.0,
        semgrep_sarif: str | None = None,
        trufflehog_json: str | None = None,
        run_semgrep: bool = False,
        semgrep_config: str = "auto",
        run_trufflehog: bool = False,
        scan_output_dir: str | None = None,
        semgrep_block_levels: list[str] | None = None,
        block_trufflehog_unknown: bool = True,
        timeout_seconds: int = 120,
        event_log: str | None = None,
    ) -> dict[str, Any]:
        return service.run_issue_gates(
            issue_id=issue_id,
            project_dir=project_dir,
            min_tests=min_tests,
            min_coverage=min_coverage,
            semgrep_sarif=semgrep_sarif,
            trufflehog_json=trufflehog_json,
            run_semgrep=run_semgrep,
            semgrep_config=semgrep_config,
            run_trufflehog=run_trufflehog,
            scan_output_dir=scan_output_dir,
            semgrep_block_levels=semgrep_block_levels,
            block_trufflehog_unknown=block_trufflehog_unknown,
            timeout_seconds=timeout_seconds,
            event_log=event_log,
        )

    @server.tool(
        name="workflow_sync_issue_state",
        description="Run issue gates, sync the resulting state, and write the issue artifact back to disk.",
        structured_output=True,
    )
    def workflow_sync_issue_state(
        issue_file: str,
        output_file: str | None = None,
        event_log: str | None = None,
    ) -> dict[str, Any]:
        return service.sync_issue_state(
            issue_file=issue_file,
            output_file=output_file,
            event_log=event_log,
        )

    @server.tool(
        name="workflow_plan_issue_flow",
        description="Build a deterministic CEO→Builder→Scanner→Reporter→DevOps plan from an issue file.",
        structured_output=True,
    )
    def workflow_plan_issue_flow(issue_file: str) -> dict[str, Any]:
        return service.plan_issue_flow(issue_file=issue_file)

    @server.tool(
        name="workflow_verify_artifacts",
        description="Verify Builder artifacts and return a policy-checked GateVerdict event.",
        structured_output=True,
    )
    def workflow_verify_artifacts(
        issue_id: str,
        project_dir: str,
        min_tests: int = 15,
        min_coverage: float = 80.0,
        event_log: str | None = None,
    ) -> dict[str, Any]:
        return service.verify_artifacts(
            issue_id=issue_id,
            project_dir=project_dir,
            min_tests=min_tests,
            min_coverage=min_coverage,
            event_log=event_log,
        )

    @server.tool(
        name="workflow_verify_security",
        description="Verify Semgrep SARIF and TruffleHog JSONL security artifacts.",
        structured_output=True,
    )
    def workflow_verify_security(
        issue_id: str,
        project_dir: str,
        semgrep_sarif: str | None = None,
        trufflehog_json: str | None = None,
        run_semgrep: bool = False,
        semgrep_config: str = "auto",
        run_trufflehog: bool = False,
        scan_output_dir: str | None = None,
        semgrep_block_levels: list[str] | None = None,
        block_trufflehog_unknown: bool = True,
        timeout_seconds: int = 120,
        event_log: str | None = None,
    ) -> dict[str, Any]:
        return service.verify_security(
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
            event_log=event_log,
        )

    @server.tool(
        name="workflow_export_schemas",
        description="Export workflow-controller JSON Schemas.",
        structured_output=True,
    )
    def workflow_export_schemas(output_dir: str) -> dict[str, Any]:
        return service.export_schemas(output_dir=output_dir)

    return server


def main() -> None:
    create_mcp_server().run()


def _policy_stop(decision: PolicyDecision) -> dict[str, Any]:
    status = "approval_required" if decision.action == "require_approval" else "blocked"
    return {
        "policy": decision.model_dump(mode="json"),
        "status": status,
        "reason": decision.reason,
    }


def _success(decision: PolicyDecision, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy": decision.model_dump(mode="json"),
        "result": result,
    }


def _load_issue(issue_file: Path):
    from .models import IssueModel

    return IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
