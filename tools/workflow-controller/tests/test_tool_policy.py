import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_controller.tool_policy import ToolPolicy, evaluate_tool_request


class ToolPolicyTests(unittest.TestCase):
    def test_allows_known_tool_inside_allowed_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = ToolPolicy(allowed_roots=(Path(tmp),))
            project_dir = Path(tmp) / "project"

            decision = evaluate_tool_request(
                "workflow_run_issue_gates",
                {"project_dir": str(project_dir)},
                policy=policy,
            )

        self.assertEqual(decision.action, "allow")
        self.assertEqual(decision.tool_name, "workflow_run_issue_gates")

    def test_blocks_unknown_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = ToolPolicy(allowed_roots=(Path(tmp),))

            decision = evaluate_tool_request(
                "shell",
                {"command": "whoami"},
                policy=policy,
            )

        self.assertEqual(decision.action, "block")
        self.assertIn("not in allow list", decision.reason)

    def test_blocks_path_outside_allowed_roots(self) -> None:
        with tempfile.TemporaryDirectory() as allowed_tmp:
            with tempfile.TemporaryDirectory() as denied_tmp:
                policy = ToolPolicy(allowed_roots=(Path(allowed_tmp),))

                decision = evaluate_tool_request(
                    "workflow_verify_artifacts",
                    {"project_dir": str(Path(denied_tmp) / "project")},
                    policy=policy,
                )

        self.assertEqual(decision.action, "block")
        self.assertIn("outside allowed roots", decision.reason)

    def test_requires_approval_for_configured_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = ToolPolicy(
                allowed_roots=(Path(tmp),),
                require_approval_tools=("workflow_verify_security",),
            )

            decision = evaluate_tool_request(
                "workflow_verify_security",
                {"project_dir": str(Path(tmp) / "project")},
                policy=policy,
            )

        self.assertEqual(decision.action, "require_approval")
        self.assertIn("requires approval", decision.reason)


if __name__ == "__main__":
    unittest.main()
