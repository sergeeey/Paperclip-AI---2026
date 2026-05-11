import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_controller.security_gate import _sanitize_trufflehog_jsonl, verify_security_scans


class SecurityGateTests(unittest.TestCase):
    def test_passes_with_clean_semgrep_sarif_and_empty_trufflehog_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            semgrep_sarif = project_dir / "semgrep.sarif"
            trufflehog_json = project_dir / "trufflehog.jsonl"
            self._write_sarif(semgrep_sarif, results=[])
            trufflehog_json.write_text("", encoding="utf-8")

            verdict = verify_security_scans(
                issue_id="BLI-2",
                project_dir=project_dir,
                semgrep_sarif=semgrep_sarif,
                trufflehog_json=trufflehog_json,
            )

        self.assertEqual(verdict.status, "pass")
        self.assertEqual(verdict.stage, "security_gate")

    def test_fails_when_semgrep_sarif_contains_blocking_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            semgrep_sarif = project_dir / "semgrep.sarif"
            trufflehog_json = project_dir / "trufflehog.jsonl"
            self._write_sarif(
                semgrep_sarif,
                results=[
                    {
                        "ruleId": "python.lang.security.audit.eval-use",
                        "level": "error",
                        "message": {"text": "Avoid eval."},
                    }
                ],
            )
            trufflehog_json.write_text("", encoding="utf-8")

            verdict = verify_security_scans(
                issue_id="BLI-2",
                project_dir=project_dir,
                semgrep_sarif=semgrep_sarif,
                trufflehog_json=trufflehog_json,
            )

        self.assertEqual(verdict.status, "fail")
        semgrep_check = next(check for check in verdict.checks if check.name == "semgrep.sarif")
        self.assertEqual(semgrep_check.observed["blocking_results"], 1)

    def test_fails_when_trufflehog_reports_verified_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            semgrep_sarif = project_dir / "semgrep.sarif"
            trufflehog_json = project_dir / "trufflehog.jsonl"
            self._write_sarif(semgrep_sarif, results=[])
            trufflehog_json.write_text(
                json.dumps(
                    {
                        "DetectorName": "SyntheticDetector",
                        "Verified": True,
                        "SourceMetadata": {
                            "Data": {"Filesystem": {"file": "config.env"}}
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            verdict = verify_security_scans(
                issue_id="BLI-2",
                project_dir=project_dir,
                semgrep_sarif=semgrep_sarif,
                trufflehog_json=trufflehog_json,
            )

        self.assertEqual(verdict.status, "fail")
        trufflehog_check = next(check for check in verdict.checks if check.name == "trufflehog.jsonl")
        self.assertEqual(trufflehog_check.observed["verified_results"], 1)

    def test_blocks_when_required_security_artifact_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            verdict = verify_security_scans(
                issue_id="BLI-2",
                project_dir=project_dir,
                semgrep_sarif=project_dir / "missing.sarif",
                trufflehog_json=project_dir / "missing.jsonl",
            )

        self.assertEqual(verdict.status, "blocked")
        missing = [check.name for check in verdict.checks if check.status == "blocked"]
        self.assertIn("semgrep.sarif", missing)
        self.assertIn("trufflehog.jsonl", missing)

    def test_sanitizes_trufflehog_output_before_persisting(self) -> None:
        raw_output = (
            json.dumps(
                {
                    "DetectorName": "SyntheticDetector",
                    "Verified": True,
                    "Raw": "synthetic-secret-value",
                    "RawV2": "synthetic-secret-value-v2",
                    "ExtraData": {"token": "synthetic-token-value"},
                }
            )
            + "\n"
        )

        sanitized = _sanitize_trufflehog_jsonl(raw_output)
        payload = json.loads(sanitized)

        self.assertNotIn("synthetic-secret-value", sanitized)
        self.assertEqual(payload["Raw"], "[REDACTED]")
        self.assertEqual(payload["RawV2"], "[REDACTED]")
        self.assertEqual(payload["ExtraData"]["token"], "[REDACTED]")

    def _write_sarif(self, path: Path, *, results: list[dict]) -> None:
        path.write_text(
            json.dumps(
                {
                    "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
                    "version": "2.1.0",
                    "runs": [
                        {
                            "tool": {"driver": {"name": "Semgrep", "rules": []}},
                            "results": results,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
