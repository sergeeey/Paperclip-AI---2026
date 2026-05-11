import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_controller.models import (
    CheckResult,
    EventModel,
    GateVerdict,
    IssueModel,
    export_json_schemas,
)


class ModelSchemaTests(unittest.TestCase):
    def test_gate_verdict_emits_valid_event_model_payload(self) -> None:
        verdict = GateVerdict(
            issue_id="BLI-2",
            project_dir=Path("/tmp/projects/BLI-2"),
            status="pass",
            reason="all checks passed",
            checks=(
                CheckResult(
                    name="test-results.json",
                    status="pass",
                    message="tests passed",
                    observed={"passed": 15},
                ),
            ),
        )

        event = verdict.to_event()
        validated = EventModel.model_validate(event)

        self.assertEqual(validated.issue_id, "BLI-2")
        self.assertEqual(validated.stage, "artifact_gate")
        self.assertEqual(validated.status, "pass")
        self.assertEqual(validated.checks["test-results.json"].observed, {"passed": 15})

    def test_issue_model_matches_strict_issue_schema_shape(self) -> None:
        issue = IssueModel(
            issue_id="BLI-2",
            title="BLI-2: Build Flask Hello World API",
            goal="Create minimal Flask API.",
            requirements=["Flask app in app.py"],
            tech_stack={"Language": "Python 3.11+", "Framework": "Flask"},
            output_location="/tmp/projects/BLI-2/",
            acceptance_criteria=["pytest passes"],
            required_artifacts=["test-results.json", "coverage.xml", "README.md"],
            assigned_to="Builder Bot",
            status="todo",
            priority="P1",
        )

        payload = issue.model_dump(mode="json", exclude_none=True)

        self.assertEqual(payload["issue_id"], "BLI-2")
        self.assertEqual(payload["required_artifacts"][0], "test-results.json")
        self.assertEqual(payload["status"], "todo")

    def test_exports_json_schemas_for_validation_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            paths = export_json_schemas(output_dir)

            names = {path.name for path in paths}
            event_schema = json.loads((output_dir / "event.schema.json").read_text(encoding="utf-8"))

        self.assertIn("check-result.schema.json", names)
        self.assertIn("event.schema.json", names)
        self.assertIn("gate-verdict.schema.json", names)
        self.assertIn("issue-flow-plan.schema.json", names)
        self.assertIn("issue-flow-step.schema.json", names)
        self.assertIn("issue.schema.json", names)
        self.assertIn("policy-decision.schema.json", names)
        self.assertIn("tool-policy.schema.json", names)
        self.assertIn("issue-execution.schema.json", names)
        self.assertEqual(event_schema["type"], "object")
        self.assertIn("properties", event_schema)


if __name__ == "__main__":
    unittest.main()
