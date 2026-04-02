---
name: genome-log
description: |
  Fast daily health logging: supplements, medications, symptoms, interventions, metrics.
  Triggers on: /genome-log, /log, "log supplements", "daily check-in", "track today",
  "how am I doing today", "log symptoms".
---

# Genome Daily Logger

Quick daily health tracking with genetic context. Creates/updates daily notes in the vault.

## Usage

```bash
# Full interactive (supplements + symptoms + interventions + metrics)
python3 $GENOME_TOOLKIT/scripts/daily_log.py --vault $GENOME_VAULT_ROOT

# Quick mode (supplements + medications only, ~15 sec)
python3 $GENOME_TOOLKIT/scripts/daily_log.py --vault $GENOME_VAULT_ROOT --quick

# Show today's log
python3 $GENOME_TOOLKIT/scripts/daily_log.py --vault $GENOME_VAULT_ROOT --show

# Log for specific date
python3 $GENOME_TOOLKIT/scripts/daily_log.py --vault $GENOME_VAULT_ROOT --date 2026-04-01
```

Or from the vault directory:
```bash
cd ~/Brains/genome && python3 data/scripts/daily_log.py
```

## What It Tracks

Four categories, all in YAML frontmatter of `Daily/YYYY-MM-DD.md`:

| Category | Format | Example |
|----------|--------|---------|
| **Medications** | boolean | `sertraline_50mg: true` |
| **Supplements** | boolean | `P5P: true`, `alflorex: true` |
| **Symptoms** | 0-10 scale | `anxiety: 6`, `nasal_congestion: 5` |
| **Interventions** | boolean | `exercise: true`, `morning_walk: true` |
| **Metrics** | numeric | `bristol_scale: 5`, `caffeine_mg: 120` |

## Template

Uses `Templates/_Daily.md` in the vault. Pre-fills all supplements as `true` (optimistic default — untoggle what you missed).

## Definitions

All trackable items with gene context defined in `Protocols/Tracking Registry.md`.

## Dataview Queries

Adherence, streaks, and symptom trends in `Meta/Supplement Adherence.md`.

## Adding New Items

1. Add to `Protocols/Tracking Registry.md` (ID, name, dose, gene basis)
2. Add to `Templates/_Daily.md` in the right category
3. Existing daily notes don't need updating — missing fields = null

## Genetic Context in Logging

When running via Claude Code skill (not standalone CLI), the logger can provide genetic context for each symptom:

- Anxiety 6+ → "FKBP5 C;T: cortisol may be elevated. Exercise or breathing helps."
- GI 7+ → "ATG16L1 G;G + ABP1 3x het: consider histamine trigger. What did you eat?"
- Nasal 5+ → "ABP1 DAO deficit: nasal + GI together = histamine pattern"
- Sleep quality <5 → "CYP1A2 slow: any caffeine after 10:00? Melatonin 0.3mg max."
