---
type: gene
gene_symbol: CYP2D6
full_name: Cytochrome P450 2D6
chromosome: '22'
systems:
  - Drug Metabolism
  - Pharmacogenomics
personal_variants:
  - rsid: rs3892097
    genotype: del
    significance: "*4 allele — non-functional"
  - rsid: rs1065852
    genotype: A;G
    significance: "*10 allele — reduced function"
evidence_tier: E1
relevance: critical
last_reviewed: '2026-03-25'
brain_vault_link: "[[Pharmacogenomics Card]]"
created_date: '2026-01-15'
tags:
  - gene
  - pgx
  - drug-metabolism
  - cpic
---

# CYP2D6 — Cytochrome P450 2D6

## Personal Genotype

| SNP | Genotype | Significance | Tier |
|-----|----------|-------------|------|
| rs3892097 | del | *4 allele — non-functional | E1 |
| rs1065852 | A;G | *10 allele — reduced function | E1 |

**Predicted phenotype:** Likely *4/*10 — intermediate to poor metabolizer (confirm with clinical sequencing).

## Health Relevance

CYP2D6 metabolizes ~25% of all prescribed drugs. The *4/*10 genotype results in significantly reduced enzyme activity affecting:

- **Sertraline** — current medication. May accumulate at standard doses. (E1, CPIC)
- **Tricyclic antidepressants** — nortriptyline requires dose reduction 25-50%. (E1, CPIC)
- **Codeine** — reduced conversion to morphine, poor analgesic effect. (E1, CPIC)
- **Tamoxifen** — reduced activation, clinical implications if ever needed. (E1, CPIC)

## Drug Interactions

Per CPIC guidelines:
- TCAs: start at 25% lower dose, monitor levels
- SSRIs: sertraline least affected among SSRIs by CYP2D6
- Opioids: avoid codeine, use non-CYP2D6 alternatives

## Gene-Gene Interactions

- [[CYP1A2]] — compensatory metabolism pathway for some substrates
- [[IL1B]] — sertraline accumulation may amplify inflammatory effects

## What Changes This

- CYP2D6 is NOT inducible — genotype determines activity permanently
- Drug-drug interactions can further inhibit remaining activity (e.g., fluoxetine, bupropion)
- Clinical sequencing recommended to confirm *4/*10 vs other configurations

## Action Items

- [ ] Schedule clinical CYP2D6 sequencing to confirm star alleles ^task-cyp2d6-seq [priority:: high] [context:: testing] [due:: 2026-05-15]
- [x] Verified sertraline dose with prescriber given CYP2D6 status [priority:: critical] [context:: prescriber] [due:: 2026-03-20]
