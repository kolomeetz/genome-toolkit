---
name: genome-onboard
description: |
  Goal-driven onboarding for new genome vault users. Triggers on: /genome-onboard,
  "set up my vault", "I just imported my data", "help me get started with my genome".
  Asks about health goals, maps to systems/genes, generates first actionable outputs.
---

# Genome Onboard

Set up a personalized genome vault based on health goals and imported genotype data.

## Prerequisites
- Genome data already imported via `genome-import` (SQLite database populated)
- Obsidian vault initialized from `vault-template/`

## Vault Configuration
- Config: `$GENOME_VAULT_ROOT` or config/default.yaml
- Database: `data/genome.db`
- Goal map: `config/goal_map.yaml`
- Templates: `Templates/`

## Workflow

### Step 1: Health Goal Questionnaire
Ask the user 4 questions using AskUserQuestion:

1. **What matters most?** (multi-select from goal_map.yaml):
   - Medication safety
   - Mental health (anxiety/mood)
   - Addiction recovery
   - Liver health
   - Gut health / autoimmune
   - Sleep optimization
   - Cardiovascular / metabolic
   - Comprehensive (everything)

2. **Current medications/substances** (free text):
   - Prescription drugs (SSRIs, statins, etc.)
   - OTC drugs (NSAIDs, PPIs)
   - Supplements
   - Cannabis, alcohol, caffeine

3. **Active diagnoses or symptoms** (free text):
   - GAD, IBS, insomnia, joint pain, etc.

4. **Do you have recent lab results?** (yes/no):
   - If yes, suggest running `/biomarker` after onboarding

### Step 2: Map Goals to Targets
Load `config/goal_map.yaml` and resolve:
- `target_systems` — biological systems to document
- `seed_genes` — genes to create notes for
- `first_reports` — reports to generate
- `first_tests` — decision-changing tests to recommend
- `first_protocols` — protocols to create

### Step 3: Score and Prioritize Genes
Query SQLite for available genotype data on seed genes:
```bash
sqlite3 data/genome.db "SELECT rsid, genotype, source, r2_quality FROM snps WHERE rsid IN (SELECT rsid FROM genes WHERE gene_symbol='CYP2D6')"
```

Score each gene using weights from `config/goal_map.yaml`:
```
score = 8*medication_match + 6*goal_match + 5*severe_finding + 4*protocol_exists + 3*biomarker_link + 2*evidence_weight
```

Cap at 8-12 genes for initial generation. Always include safety-critical PGx genes if medication_safety is selected.

### Step 4: Generate First Outputs

**Always generate:**
1. **Wallet Card** (`Reports/Wallet Card.md`) — emergency drug safety reference
2. **Top Tests** section in Action Items — decision-changing labs based on goals

**Goal-dependent:**
3. **8-12 Gene notes** — use `/new-gene` workflow for each, prioritized by score
4. **2-4 System notes** — use Templates/_System.md
5. **2-3 Protocol notes** — use Templates/ or create from goal_map

### Step 5: Populate Dashboard
Update `Dashboard.md` with:
- User's selected goals
- Profile name and import stats
- Goal-specific quick access links
- Progress tracking (X/Y genes created)

### Step 6: Wire Navigation
- Update `MoC - All Genes.md` (Dataview auto-populates)
- Update `MoC - All Systems.md` (Dataview auto-populates)
- Create relevant entries in `Action Items.md`
- Link first reports from Dashboard

### Step 7: Suggest Next Steps
Based on genotype findings, suggest:
- Specific lab tests (with reasoning)
- Follow-up gene notes to create
- Whether imputation would unlock more data
- Prescriber conversation topics

## Output
- Populated vault with 8-12 gene notes, 2-4 system notes, Wallet Card
- Dashboard.md personalized to user goals
- Action Items with prioritized tests and prescriber topics
- Getting Started guide with user's specific next steps
