import json
import tempfile
import unittest
from pathlib import Path
import asyncio

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_controller.mcp_tools import WorkflowToolService, create_mcp_server
from workflow_controller.tool_policy import ToolPolicy


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class MCPToolTests(unittest.TestCase):
    def test_verify_artifacts_tool_runs_when_policy_allows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "project"
            project_dir.mkdir()
            self._write_valid_artifacts(project_dir)
            service = WorkflowToolService(policy=ToolPolicy(allowed_roots=(root,)))

            response = service.verify_artifacts(
                issue_id="BLI-2",
                project_dir=str(project_dir),
            )

        self.assertEqual(response["policy"]["action"], "allow")
        self.assertEqual(response["result"]["status"], "pass")
        self.assertEqual(response["result"]["stage"], "artifact_gate")

    def test_run_issue_gates_tool_runs_when_policy_allows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "project"
            project_dir.mkdir()
            self._write_valid_artifacts(project_dir)
            semgrep_sarif = root / "semgrep.sarif"
            trufflehog_json = root / "trufflehog.jsonl"
            self._write_clean_sarif(semgrep_sarif)
            trufflehog_json.write_text("", encoding="utf-8")
            service = WorkflowToolService(policy=ToolPolicy(allowed_roots=(root,)))

            response = service.run_issue_gates(
                issue_id="BLI-2",
                project_dir=str(project_dir),
                semgrep_sarif=str(semgrep_sarif),
                trufflehog_json=str(trufflehog_json),
            )

        self.assertEqual(response["policy"]["action"], "allow")
        self.assertEqual(response["result"]["status"], "pass")
        self.assertEqual(response["result"]["final"]["stage"], "issue_gates")

    def test_sync_issue_state_tool_runs_when_policy_allows(self) -> None:
        issue_file = FIXTURES / "issues" / "clean-issue.json"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_file = root / "synced-issue.json"
            event_log = root / "events.jsonl"
            service = WorkflowToolService(policy=ToolPolicy(allowed_roots=(Path.cwd(), root)))

            response = service.sync_issue_state(
                issue_file=str(issue_file),
                output_file=str(output_file),
                event_log=str(event_log),
            )
            synced = json.loads(output_file.read_text(encoding="utf-8"))

        self.assertEqual(response["policy"]["action"], "allow")
        self.assertEqual(response["result"]["issue"]["status"], "done")
        self.assertEqual(synced["status"], "done")

    def test_plan_issue_flow_tool_runs_when_policy_allows(self) -> None:
        issue_file = FIXTURES / "issues" / "clean-issue.json"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = WorkflowToolService(policy=ToolPolicy(allowed_roots=(Path.cwd(), root)))

            response = service.plan_issue_flow(issue_file=str(issue_file))

        self.assertEqual(response["policy"]["action"], "allow")
        self.assertEqual(response["result"]["next_stage"], "ceo")

    def test_mcp_server_can_call_sync_issue_state_tool(self) -> None:
        issue_file = FIXTURES / "issues" / "clean-issue.json"

        async def run_check(root: Path) -> dict:
            server = create_mcp_server(policy=ToolPolicy(allowed_roots=(Path.cwd(), root)))
            _, structured = await server.call_tool(
                "workflow_sync_issue_state",
                {
                    "issue_file": str(issue_file),
                    "output_file": str(root / "synced-issue.json"),
                    "event_log": str(root / "events.jsonl"),
                },
            )
            return structured

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            structured = asyncio.run(run_check(root))

        self.assertEqual(structured["policy"]["action"], "allow")
        self.assertEqual(structured["result"]["issue"]["status"], "done")

    def test_mcp_server_can_call_plan_issue_flow_tool(self) -> None:
        issue_file = FIXTURES / "issues" / "clean-issue.json"

        async def run_check(root: Path) -> dict:
            server = create_mcp_server(policy=ToolPolicy(allowed_roots=(Path.cwd(), root)))
            _, structured = await server.call_tool(
                "workflow_plan_issue_flow",
                {"issue_file": str(issue_file)},
            )
            return structured

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            structured = asyncio.run(run_check(root))

        self.assertEqual(structured["policy"]["action"], "allow")
        self.assertEqual(structured["result"]["next_stage"], "ceo")

    def test_verify_artifacts_tool_returns_policy_block_without_running(self) -> None:
        with tempfile.TemporaryDirectory() as allowed_tmp:
            with tempfile.TemporaryDirectory() as denied_tmp:
                service = WorkflowToolService(
                    policy=ToolPolicy(allowed_roots=(Path(allowed_tmp),))
                )

                response = service.verify_artifacts(
                    issue_id="BLI-2",
                    project_dir=str(Path(denied_tmp) / "project"),
                )

        self.assertEqual(response["policy"]["action"], "block")
        self.assertEqual(response["status"], "blocked")

    def test_export_schemas_tool_writes_inside_policy_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = WorkflowToolService(policy=ToolPolicy(allowed_roots=(root,)))

            response = service.export_schemas(output_dir=str(root / "schemas"))
            paths = response["result"]["paths"]

            first_schema = json.loads(Path(paths[0]).read_text(encoding="utf-8"))

        self.assertEqual(response["policy"]["action"], "allow")
        self.assertEqual(len(paths), 9)
        self.assertEqual(first_schema["type"], "object")

    def test_verify_security_tool_validates_existing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "project"
            project_dir.mkdir()
            semgrep_sarif = root / "semgrep.sarif"
            trufflehog_json = root / "trufflehog.jsonl"
            semgrep_sarif.write_text(
                json.dumps(
                    {
                        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
                        "version": "2.1.0",
                        "runs": [
                            {
                                "tool": {"driver": {"name": "Semgrep", "rules": []}},
                                "results": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            trufflehog_json.write_text("", encoding="utf-8")
            service = WorkflowToolService(policy=ToolPolicy(allowed_roots=(root,)))

            response = service.verify_security(
                issue_id="BLI-2",
                project_dir=str(project_dir),
                semgrep_sarif=str(semgrep_sarif),
                trufflehog_json=str(trufflehog_json),
            )

        self.assertEqual(response["policy"]["action"], "allow")
        self.assertEqual(response["result"]["status"], "pass")
        self.assertEqual(response["result"]["stage"], "security_gate")

    def test_mcp_server_can_be_created(self) -> None:
        server = create_mcp_server(policy=ToolPolicy(allowed_roots=(Path.cwd(),)))

        self.assertEqual(server.name, "paperclip-workflow-controller")

    def test_mcp_server_lists_registered_tools(self) -> None:
        async def run_check() -> set[str]:
            server = create_mcp_server(policy=ToolPolicy(allowed_roots=(Path.cwd(),)))
            tools = await server.list_tools()
            return {tool.name for tool in tools}

        names = asyncio.run(run_check())

        self.assertEqual(
            names,
            {
                "workflow_run_issue_gates",
                "workflow_plan_issue_flow",
                "workflow_sync_issue_state",
                "workflow_verify_artifacts",
                "workflow_verify_security",
                "workflow_export_schemas",
            },
        )

    def test_mcp_server_can_call_verify_artifacts_tool(self) -> None:
        async def run_check(root: Path, project_dir: Path) -> dict:
            server = create_mcp_server(policy=ToolPolicy(allowed_roots=(root,)))
            _, structured = await server.call_tool(
                "workflow_verify_artifacts",
                {"issue_id": "BLI-2", "project_dir": str(project_dir)},
            )
            return structured

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "project"
            project_dir.mkdir()
            self._write_valid_artifacts(project_dir)

            structured = asyncio.run(run_check(root, project_dir))

        self.assertEqual(structured["policy"]["action"], "allow")
        self.assertEqual(structured["result"]["status"], "pass")

    def _write_valid_artifacts(self, project_dir: Path) -> None:
        (project_dir / "test-results.json").write_text(
            json.dumps({"summary": {"passed": 15, "failed": 0}}),
            encoding="utf-8",
        )
        (project_dir / "coverage.xml").write_text(
            '<?xml version="1.0" ?><coverage line-rate="0.82"></coverage>',
            encoding="utf-8",
        )
        (project_dir / "README.md").write_text(
            "# BLI-2\n\nInstall dependencies.\n\nRun the app.\n\nTest with pytest.\n",
            encoding="utf-8",
        )

    def _write_clean_sarif(self, path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
                    "version": "2.1.0",
                    "runs": [
                        {
                            "tool": {"driver": {"name": "Semgrep", "rules": []}},
                            "results": [],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
