from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .artifact_gate import verify_artifacts, write_event
from .event_log import verify_event_log
from .issue_flow import build_issue_flow_plan
from .issue_runner import run_issue_gates, run_issue_gates_from_issue
from .issue_state import sync_issue_state, write_issue_state
from .models import GateVerdict, IssueModel, export_json_schemas
from .security_gate import verify_security_scans


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify-artifacts":
        project_dir = args.project_dir or Path("/tmp/projects") / args.issue_id
        verdict = verify_artifacts(
            issue_id=args.issue_id,
            project_dir=project_dir,
            min_tests=args.min_tests,
            min_coverage=args.min_coverage,
        )
        if args.event_log is not None:
            write_event(verdict, args.event_log)
        _print_verdict(verdict, as_json=args.json)
        return _exit_code(verdict.status)

    if args.command == "verify-security":
        project_dir = args.project_dir or Path("/tmp/projects") / args.issue_id
        verdict = verify_security_scans(
            issue_id=args.issue_id,
            project_dir=project_dir,
            semgrep_sarif=args.semgrep_sarif,
            trufflehog_json=args.trufflehog_json,
            run_semgrep=args.run_semgrep,
            semgrep_config=args.semgrep_config,
            run_trufflehog=args.run_trufflehog,
            scan_output_dir=args.scan_output_dir,
            semgrep_block_levels=tuple(args.semgrep_block_level),
            block_trufflehog_unknown=not args.allow_trufflehog_unknown,
            timeout_seconds=args.timeout_seconds,
        )
        if args.event_log is not None:
            write_event(verdict, args.event_log)
        _print_verdict(verdict, as_json=args.json)
        return _exit_code(verdict.status)

    if args.command == "export-schemas":
        paths = export_json_schemas(args.output_dir)
        if args.json:
            print(json.dumps([str(path) for path in paths], indent=2))
        else:
            for path in paths:
                print(path)
        return 0

    if args.command == "run-issue-gates":
        project_dir = args.project_dir or Path("/tmp/projects") / args.issue_id
        run = run_issue_gates(
            issue_id=args.issue_id,
            project_dir=project_dir,
            min_tests=args.min_tests,
            min_coverage=args.min_coverage,
            semgrep_sarif=args.semgrep_sarif,
            trufflehog_json=args.trufflehog_json,
            run_semgrep=args.run_semgrep,
            semgrep_config=args.semgrep_config,
            run_trufflehog=args.run_trufflehog,
            scan_output_dir=args.scan_output_dir,
            semgrep_block_levels=tuple(args.semgrep_block_level),
            block_trufflehog_unknown=not args.allow_trufflehog_unknown,
            timeout_seconds=args.timeout_seconds,
            event_log=args.event_log,
        )
        _print_run(run, as_json=args.json)
        return _exit_code(run.final.status)

    if args.command == "run-issue-gates-from-issue":
        issue_file = args.issue_file
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))
        run = run_issue_gates_from_issue(
            issue,
            issue_file=issue_file,
            event_log=args.event_log,
        )
        _print_run(run, as_json=args.json)
        return _exit_code(run.final.status)

    if args.command == "verify-event-log":
        verdict = verify_event_log(
            event_log=args.event_log,
            expected_issue_id=args.expected_issue_id,
        )
        _print_verdict(verdict, as_json=args.json)
        return _exit_code(verdict.status)

    if args.command == "sync-issue-state":
        issue_file = args.issue_file
        issue = IssueModel.model_validate_json(issue_file.read_text(encoding="utf-8"))
        run = run_issue_gates_from_issue(
            issue,
            issue_file=issue_file,
            event_log=args.event_log,
        )
        updated = sync_issue_state(issue, final_run=run, event_log=args.event_log)
        output_file = args.output_file or issue_file
        write_issue_state(updated, issue_file=output_file)
        _print_run(run, as_json=args.json)
        return _exit_code(run.final.status)

    if args.command == "plan-issue-flow":
        issue = IssueModel.model_validate_json(args.issue_file.read_text(encoding="utf-8"))
        plan = build_issue_flow_plan(issue)
        _print_plan(plan, as_json=args.json)
        return 0

    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workflow-controller",
        description="Artifact-driven workflow gates for Paperclip issues.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser(
        "verify-artifacts",
        help="Verify Builder artifacts before advancing an issue.",
    )
    verify_parser.add_argument("issue_id", help="Issue identifier, for example BLI-2.")
    verify_parser.add_argument(
        "--project-dir",
        type=Path,
        help="Directory containing issue artifacts. Defaults to /tmp/projects/{issue_id}.",
    )
    verify_parser.add_argument(
        "--min-tests",
        type=int,
        default=15,
        help="Minimum number of passing tests required.",
    )
    verify_parser.add_argument(
        "--min-coverage",
        type=float,
        default=80.0,
        help="Minimum line coverage percentage required.",
    )
    verify_parser.add_argument(
        "--event-log",
        type=Path,
        help="Append a JSONL event to this path.",
    )
    verify_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full verdict event as JSON.",
    )

    security_parser = subparsers.add_parser(
        "verify-security",
        help="Verify Scanner security outputs before deployment/reporting.",
    )
    security_parser.add_argument("issue_id", help="Issue identifier, for example BLI-2.")
    security_parser.add_argument(
        "--project-dir",
        type=Path,
        help="Directory containing issue artifacts. Defaults to /tmp/projects/{issue_id}.",
    )
    security_parser.add_argument(
        "--semgrep-sarif",
        type=Path,
        help="Existing Semgrep SARIF artifact to validate.",
    )
    security_parser.add_argument(
        "--trufflehog-json",
        type=Path,
        help="Existing TruffleHog JSONL artifact to validate.",
    )
    security_parser.add_argument(
        "--run-semgrep",
        action="store_true",
        help="Run semgrep scan and validate the generated SARIF.",
    )
    security_parser.add_argument(
        "--semgrep-config",
        default="auto",
        help="Semgrep config path or registry config. Defaults to auto.",
    )
    security_parser.add_argument(
        "--run-trufflehog",
        action="store_true",
        help="Run trufflehog filesystem scan and validate the generated JSONL.",
    )
    security_parser.add_argument(
        "--scan-output-dir",
        type=Path,
        help="Directory for generated scanner artifacts. Defaults to project/.paperclip-security.",
    )
    security_parser.add_argument(
        "--semgrep-block-level",
        action="append",
        default=["error", "warning"],
        choices=("error", "warning", "note", "none"),
        help="SARIF level that fails the gate. Can be passed multiple times.",
    )
    security_parser.add_argument(
        "--allow-trufflehog-unknown",
        action="store_true",
        help="Only fail TruffleHog verified findings; ignore unknown findings.",
    )
    security_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="Timeout for each scanner process.",
    )
    security_parser.add_argument(
        "--event-log",
        type=Path,
        help="Append a JSONL event to this path.",
    )
    security_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full verdict event as JSON.",
    )

    schema_parser = subparsers.add_parser(
        "export-schemas",
        help="Export Pydantic JSON Schemas for validation hooks.",
    )
    schema_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".paperclip") / "schemas",
        help="Directory where schema files are written.",
    )
    schema_parser.add_argument(
        "--json",
        action="store_true",
        help="Print written schema paths as JSON.",
    )

    run_parser = subparsers.add_parser(
        "run-issue-gates",
        help="Run artifact and security gates as one issue-level pipeline.",
    )
    run_parser.add_argument("issue_id", help="Issue identifier, for example BLI-2.")
    run_parser.add_argument(
        "--project-dir",
        type=Path,
        help="Directory containing issue artifacts. Defaults to /tmp/projects/{issue_id}.",
    )
    run_parser.add_argument(
        "--min-tests",
        type=int,
        default=15,
        help="Minimum number of passing tests required.",
    )
    run_parser.add_argument(
        "--min-coverage",
        type=float,
        default=80.0,
        help="Minimum line coverage percentage required.",
    )
    run_parser.add_argument(
        "--semgrep-sarif",
        type=Path,
        help="Existing Semgrep SARIF artifact to validate.",
    )
    run_parser.add_argument(
        "--trufflehog-json",
        type=Path,
        help="Existing TruffleHog JSONL artifact to validate.",
    )
    run_parser.add_argument(
        "--run-semgrep",
        action="store_true",
        help="Run semgrep scan and validate the generated SARIF.",
    )
    run_parser.add_argument(
        "--semgrep-config",
        default="auto",
        help="Semgrep config path or registry config. Defaults to auto.",
    )
    run_parser.add_argument(
        "--run-trufflehog",
        action="store_true",
        help="Run trufflehog filesystem scan and validate the generated JSONL.",
    )
    run_parser.add_argument(
        "--scan-output-dir",
        type=Path,
        help="Directory for generated scanner artifacts. Defaults to project/.paperclip-security.",
    )
    run_parser.add_argument(
        "--semgrep-block-level",
        action="append",
        default=["error", "warning"],
        choices=("error", "warning", "note", "none"),
        help="SARIF level that fails the gate. Can be passed multiple times.",
    )
    run_parser.add_argument(
        "--allow-trufflehog-unknown",
        action="store_true",
        help="Only fail TruffleHog verified findings; ignore unknown findings.",
    )
    run_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="Timeout for each scanner process.",
    )
    run_parser.add_argument(
        "--event-log",
        type=Path,
        help="Append JSONL events for each gate and the final issue verdict.",
    )
    run_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full issue gate run as JSON.",
    )

    issue_file_parser = subparsers.add_parser(
        "run-issue-gates-from-issue",
        help="Load an issue JSON file and run the issue-level pipeline.",
    )
    issue_file_parser.add_argument(
        "--issue-file",
        type=Path,
        required=True,
        help="Path to a strict issue JSON file.",
    )
    issue_file_parser.add_argument(
        "--event-log",
        type=Path,
        help="Override the issue file event log path if provided.",
    )
    issue_file_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full issue gate run as JSON.",
    )

    event_log_parser = subparsers.add_parser(
        "verify-event-log",
        help="Verify JSONL event log structure and verdict consistency.",
    )
    event_log_parser.add_argument(
        "--event-log",
        type=Path,
        required=True,
        help="Path to the JSONL event log.",
    )
    event_log_parser.add_argument(
        "--expected-issue-id",
        type=str,
        help="Optional issue ID that all events must match.",
    )
    event_log_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full event-log verdict as JSON.",
    )

    sync_parser = subparsers.add_parser(
        "sync-issue-state",
        help="Run issue gates and write the updated issue state back to JSON.",
    )
    sync_parser.add_argument(
        "--issue-file",
        type=Path,
        required=True,
        help="Path to a strict issue JSON file.",
    )
    sync_parser.add_argument(
        "--output-file",
        type=Path,
        help="Optional output file. Defaults to overwriting the input issue file.",
    )
    sync_parser.add_argument(
        "--event-log",
        type=Path,
        help="Append gate events to this path.",
    )
    sync_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full issue gate run as JSON.",
    )

    plan_parser = subparsers.add_parser(
        "plan-issue-flow",
        help="Build a deterministic CEO→Builder→Scanner→Reporter→DevOps plan from an issue file.",
    )
    plan_parser.add_argument(
        "--issue-file",
        type=Path,
        required=True,
        help="Path to a strict issue JSON file.",
    )
    plan_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full issue flow plan as JSON.",
    )

    return parser


def _print_verdict(verdict: GateVerdict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(verdict.to_event(), indent=2, sort_keys=True))
        return

    print(f"{verdict.issue_id}: {verdict.status.upper()} - {verdict.reason}")
    for check in verdict.checks:
        print(f"- {check.name}: {check.status} ({check.message})")


def _print_run(run, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(run.to_dict(), indent=2, sort_keys=True))
        return

    print(f"{run.issue_id}: {run.final.status.upper()} - {run.final.reason}")
    for gate in run.gates:
        print(f"- {gate.stage}: {gate.status} ({gate.reason})")


def _print_plan(plan, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(plan.model_dump(mode="json", exclude_none=True), indent=2, sort_keys=True))
        return

    print(f"{plan.issue_id}: {plan.summary}")
    for step in plan.steps:
        print(f"- {step.stage}: {step.status} -> {step.owner} ({step.action})")


def _exit_code(status: str) -> int:
    if status == "pass":
        return 0
    if status == "fail":
        return 2
    if status == "blocked":
        return 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
