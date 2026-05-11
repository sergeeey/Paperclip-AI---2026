import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_controller.cli import main
from workflow_controller.models import IssueModel
from workflow_controller.issue_runner import run_issue_gates_from_issue


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "issues"


class IssueFromIssueTests(unittest.TestCase):
    def test_issue_model_accepts_execution_block(self) -> None:
        issue = IssueModel.model_validate_json((FIXTURES / "clean-issue.json").read_text(encoding="utf-8"))

        self.assertEqual(issue.issue_id, "FIX-1")
        self.assertIsNotNone(issue.execution)
        self.assertEqual(issue.execution.semgrep_sarif, "../clean-project/semgrep.sarif")

    def test_issue_file_runner_passes_clean_issue(self) -> None:
        issue_file = FIXTURES / "clean-issue.json"
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmp:
            event_log = Path(tmp) / "events.jsonl"
            run = run_issue_gates_from_issue(issue, issue_file=issue_file, event_log=event_log)
            events = self._read_events(event_log)

        self.assertEqual(run.final.status, "pass")
        self.assertEqual(events[-1]["stage"], "issue_gates")
        self.assertEqual(events[-1]["status"], "pass")

    def test_issue_file_runner_fails_vulnerable_issue(self) -> None:
        issue_file = FIXTURES / "vulnerable-issue.json"
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))

        run = run_issue_gates_from_issue(issue, issue_file=issue_file)

        self.assertEqual(run.final.status, "fail")
        self.assertEqual(run.final.reason, "security gate failed")

    def test_issue_file_runner_blocks_missing_artifacts_issue(self) -> None:
        issue_file = FIXTURES / "blocked-issue.json"
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))

        run = run_issue_gates_from_issue(issue, issue_file=issue_file)

        self.assertEqual(run.final.status, "blocked")
        self.assertEqual(run.final.reason, "artifact gate blocked")

    def test_cli_run_issue_gates_from_issue_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            event_log = Path(tmp) / "events.jsonl"
            with redirect_stdout(StringIO()):
                clean_exit = main(
                    [
                        "run-issue-gates-from-issue",
                        "--issue-file",
                        str(FIXTURES / "clean-issue.json"),
                        "--event-log",
                        str(event_log),
                        "--json",
                    ]
                )
                vulnerable_exit = main(
                    [
                        "run-issue-gates-from-issue",
                        "--issue-file",
                        str(FIXTURES / "vulnerable-issue.json"),
                        "--event-log",
                        str(event_log),
                        "--json",
                    ]
                )
                blocked_exit = main(
                    [
                        "run-issue-gates-from-issue",
                        "--issue-file",
                        str(FIXTURES / "blocked-issue.json"),
                        "--event-log",
                        str(event_log),
                        "--json",
                    ]
                )

        self.assertEqual(clean_exit, 0)
        self.assertEqual(vulnerable_exit, 2)
        self.assertEqual(blocked_exit, 3)

    def _read_events(self, event_log: Path) -> list[dict]:
        return [
            json.loads(line)
            for line in event_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


if __name__ == "__main__":
    unittest.main()
