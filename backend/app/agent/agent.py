"""Agent session management using Claude Agent SDK.

Each user chat session gets a ClaudeSDKClient that maintains conversation
context. Custom genome tools are provided via an in-process MCP server.
"""
import asyncio
from typing import AsyncIterator

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)

from backend.app.agent.tools import create_genome_mcp_server

SYSTEM_PROMPT = """You are a genome data assistant for a personal genomics toolkit. You help users understand their genetic variants (SNPs), explain clinical significance, and navigate their data.

You have access to the user's genetic data through the genome MCP tools. Use them to query variants and update the UI table.

Guidelines:
- Be concise and scientifically accurate
- When discussing variants, mention the rsID, genotype, and what it means clinically
- Use update_table_view to filter the UI table when showing specific variants
- Explain significance in plain language
- Note when data is imputed (lower confidence) vs genotyped (directly measured)
- Format responses with clean markdown. Use ## for headings, **bold** for emphasis, bullet lists for actions. Do NOT use unicode dashes (———), decorative lines, or ASCII art separators. Keep formatting simple and readable.
- ALWAYS call suggest_responses at the end of every response with 2-4 short follow-up options
- When there are concrete next steps (e.g. adding a supplement, checking a gene, reviewing a variant), call suggest_actions with 1-4 typed actions. Use add_to_checklist for recommendations, show_gene/show_variant for navigation, open_link for external resources (ClinVar, PubMed). Actions appear as clickable buttons the user can execute instantly.
- When using update_table_view, set clear_restrictive_filters=true so ACTIONABLE filter doesn't hide results

CRITICAL — Vault integration:
- ALWAYS use read_gene_note when the user asks about a specific gene. The vault contains personalized, curated notes with drug interactions, gene-gene interactions, actionable recommendations, and evidence tiers that are FAR richer than ClinVar data.
- When discussing a gene, read its vault note FIRST, then supplement with database queries.
- Use read_vault_note to access Systems (e.g. Drug Metabolism, Dopamine System), Phenotypes (e.g. Reward Deficiency Syndrome), and Protocols (e.g. Craving Management).
- Use list_vault_notes to discover available notes when the user asks broad questions.
- Cite the evidence tier from the vault note (E1=gold standard, E2=strong, E3=moderate).
- Include actionable recommendations from the vault — these are personalized for this user.

Voice mode:
- When the user's message starts with [VOICE], call voice_summary at the end with a short spoken version.
- Your full text response still goes to screen. The voice_summary goes to the speaker.
- Both in the same turn — no extra request needed."""

def build_system_prompt(page_context: str | None = None) -> str:
    """Build system prompt, optionally injecting page context."""
    if not page_context:
        return SYSTEM_PROMPT
    return (
        SYSTEM_PROMPT
        + "\n\n## User's Current Page Context\n"
        + page_context
        + "\n\nUse this context to give relevant answers. The user can see this data on their screen right now."
    )


# MCP server config — created once, shared across sessions
_genome_mcp = None


def get_genome_mcp():
    global _genome_mcp
    if _genome_mcp is None:
        _genome_mcp = create_genome_mcp_server()
    return _genome_mcp


async def create_agent_session(
    cwd: str | None = None,
    page_context: str | None = None,
) -> tuple[ClaudeSDKClient, str | None]:
    """Create a new Agent SDK client with genome tools.

    Returns (client, session_id).
    """
    from pathlib import Path

    mcp = get_genome_mcp()
    resolved_cwd = cwd or str(Path(__file__).resolve().parents[3])

    options = ClaudeAgentOptions(
        system_prompt=build_system_prompt(page_context),
        mcp_servers={"genome": mcp},
        allowed_tools=[
            "mcp__genome__query_snps",
            "mcp__genome__get_snp_detail",
            "mcp__genome__get_genome_stats",
            "mcp__genome__update_table_view",
            "mcp__genome__suggest_responses",
            "mcp__genome__suggest_actions",
            "mcp__genome__voice_summary",
            "mcp__genome__read_gene_note",
            "mcp__genome__read_vault_note",
            "mcp__genome__list_vault_notes",
        ],
        permission_mode="bypassPermissions",
        max_turns=10,
        cwd=resolved_cwd,
    )

    client = ClaudeSDKClient(options=options)
    return client, None


async def stream_agent_response(
    client: ClaudeSDKClient,
    message: str,
) -> AsyncIterator[dict]:
    """Send a message to the agent and yield SSE-compatible events.

    Yields dicts with 'event' and 'data' keys.
    """
    await client.query(message)

    emitted_text_len = 0  # Track how much text we've already sent

    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    text = block.text
                    # Only emit new text (Agent SDK may re-send earlier text in multi-turn)
                    if len(text) > emitted_text_len:
                        new_text = text[emitted_text_len:]
                        emitted_text_len = len(text)
                        yield {
                            "event": "text_delta",
                            "data": {"content": new_text},
                        }
                elif isinstance(block, ToolUseBlock):
                    yield {
                        "event": "tool_call",
                        "data": {"tool": block.name, "args": block.input},
                    }
                    # Detect UI action tools
                    if block.name == "mcp__genome__update_table_view":
                        yield {
                            "event": "ui_action",
                            "data": {"action": "filter_table", "params": block.input},
                        }
                    elif block.name == "mcp__genome__voice_summary":
                        yield {
                            "event": "ui_action",
                            "data": {
                                "action": "speak",
                                "params": {
                                    "text": block.input.get("text", ""),
                                    "emotion": block.input.get("emotion", ""),
                                },
                            },
                        }
                    elif block.name == "mcp__genome__suggest_responses":
                        suggestions = block.input.get("suggestions", "[]")
                        if isinstance(suggestions, str):
                            import json as _json
                            try:
                                suggestions = _json.loads(suggestions)
                            except Exception:
                                suggestions = [suggestions]
                        yield {
                            "event": "ui_action",
                            "data": {"action": "suggest_responses", "params": {"suggestions": suggestions}},
                        }
                    elif block.name == "mcp__genome__suggest_actions":
                        actions = block.input.get("actions", "[]")
                        if isinstance(actions, str):
                            import json as _json
                            try:
                                actions = _json.loads(actions)
                            except Exception:
                                actions = []
                        yield {
                            "event": "ui_action",
                            "data": {"action": "suggest_actions", "params": {"actions": actions}},
                        }

        elif isinstance(msg, ResultMessage):
            yield {
                "event": "result",
                "data": {
                    "cost_usd": msg.total_cost_usd,
                    "turns": msg.num_turns,
                    "session_id": msg.session_id,
                },
            }

        elif isinstance(msg, SystemMessage) and msg.subtype == "init":
            agent_sid = msg.data.get("session_id") if isinstance(msg.data, dict) else None
            yield {
                "event": "session_init",
                "data": {"agent_session_id": agent_sid},
            }

    yield {"event": "done", "data": {}}
