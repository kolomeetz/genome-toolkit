---
type: guide
created_date: '{{date}}'
tags:
  - guide
  - onboarding
---

# Getting Started with Your Genome Vault

This vault turns your raw genetic data into actionable health insights. Follow the steps below in order. If you want a quick checklist you can tick off as you go, see [[Setup Checklist]].

---

## Step 1: Enable Community Plugins in Obsidian

The vault relies on community plugins for dynamic tables and dashboards. Without them, most pages will look empty.

**What to do:**
1. Open Settings (Cmd/Ctrl + ,)
2. Go to **Community plugins** in the left sidebar
3. Turn off **Restricted mode** (confirm the prompt)
4. Click **Browse**, search for **Dataview**, and install it
5. Enable Dataview in the installed plugins list

**How to verify:** Open [[Dashboard]]. If you see tables with gene data (or empty tables with column headers), Dataview is working. If you see raw code blocks starting with `dataview`, the plugin is not active.

**If something went wrong:**
- Make sure Restricted mode is OFF
- Try restarting Obsidian after installing the plugin
- Check that Dataview appears under Settings > Community plugins > Installed plugins

> [!tip] Optional but recommended
> Also install **Templater** (for note creation templates) and **Periodic Notes** (for biomarker tracking).

---

## Step 2: Import Your Genome Data

Place your raw genome file in `data/raw/` and run:
```
/genome-import
```

Supported providers: 23andMe (v4/v5), AncestryDNA, MyHeritage, Nebula, any VCF file.

The import script auto-detects your provider, parses the data, runs quality checks, and populates the SQLite database.

**How to verify:** The import prints a QC report showing total SNPs imported, filtered variants, and chromosome distribution. You should see 500K+ SNPs for a typical DTC test. You can also check that `data/genome.db` exists and is not empty.

**If something went wrong:**
- **"File not found"** — make sure your raw file is inside `data/raw/`
- **"Unknown format"** — check [[Supported Providers]] or try renaming the file to `.txt` or `.vcf`
- **Low SNP count (<100K)** — you may have an older chip version; this is fine, but consider imputation (Step 4)
- Run `/genome-import` again to see the troubleshooting menu

---

## Step 3: Run Onboarding

Once your data is imported, run the onboarding wizard:
```
/genome-onboard
```

This asks about your health goals and creates personalized content:
- **Wallet Card** — emergency drug safety reference (print this!)
- **8-12 Gene notes** — your most relevant genes, scored by your goals
- **System notes** — how your genes interact in biological systems
- **Action items** — tests to request, conversations to have with your doctor

There are two modes:
- **Quick mode** (default, ~2 min): 4 questions, fast vault bootstrap
- **Full mode** (~12 min): `/genome-onboard --full` — 22-question interview with validated psychological instruments, generates a Profile Card and Action Plan

**How to verify:** After onboarding, check:
1. [[Dashboard]] shows your selected goals and has populated links
2. `Reports/Wallet Card.md` exists
3. Several gene notes appear in the Genes/ folder
4. [[Action Items]] has entries

**If something went wrong:**
- **"No genotype data found"** — you skipped Step 2. Run `/genome-import` first.
- **Empty dashboard** — make sure Dataview is enabled (Step 1)
- **Want to change goals** — run `/genome-onboard` again; it will regenerate content based on new answers

---

## Step 4: Expand Your Data with Imputation (Optional)

Your DTC test covers ~600K SNPs (~1.5% of common variation). Imputation can expand this to ~3-40 million variants using statistical inference.

**What to do:**
1. Read [[Imputation Guide]] for the full walkthrough
2. Prepare your data: the guide walks you through export and server upload
3. After imputation completes (2-12 hours), re-run `/genome-import` with your imputed VCF files

**How to verify:** After importing imputed data, the QC report will show millions of SNPs instead of hundreds of thousands. Gene notes will have more complete data.

**If something went wrong:**
- See the troubleshooting section in [[Imputation Guide]]
- Common issues: assembly mismatch (GRCh37 vs GRCh38), chromosome naming, 5-sample minimum on Michigan server

---

## Step 5: Explore Your Vault

Now that your vault is set up, here are three ways in:

### By Concern
> "I'm anxious" / "My liver enzymes are high" / "Is this drug safe?"

Start at [[Question Index]] — search by concern, not by gene.

### By System
> "How does my stress response work?" / "What about dopamine?"

Start at [[MoC - All Systems]] — biological systems first.

### By Experience
> "Why do I procrastinate?" / "Why is sleep hard?"

Start at [[MoC - Phenotypes]] — genetics meets daily life.

---

## Step 6: Add Lab Results

When you get bloodwork, import it:
```
/biomarker
```

The vault compares your lab values against genetic predictions. This is where genetics meets reality.

**How to verify:** After import, biomarker notes appear in the Biomarkers/ folder with genetic context annotations.

---

## Step 7: Keep It Current

| Task | Command | When |
|------|---------|------|
| Check for new research | `/genome-analytics` | Monthly |
| Audit vault health | `/genome-audit` | Monthly |
| Fact-check claims | `/genome-validate` | After major updates |
| Re-run assessments | `/genome-assess` | Every 30 days |

---

## Key Concepts

### Evidence Tiers (E1-E5)
Every claim in this vault has an evidence tier. E1 (clinical-grade) is reliable. E5 (speculative) is a hypothesis. See [[Genetic Determinism - Limits and Caveats]].

### The Exit Ramp
Every gene note ends with "What Changes This" — because genetics is not destiny. The vault is designed to show what you can do, not just what your DNA says.

### Single Source of Truth
- **Genotype data** lives in SQLite (`data/genome.db`)
- **Interpretation** lives in markdown (Gene notes, System notes)
- **Aggregation** happens via Dataview queries (dashboards, MoCs)

---

## Need Help?

| Command | What it does |
|---------|-------------|
| `/genome-import` | Import or troubleshoot data |
| `/genome-onboard` | Re-run onboarding with different goals |
| `/genome-validate` | Fact-check any note |
| `/genome-audit` | Check vault health and staleness |

Your home base is [[Dashboard]].
