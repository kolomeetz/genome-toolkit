---
name: genome-analytics
description: |
  Run analysis scripts: PRS, enrichment, vault audit, PubMed monitoring, consistency checks.
  Triggers on: /genome-analytics, "run PRS", "audit vault", "check PubMed",
  "run enrichment", "check consistency", "analyze pathway".
---

# Genome Analytics

Run analysis and quality assurance scripts on the genome vault.

## Vault Configuration
- Database: `data/genome.db`
- Scripts: `scripts/analytics/`
- Output: `data/output/`

## Available Analyses

### Risk Scores
```bash
python3 scripts/analytics/prs_calculator.py --details
```
Calculates Polygenic Risk Scores for: GAD/Anxiety, Depression, BMI, CAD, T2D, Ankylosing Spondylitis.
Uses `scripts/data/prs_snp_weights.json` for effect sizes.

### Enrichment
```bash
python3 scripts/analytics/snp_enrich.py --rsid rs4680
python3 scripts/analytics/snp_enrich.py --gene CYP2D6
```
Queries SNPedia, ClinVar, MyVariant, gnomAD. Respects rate limits from config.

### Vault Quality Audit
```bash
python3 scripts/analytics/gap_audit.py
python3 scripts/analytics/consistency_checker.py
python3 scripts/analytics/vault_graph_analysis.py
python3 scripts/analytics/evidence_tier_analyzer.py
python3 scripts/analytics/claim_density.py
python3 scripts/analytics/intervention_matrix.py
```
Checks: schema compliance, link integrity, evidence quality, staleness, claim density.

### Literature Monitoring
```bash
python3 scripts/analytics/pubmed_monitor.py --months 6
```
Scans PubMed for new publications on genes in the vault.

### Biomarker Analysis
```bash
python3 scripts/analytics/biomarker_analyzer.py
```
Trend analysis across lab results, comparison against genetic predictions.

### Specialized
- `ld_analysis.py` — Linkage disequilibrium between vault variants
- `pathway_enrichment.py` — KEGG/Reactome pathway analysis
- `effect_size_aggregator.py` — Audit effect sizes vs published data
- `prediction_tracker.py` — Track genetic prediction accuracy

## Workflow
1. Ask user what analysis they need (or detect from context)
2. Check prerequisites (database populated, relevant notes exist)
3. Run appropriate script(s)
4. Summarize results
5. Suggest follow-up actions (create notes, update reports, research)

## Output
- Analysis results (console + text/markdown reports in `data/output/`)
- Recommendations for vault updates
- Flags for human review
