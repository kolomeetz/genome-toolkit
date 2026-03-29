---
name: genome-report
description: |
  Generate prescriber-facing reports and import biomarker lab results.
  Triggers on: /biomarker, /wallet-card, "import lab results", "analyze bloodwork",
  "generate prescriber summary", "create wallet card", "update PGx card".
---

# Genome Report

Generate clinical reports and import biomarker data.

## Vault Configuration
- Database: `data/genome.db`
- Templates: `Templates/Biomarker Entry.md`
- Genetic predictions: `skills/genome-report/references/genetic_predictions.md`
- Reports: `Reports/`
- Biomarkers: `Biomarkers/`

## Sub-Workflows

### A: Biomarker Import
Triggered by: `/biomarker`, "import lab results", PDF shared

1. **Read PDF** and extract lab markers (values, units, reference ranges)
2. **Normalize** German lab names if needed (Leukozyten → WBC, GPT → ALT)
3. **Create entry** at `Biomarkers/YYYY-MM-DD Lab Results.md` using template
4. **Compare** each marker against genetic predictions:
   - PNPLA3 G;G → expect elevated ALT
   - HFE het → monitor ferritin/transferrin
   - IL1B G;G → expect elevated CRP
   - SH2B3 C;T → expect lower platelets
5. **Flag clinical thresholds**:
   - CRP > 3 mg/L → SSRI augmentation consideration
   - Ferritin > 300 → phlebotomy discussion
   - ALT > 2x ULN → hepatology referral
6. **Generate missing markers** list (prioritized)
7. **Run trend analysis** if previous biomarkers exist
8. **Update** `Meta/Biomarker Tracking Dashboard.md`

### B: Wallet Card Generation
Triggered by: `/wallet-card`, "create wallet card"

Generate `Reports/Wallet Card.md`:
- Query CYP enzyme status from database
- List: AVOID (hard contraindications), CAUTION (dose adjustments), LIMIT (max doses)
- Include: current medication, carrier status, cannabis interaction note
- Format: printable 1-page reference

### C: Pharmacogenomics Card
Full enzyme status table with drug interaction matrix.

### D: Prescriber Summary
One-page overview for doctors unfamiliar with PGx.

### E: SSRI Response Profile
CRP-guided treatment algorithm, sertraline vs alternatives.

## Validation
All prescriber-facing reports require multi-agent validation gate (2 agents must agree).
Run `/genome-validate` automatically if `config/agents.yaml` has gates configured.

## Output
- Report note in `Reports/` or `Biomarkers/`
- Updated dashboards
- Validation report (for prescriber docs)
