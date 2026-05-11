from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

PolicyAction = Literal["allow", "block", "require_approval"]

DEFAULT_ALLOWED_TOOLS = (
    "workflow_run_issue_gates",
    "workflow_plan_issue_flow",
    "workflow_sync_issue_state",
    "workflow_verify_artifacts",
    "workflow_verify_security",
    "workflow_export_schemas",
)

PATH_ARGUMENT_NAMES = {
    "issue_file",
    "project_dir",
    "semgrep_sarif",
    "trufflehog_json",
    "scan_output_dir",
    "output_dir",
    "event_log",
}


class ToolPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed_tools: tuple[str, ...] = DEFAULT_ALLOWED_TOOLS
    blocked_tools: tuple[str, ...] = ()
    require_approval_tools: tuple[str, ...] = ()
    allowed_roots: tuple[Path, ...] = Field(default_factory=lambda: _default_allowed_roots())

    @field_serializer("allowed_roots")
    def _serialize_allowed_roots(self, value: tuple[Path, ...]) -> list[str]:
        return [str(path) for path in value]


class PolicyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_name: str
    action: PolicyAction
    reason: str
    matched_rule: str
    checked_paths: tuple[str, ...] = ()


def evaluate_tool_request(
    tool_name: str,
    arguments: dict[str, Any],
    *,
    policy: ToolPolicy | None = None,
) -> PolicyDecision:
    policy = policy or ToolPolicy()

    if tool_name in policy.blocked_tools:
        return PolicyDecision(
            tool_name=tool_name,
            action="block",
            reason=f"tool {tool_name!r} is explicitly blocked",
            matched_rule="blocked_tools",
        )

    if policy.allowed_tools and tool_name not in policy.allowed_tools:
        return PolicyDecision(
            tool_name=tool_name,
            action="block",
            reason=f"tool {tool_name!r} is not in allow list",
            matched_rule="allowed_tools",
        )

    path_decision = _evaluate_paths(tool_name, arguments, policy)
    if path_decision is not None:
        return path_decision

    if tool_name in policy.require_approval_tools:
        return PolicyDecision(
            tool_name=tool_name,
            action="require_approval",
            reason=f"tool {tool_name!r} requires approval",
            matched_rule="require_approval_tools",
        )

    return PolicyDecision(
        tool_name=tool_name,
        action="allow",
        reason="tool request allowed by policy",
        matched_rule="allowed_tools",
        checked_paths=tuple(_stringify_checked_paths(arguments)),
    )


def default_policy() -> ToolPolicy:
    return ToolPolicy()


def _evaluate_paths(
    tool_name: str,
    arguments: dict[str, Any],
    policy: ToolPolicy,
) -> PolicyDecision | None:
    allowed_roots = tuple(_resolve_path(path) for path in policy.allowed_roots)
    checked_paths: list[str] = []

    for name, value in arguments.items():
        if name not in PATH_ARGUMENT_NAMES or value in (None, ""):
            continue

        path = _resolve_path(Path(value))
        checked_paths.append(str(path))
        if not _is_under_allowed_root(path, allowed_roots):
            roots = ", ".join(str(root) for root in allowed_roots)
            return PolicyDecision(
                tool_name=tool_name,
                action="block",
                reason=f"path argument {name!r} is outside allowed roots: {path}",
                matched_rule="allowed_roots",
                checked_paths=tuple(checked_paths + [f"allowed_roots={roots}"]),
            )

    return None


def _stringify_checked_paths(arguments: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for name, value in arguments.items():
        if name in PATH_ARGUMENT_NAMES and value not in (None, ""):
            paths.append(str(_resolve_path(Path(value))))
    return paths


def _is_under_allowed_root(path: Path, allowed_roots: tuple[Path, ...]) -> bool:
    return any(_is_relative_to(path, root) for root in allowed_roots)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _default_allowed_roots() -> tuple[Path, ...]:
    roots = [
        Path.cwd(),
        Path(tempfile.gettempdir()),
        Path("/tmp/projects"),
    ]
    return tuple(_resolve_path(root) for root in roots)
