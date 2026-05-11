import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_controller.artifact_gate import verify_artifacts, write_event


class ArtifactGateTests(unittest.TestCase):
    def test_blocks_when_project_directory_is_missing(self) -> None:
        verdict = verify_artifacts(
            issue_id="BLI-2",
            project_dir=Path("does-not-exist"),
            min_tests=15,
            min_coverage=80.0,
        )

        self.assertEqual(verdict.status, "blocked")
        self.assertEqual(verdict.reason, "project directory missing")
        self.assertTrue(any(check.name == "project_dir" for check in verdict.checks))

    def test_blocks_when_required_artifacts_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            (project_dir / "test-results.json").write_text(
                json.dumps({"summary": {"passed": 15, "failed": 0}}),
                encoding="utf-8",
            )

            verdict = verify_artifacts(
                issue_id="BLI-2",
                project_dir=project_dir,
                min_tests=15,
                min_coverage=80.0,
            )

        self.assertEqual(verdict.status, "blocked")
        self.assertEqual(verdict.reason, "required artifact missing")
        missing = [check.name for check in verdict.checks if check.status == "blocked"]
        self.assertIn("coverage.xml", missing)
        self.assertIn("README.md", missing)

    def test_fails_when_test_results_report_failed_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            self._write_valid_readme(project_dir)
            self._write_coverage(project_dir, line_rate="0.95")
            (project_dir / "test-results.json").write_text(
                json.dumps({"summary": {"passed": 14, "failed": 1}}),
                encoding="utf-8",
            )

            verdict = verify_artifacts(
                issue_id="BLI-2",
                project_dir=project_dir,
                min_tests=15,
                min_coverage=80.0,
            )

        self.assertEqual(verdict.status, "fail")
        self.assertEqual(verdict.reason, "artifact checks failed")
        test_check = next(check for check in verdict.checks if check.name == "test-results.json")
        self.assertIn("failed=1", test_check.message)

    def test_fails_when_coverage_is_below_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            self._write_valid_readme(project_dir)
            self._write_tests(project_dir, passed=15, failed=0)
            self._write_coverage(project_dir, line_rate="0.799")

            verdict = verify_artifacts(
                issue_id="BLI-2",
                project_dir=project_dir,
                min_tests=15,
                min_coverage=80.0,
            )

        self.assertEqual(verdict.status, "fail")
        coverage_check = next(check for check in verdict.checks if check.name == "coverage.xml")
        self.assertIn("79.90%", coverage_check.message)

    def test_passes_with_required_artifacts_and_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            self._write_valid_readme(project_dir)
            self._write_tests(project_dir, passed=16, failed=0)
            self._write_coverage(project_dir, line_rate="0.875")

            verdict = verify_artifacts(
                issue_id="BLI-2",
                project_dir=project_dir,
                min_tests=15,
                min_coverage=80.0,
            )

        self.assertEqual(verdict.status, "pass")
        self.assertEqual(verdict.reason, "all artifact checks passed")

    def test_writes_jsonl_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            project_dir = tmp_path / "project"
            project_dir.mkdir()
            self._write_valid_readme(project_dir)
            self._write_tests(project_dir, passed=15, failed=0)
            self._write_coverage(project_dir, line_rate="0.82")
            event_log = tmp_path / "events.jsonl"

            verdict = verify_artifacts(
                issue_id="BLI-2",
                project_dir=project_dir,
                min_tests=15,
                min_coverage=80.0,
            )
            write_event(verdict, event_log)

            event = json.loads(event_log.read_text(encoding="utf-8").strip())

        self.assertEqual(event["issue_id"], "BLI-2")
        self.assertEqual(event["stage"], "artifact_gate")
        self.assertEqual(event["status"], "pass")
        self.assertEqual(event["checks"]["coverage.xml"]["status"], "pass")

    def _write_tests(self, project_dir: Path, passed: int, failed: int) -> None:
        (project_dir / "test-results.json").write_text(
            json.dumps({"summary": {"passed": passed, "failed": failed}}),
            encoding="utf-8",
        )

    def _write_coverage(self, project_dir: Path, line_rate: str) -> None:
        (project_dir / "coverage.xml").write_text(
            f'<?xml version="1.0" ?><coverage line-rate="{line_rate}"></coverage>',
            encoding="utf-8",
        )

    def _write_valid_readme(self, project_dir: Path) -> None:
        (project_dir / "README.md").write_text(
            "# BLI-2\n\nInstall dependencies.\n\nRun the app.\n\nTest with pytest.\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
