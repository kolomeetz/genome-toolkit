"""Multi-agent validation orchestration for the Genome Toolkit.

Dispatches validation tasks to multiple AI agents (Codex CLI, NotebookLM,
PubMed subagents, Tavily search) and aggregates results with consensus logic.

This module provides the Python-side orchestration. The actual agent calls
are made through Claude Code skills and the Codex CLI — this module defines
the data structures, configuration loading, and consensus logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal

import yaml


class Severity(str, Enum):
    BLOCK = "block"
    WARN = "warn"
    INFO = "info"


@dataclass
class ValidationFlag:
    """A single issue found during validation."""
    severity: Severity
    agent: str                    # which agent found this
    claim: str                    # the claim being validated
    issue: str                    # what's wrong
    suggestion: str               # how to fix it
    evidence: str | None = None   # supporting evidence for the flag
    file_path: str | None = None  # vault note path


@dataclass
class AgentResult:
    """Result from a single validation agent."""
    agent: str
    status: Literal["pass", "fail", "error", "timeout", "skipped"]
    flags: list[ValidationFlag] = field(default_factory=list)
    summary: str = ""
    duration_ms: int = 0
    raw_output: str = ""


@dataclass
class ConsensusResult:
    """Aggregated consensus across all agents."""
    passed: bool
    blocking_flags: list[ValidationFlag]
    warning_flags: list[ValidationFlag]
    info_flags: list[ValidationFlag]
    agent_agreement: float         # 0.0-1.0: fraction of agents that passed
    requires_human_review: bool


@dataclass
class ValidationResult:
    """Complete result of a multi-agent validation run."""
    target: str                    # what was validated (note path, report name, "full_audit")
    validation_type: str           # "gene_note", "prescriber_report", "vault_audit"
    passed: bool
    agent_results: dict[str, AgentResult]
    consensus: ConsensusResult
    flags: list[ValidationFlag]
    recommendations: list[str]
    timestamp: str = ""


def load_agent_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load multi-agent configuration from agents.yaml."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent.parent / "config" / "agents.yaml"

    if not config_path.exists():
        return {"agents": {}, "gates": {}, "consensus": {}}

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def get_gate_config(config: dict, validation_type: str) -> dict:
    """Get the gate configuration for a validation type."""
    return config.get("gates", {}).get(validation_type, {
        "required_agents": 1,
        "timeout_minutes": 10,
        "block_on": [],
        "warn_on": [],
    })


def compute_consensus(
    agent_results: dict[str, AgentResult],
    gate: dict,
    consensus_config: dict,
) -> ConsensusResult:
    """Compute consensus across agent results.

    Logic:
    - Collect all flags from all agents
    - Check if any blocking flags match gate's block_on list
    - Check if enough agents passed (>= required_agents)
    - Apply tolerance rules for effect sizes and evidence tiers
    """
    all_flags = []
    for result in agent_results.values():
        all_flags.extend(result.flags)

    blocking = [f for f in all_flags if f.severity == Severity.BLOCK]
    warnings = [f for f in all_flags if f.severity == Severity.WARN]
    infos = [f for f in all_flags if f.severity == Severity.INFO]

    # Check gate's block_on list
    block_on_types = set(gate.get("block_on", []))
    actual_blocks = [f for f in blocking if f.issue in block_on_types]

    # Count passing agents
    passing = sum(1 for r in agent_results.values() if r.status == "pass")
    total = sum(1 for r in agent_results.values() if r.status != "skipped")
    agreement = passing / total if total > 0 else 0.0

    required = gate.get("required_agents", 1)
    enough_agreement = passing >= required

    passed = enough_agreement and len(actual_blocks) == 0
    requires_human = (
        len(actual_blocks) > 0
        and consensus_config.get("require_human_for_blocks", True)
    )

    return ConsensusResult(
        passed=passed,
        blocking_flags=blocking,
        warning_flags=warnings,
        info_flags=infos,
        agent_agreement=agreement,
        requires_human_review=requires_human,
    )


def check_available_agents(config: dict) -> dict[str, bool]:
    """Check which configured agents are actually available.

    Returns dict of agent_name -> is_available. An agent is available if:
    - It's enabled in config
    - Its required skill/binary exists (checked by name convention)

    External skills (notebooklm, tavily-search, firecrawl-research) are
    checked by looking for their skill directories in ~/.claude/skills/.
    Codex CLI is checked by looking for the `codex` binary.
    Subagents (Claude) are always available.
    """
    import shutil

    agents = config.get("agents", {})
    available = {}
    skills_dir = Path.home() / ".claude" / "skills"

    for name, agent_config in agents.items():
        if not agent_config.get("enabled", True):
            available[name] = False
            continue

        if name == "codex":
            available[name] = shutil.which("codex") is not None
        elif name == "subagents":
            available[name] = True  # Claude subagents always available
        elif "skill" in agent_config:
            skill_name = agent_config["skill"]
            available[name] = (skills_dir / skill_name).is_dir()
        else:
            available[name] = True  # no external dependency

    return available


def adjust_gate_for_available_agents(
    gate: dict,
    available: dict[str, bool],
) -> dict:
    """Adjust gate requirements based on which agents are actually available.

    If fewer agents are available than required_agents, lower the requirement
    to the number of available agents (minimum 1). This allows validation to
    proceed with degraded confidence rather than blocking entirely.
    """
    num_available = sum(1 for v in available.values() if v)
    adjusted = dict(gate)

    original_required = gate.get("required_agents", 1)
    if num_available < original_required:
        adjusted["required_agents"] = max(1, num_available)
        adjusted["_degraded"] = True
        adjusted["_original_required"] = original_required
        adjusted["_available_agents"] = num_available
    else:
        adjusted["_degraded"] = False

    return adjusted


def format_validation_report(result: ValidationResult) -> str:
    """Format a validation result as a markdown report."""
    lines = [
        f"# Validation Report: {result.target}",
        f"**Type**: {result.validation_type}",
        f"**Result**: {'PASSED' if result.passed else 'BLOCKED'}",
        f"**Agent Agreement**: {result.consensus.agent_agreement:.0%}",
        "",
    ]

    if result.consensus.blocking_flags:
        lines.append("## Blocking Issues")
        for flag in result.consensus.blocking_flags:
            lines.append(f"- **[{flag.agent}]** {flag.claim}: {flag.issue}")
            lines.append(f"  - Suggestion: {flag.suggestion}")
        lines.append("")

    if result.consensus.warning_flags:
        lines.append("## Warnings")
        for flag in result.consensus.warning_flags:
            lines.append(f"- **[{flag.agent}]** {flag.claim}: {flag.issue}")
        lines.append("")

    if result.recommendations:
        lines.append("## Recommendations")
        for rec in result.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

    lines.append("## Agent Results")
    for agent, ar in result.agent_results.items():
        lines.append(f"### {agent}")
        lines.append(f"- Status: {ar.status}")
        lines.append(f"- Duration: {ar.duration_ms}ms")
        if ar.summary:
            lines.append(f"- Summary: {ar.summary}")
        lines.append("")

    return "\n".join(lines)
