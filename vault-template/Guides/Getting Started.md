---
type: guide
created_date: '{{date}}'
tags:
  - guide
  - onboarding
---

# Getting Started with Your Genome Vault

This vault turns your raw genetic data into actionable health insights. Here's how to get started.

## Step 1: Import Your Data

Place your raw genome file in `data/raw/` and run:
```
/genome-import
```

Supported providers: 23andMe (v4/v5), AncestryDNA, MyHeritage, Nebula, any VCF file.

The import script auto-detects your provider, parses the data, runs quality checks, and populates the SQLite database.

**What you'll see**: A QC report showing total SNPs imported, filtered variants, and chromosome distribution.

## Step 2: Set Up Your Vault

Run the onboarding wizard:
```
/genome-onboard
```

This asks about your health goals and creates personalized content:
- **Wallet Card** — emergency drug safety reference (print this!)
- **8-12 Gene notes** — your most relevant genes, scored by your goals
- **System notes** — how your genes interact in biological systems
- **Action items** — tests to request, conversations to have with your doctor

## Step 3: Optional — Expand Your Data with Imputation

Your DTC test covers ~600K SNPs (~1.5% of common variation). Imputation can expand this to ~3-40 million variants using statistical inference.

See [[Imputation Guide]] for the full walkthrough.

After imputation, re-run `/genome-import` with your imputed VCF files.

## Step 4: Explore

### By Concern
> "I'm anxious" / "My liver enzymes are high" / "Is this drug safe?"
> Start at [[Question Index]] — search by concern, not by gene.

### By System
> "How does my stress response work?" / "What about dopamine?"
> Start at [[MoC - All Systems]] — biological systems first.

### By Experience
> "Why do I procrastinate?" / "Why is sleep hard?"
> Start at [[MoC - Phenotypes]] — genetics meets daily life.

## Step 5: Add Lab Results

When you get bloodwork, import it:
```
/biomarker
```

The vault compares your lab values against genetic predictions. This is where genetics meets reality.

## Step 6: Keep It Current

- **New research**: Run `/genome-analytics` to check PubMed for new publications on your genes
- **Vault health**: Run `/genome-audit` periodically to check for staleness and consistency
- **Validation**: Run `/genome-validate` to fact-check claims with multiple AI agents

## Key Concepts

### Evidence Tiers (E1-E5)
Every claim in this vault has an evidence tier. E1 (clinical-grade) is reliable. E5 (speculative) is a hypothesis. See [[Genetic Determinism - Limits and Caveats]].

### The Exit Ramp
Every gene note ends with "What Changes This" — because genetics is not destiny. The vault is designed to show what you can do, not just what your DNA says.

### Single Source of Truth
- **Genotype data** lives in SQLite (`data/genome.db`)
- **Interpretation** lives in markdown (Gene notes, System notes)
- **Aggregation** happens via Dataview queries (dashboards, MoCs)

## Required Obsidian Plugins

- **Dataview** (essential) — powers all dynamic tables and dashboards
- **Templater** (recommended) — template variables for note creation
- **Periodic Notes** (optional) — biomarker tracking cadence

## Need Help?

- `/genome-import` — import or troubleshoot data
- `/genome-onboard` — re-run onboarding with different goals
- `/genome-validate` — fact-check any note
- [[Dashboard]] — your home base
