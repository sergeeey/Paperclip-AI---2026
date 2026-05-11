import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_controller.cli import main
from workflow_controller.issue_runner import run_issue_gates


FIXTURES = Path(__file__).resolve().parent / "fixtures"


class IssueRunnerTests(unittest.TestCase):
    def test_passes_clean_fixture_and_writes_gate_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = FIXTURES / "clean-project"
            event_log = Path(tmp) / "events.jsonl"

            run = run_issue_gates(
                issue_id="FIX-1",
                project_dir=project_dir,
                semgrep_sarif=project_dir / "semgrep.sarif",
                trufflehog_json=project_dir / "trufflehog.jsonl",
                event_log=event_log,
            )
            events = self._read_events(event_log)

        self.assertEqual(run.final.status, "pass")
        self.assertEqual(run.final.stage, "issue_gates")
        self.assertEqual([event["stage"] for event in events], ["artifact_gate", "security_gate", "issue_gates"])

    def test_fails_vulnerable_fixture(self) -> None:
        project_dir = FIXTURES / "vulnerable-project"

        run = run_issue_gates(
            issue_id="FIX-2",
            project_dir=project_dir,
            semgrep_sarif=project_dir / "semgrep.sarif",
            trufflehog_json=project_dir / "trufflehog.jsonl",
        )

        self.assertEqual(run.final.status, "fail")
        self.assertEqual(run.final.reason, "security gate failed")
        security_check = next(check for check in run.final.checks if check.name == "security_gate")
        self.assertEqual(security_check.observed["status"], "fail")

    def test_stops_before_security_when_artifacts_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = FIXTURES / "missing-artifacts-project"
            event_log = Path(tmp) / "events.jsonl"

            run = run_issue_gates(
                issue_id="FIX-3",
                project_dir=project_dir,
                semgrep_sarif=project_dir / "semgrep.sarif",
                trufflehog_json=project_dir / "trufflehog.jsonl",
                event_log=event_log,
            )
            events = self._read_events(event_log)

        self.assertEqual(run.final.status, "blocked")
        self.assertEqual(run.final.reason, "artifact gate blocked")
        self.assertEqual([event["stage"] for event in events], ["artifact_gate", "issue_gates"])

    def test_cli_run_issue_gates_exit_codes(self) -> None:
        clean = FIXTURES / "clean-project"
        vulnerable = FIXTURES / "vulnerable-project"
        missing = FIXTURES / "missing-artifacts-project"

        with redirect_stdout(StringIO()):
            clean_exit = main(
                [
                    "run-issue-gates",
                    "FIX-1",
                    "--project-dir",
                    str(clean),
                    "--semgrep-sarif",
                    str(clean / "semgrep.sarif"),
                    "--trufflehog-json",
                    str(clean / "trufflehog.jsonl"),
                    "--json",
                ]
            )
            vulnerable_exit = main(
                [
                    "run-issue-gates",
                    "FIX-2",
                    "--project-dir",
                    str(vulnerable),
                    "--semgrep-sarif",
                    str(vulnerable / "semgrep.sarif"),
                    "--trufflehog-json",
                    str(vulnerable / "trufflehog.jsonl"),
                    "--json",
                ]
            )
            missing_exit = main(
                [
                    "run-issue-gates",
                    "FIX-3",
                    "--project-dir",
                    str(missing),
                    "--semgrep-sarif",
                    str(missing / "semgrep.sarif"),
                    "--trufflehog-json",
                    str(missing / "trufflehog.jsonl"),
                    "--json",
                ]
            )

        self.assertEqual(clean_exit, 0)
        self.assertEqual(vulnerable_exit, 2)
        self.assertEqual(missing_exit, 3)

    def _read_events(self, event_log: Path) -> list[dict]:
        return [
            json.loads(line)
            for line in event_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


if __name__ == "__main__":
    unittest.main()
