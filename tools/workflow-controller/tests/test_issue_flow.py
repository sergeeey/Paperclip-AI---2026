import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_controller.cli import main
from workflow_controller.issue_flow import build_issue_flow_plan
from workflow_controller.models import IssueExecutionModel, IssueModel


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "issues"


class IssueFlowTests(unittest.TestCase):
    def test_plan_starts_with_ceo_for_todo_issue(self) -> None:
        issue = IssueModel.model_validate_json((FIXTURES / "clean-issue.json").read_text(encoding="utf-8"))

        plan = build_issue_flow_plan(issue)

        self.assertEqual(plan.next_stage, "ceo")
        self.assertEqual(plan.next_owner, "CEO")
        self.assertEqual(plan.steps[0].status, "active")
        self.assertEqual(plan.steps[1].status, "pending")

    def test_plan_moves_to_builder_after_fail(self) -> None:
        issue = IssueModel(
            issue_id="FLOW-2",
            title="FLOW-2: Recover after failed scan",
            goal="Retry the pipeline after a failed gate run.",
            requirements=["Return to Builder after failure"],
            tech_stack={"Language": "Python 3.11+"},
            output_location="/tmp/projects/FLOW-2/",
            acceptance_criteria=["Failure should route back to Builder"],
            required_artifacts=["test-results.json", "coverage.xml", "README.md"],
            assigned_to="Builder Bot",
            status="in_progress",
            execution=IssueExecutionModel(last_run_status="fail", last_run_reason="security gate failed"),
        )

        plan = build_issue_flow_plan(issue)

        self.assertEqual(plan.next_stage, "builder")
        self.assertEqual(plan.steps[0].status, "complete")
        self.assertEqual(plan.steps[1].status, "active")

    def test_plan_moves_to_reporter_after_pass(self) -> None:
        issue = IssueModel(
            issue_id="FLOW-1",
            title="FLOW-1: Deploy verified app",
            goal="Deploy a verified app.",
            requirements=["Build, scan, and report"],
            tech_stack={"Language": "Python 3.11+"},
            output_location="/tmp/projects/FLOW-1/",
            acceptance_criteria=["Artifacts pass"],
            required_artifacts=["test-results.json", "coverage.xml", "README.md"],
            assigned_to="Builder Bot",
            status="in_progress",
            deployment={"port": 8001, "service_name": "hello-world"},
            execution=IssueExecutionModel(last_run_status="pass", last_run_reason="all issue gates passed"),
        )

        plan = build_issue_flow_plan(issue)

        self.assertEqual(plan.next_stage, "reporter")
        self.assertEqual(plan.steps[0].status, "complete")
        self.assertEqual(plan.steps[2].status, "complete")
        self.assertEqual(plan.steps[3].status, "active")

    def test_cli_plan_issue_flow_json(self) -> None:
        issue_file = FIXTURES / "clean-issue.json"
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(["plan-issue-flow", "--issue-file", str(issue_file), "--json"])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["next_stage"], "ceo")
        self.assertEqual(payload["steps"][0]["owner"], "CEO")


if __name__ == "__main__":
    unittest.main()
