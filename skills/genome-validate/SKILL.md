---
name: genome-validate
description: |
  Multi-agent validation pipeline for fact-checking claims, verifying evidence tiers,
  and ensuring prescriber document accuracy. Uses Codex CLI, NotebookLM, PubMed
  subagents, and Tavily search.
  Triggers on: /genome-validate, "validate this note", "fact-check", "cross-check claims",
  "verify evidence", "audit this report".
---

# Genome Validate

Multi-agent validation for genome vault claims and reports.

## Vault Configuration
- Agent config: `config/agents.yaml`
- Validation logic: `scripts/lib/multi_agent.py`
- Evidence tiers: `config/evidence_tiers.yaml`

## Validation Modes

### Mode 1: Single Note Validation
Validate a specific gene note or research finding.

1. Read the note content
2. Dispatch to configured agents in parallel:
   - **Codex CLI**: Review evidence tiers, effect sizes, drug interactions
   - **Claude subagent (PubMed)**: Search for recent publications on this gene
   - **Tavily**: Check for retractions of cited papers
3. Aggregate results using consensus logic
4. Report: pass/warn/block with specific flags

**Gate**: `gene_note` — requires 1 agent pass, blocks on effect_size_mismatch, wrong_evidence_tier

### Mode 2: Report Validation (Gated)
Validate prescriber-facing documents (Wallet Card, PGx Card, Prescriber Summary).

1. Read the report content
2. Dispatch to agents:
   - **Codex CLI**: Check drug contraindications against CPIC guidelines
   - **NotebookLM**: Verify claims against uploaded source papers
   - **Claude subagent**: Cross-reference drug interactions
3. Apply strict consensus gate
4. **BLOCK publication** if safety-critical errors found

**Gate**: `prescriber_report` — requires 2 agents agree, zero tolerance on drug safety

### Mode 3: Full Vault Audit
Comprehensive multi-agent audit of the entire vault.

1. Run Python audit scripts (graph, consistency, staleness, evidence, claims)
2. Dispatch to agents:
   - **Codex CLI**: Review top 10 highest-PageRank notes
   - **NotebookLM**: Check prescriber docs vs research notes for contradictions
   - **Tavily**: Scan for retractions and safety alerts
   - **Claude subagent**: PubMed scan for new publications
3. Generate unified audit report

**Gate**: `vault_audit` — advisory only, no blocking

## Agent Integration

### Codex CLI
```bash
echo "PROMPT" | codex exec --skip-git-repo-check -m gpt-5-codex --config model_reasoning_effort="high" --sandbox read-only --full-auto -C $GENOME_VAULT_ROOT 2>/dev/null
```

### NotebookLM
Use the `notebooklm` skill to upload source papers and query.
Requires manual source upload for new validations.

### PubMed Subagent
Launch Claude Explore agent with PubMed search focus.

### Tavily
Use the `tavily-search` skill for web-based verification.

## Consensus Logic

From `config/agents.yaml`:
- `effect_size_tolerance`: 20% — flag if agents disagree by more
- `evidence_tier_tolerance`: 1 tier — flag if agents disagree by more
- `drug_interaction_strict`: true — zero tolerance on safety claims
- `require_human_for_blocks`: true — human must override blocks

## Output
- Validation report (markdown) with per-agent results
- Pass/warn/block status
- Specific flags with suggestions for correction
- Recommendations for follow-up
