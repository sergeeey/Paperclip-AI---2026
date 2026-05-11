import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_controller.event_log import verify_event_log
from workflow_controller.issue_runner import run_issue_gates_from_issue
from workflow_controller.models import IssueModel


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "issues"


class EventLogTests(unittest.TestCase):
    def test_valid_clean_event_log_passes(self) -> None:
        issue_file = FIXTURES / "clean-issue.json"
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmp:
            event_log = Path(tmp) / "events.jsonl"
            run_issue_gates_from_issue(issue, issue_file=issue_file, event_log=event_log)

            verdict = verify_event_log(event_log=event_log)

        self.assertEqual(verdict.status, "pass")
        self.assertEqual(verdict.stage, "event_log_gate")

    def test_valid_blocked_event_log_passes(self) -> None:
        issue_file = FIXTURES / "blocked-issue.json"
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmp:
            event_log = Path(tmp) / "events.jsonl"
            run_issue_gates_from_issue(issue, issue_file=issue_file, event_log=event_log)

            verdict = verify_event_log(event_log=event_log)

        self.assertEqual(verdict.status, "pass")

    def test_empty_event_log_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            event_log = Path(tmp) / "events.jsonl"
            event_log.write_text("", encoding="utf-8")

            verdict = verify_event_log(event_log=event_log)

        self.assertEqual(verdict.status, "blocked")
        self.assertEqual(verdict.reason, "event log empty")

    def test_malformed_event_log_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            event_log = Path(tmp) / "events.jsonl"
            event_log.write_text("{not-json}\n", encoding="utf-8")

            verdict = verify_event_log(event_log=event_log)

        self.assertEqual(verdict.status, "fail")
        self.assertIn("invalid JSON", verdict.reason)

    def test_out_of_order_event_log_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            event_log = Path(tmp) / "events.jsonl"
            event_log.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-05-10T00:00:00Z",
                                "stage": "issue_gates",
                                "issue_id": "FIX-1",
                                "status": "pass",
                                "reason": "all issue gates passed",
                                "checks": {},
                            }
                        ),
                        json.dumps(
                            {
                                "timestamp": "2026-05-10T00:00:01Z",
                                "stage": "artifact_gate",
                                "issue_id": "FIX-1",
                                "status": "pass",
                                "reason": "all artifact checks passed",
                                "checks": {},
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            verdict = verify_event_log(event_log=event_log)

        self.assertEqual(verdict.status, "fail")
        self.assertIn("invalid stage sequence", verdict.reason)

    def test_cli_verify_event_log_exit_codes(self) -> None:
        issue_file = FIXTURES / "clean-issue.json"
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmp:
            event_log = Path(tmp) / "events.jsonl"
            run_issue_gates_from_issue(issue, issue_file=issue_file, event_log=event_log)

            with redirect_stdout(StringIO()):
                from workflow_controller.cli import main

                clean_exit = main(["verify-event-log", "--event-log", str(event_log), "--json"])
                missing_exit = main(
                    [
                        "verify-event-log",
                        "--event-log",
                        str(Path(tmp) / "missing.jsonl"),
                        "--json",
                    ]
                )

        self.assertEqual(clean_exit, 0)
        self.assertEqual(missing_exit, 3)


if __name__ == "__main__":
    unittest.main()
