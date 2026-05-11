import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_controller.cli import main
from workflow_controller.issue_runner import run_issue_gates_from_issue
from workflow_controller.issue_state import sync_issue_state, write_issue_state
from workflow_controller.models import IssueModel


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "issues"


class IssueStateTests(unittest.TestCase):
    def test_sync_issue_state_marks_done_on_pass(self) -> None:
        issue_file = FIXTURES / "clean-issue.json"
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmp:
            event_log = Path(tmp) / "events.jsonl"
            run = run_issue_gates_from_issue(issue, issue_file=issue_file, event_log=event_log)
            updated = sync_issue_state(issue, final_run=run, event_log=event_log)

        self.assertEqual(updated.status, "done")
        self.assertEqual(updated.execution.last_run_status, "pass")
        self.assertEqual(updated.execution.last_event_log, str(event_log))

    def test_sync_issue_state_marks_in_progress_on_fail(self) -> None:
        issue_file = FIXTURES / "vulnerable-issue.json"
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))

        run = run_issue_gates_from_issue(issue, issue_file=issue_file)
        updated = sync_issue_state(issue, final_run=run)

        self.assertEqual(updated.status, "in_progress")
        self.assertEqual(updated.execution.last_run_status, "fail")

    def test_sync_issue_state_marks_blocked_on_block(self) -> None:
        issue_file = FIXTURES / "blocked-issue.json"
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))

        run = run_issue_gates_from_issue(issue, issue_file=issue_file)
        updated = sync_issue_state(issue, final_run=run)

        self.assertEqual(updated.status, "blocked")
        self.assertEqual(updated.execution.last_run_status, "blocked")

    def test_write_issue_state_round_trips_json(self) -> None:
        issue_file = FIXTURES / "clean-issue.json"
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "issue.json"
            write_issue_state(issue, issue_file=path)
            reloaded = IssueModel.model_validate_json(path.read_text(encoding="utf-8"))

        self.assertEqual(reloaded.issue_id, "FIX-1")
        self.assertEqual(reloaded.status, "todo")

    def test_cli_sync_issue_state_exit_code(self) -> None:
        issue_file = FIXTURES / "clean-issue.json"
        with tempfile.TemporaryDirectory() as tmp:
            output_file = Path(tmp) / "synced-issue.json"
            event_log = Path(tmp) / "events.jsonl"
            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "sync-issue-state",
                        "--issue-file",
                        str(issue_file),
                        "--output-file",
                        str(output_file),
                        "--event-log",
                        str(event_log),
                        "--json",
                    ]
                )
            synced = IssueModel.model_validate_json(output_file.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(synced.status, "done")
        self.assertEqual(synced.execution.last_run_status, "pass")


if __name__ == "__main__":
    unittest.main()
