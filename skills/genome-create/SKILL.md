---
name: genome-create
description: |
  Create gene, system, or phenotype notes from SQLite genotype data and templates.
  Triggers on: /new-gene SYMBOL, /new-system NAME, "add gene X", "create system note",
  "create phenotype note for X".
---

# Genome Create

Create structured vault notes from genotype data, following templates and evidence standards.

## Vault Configuration
- Database: `data/genome.db` (query genotype data FIRST, never guess)
- Templates: `Templates/_Gene.md`, `Templates/_System.md`, `Templates/_Phenotype.md`
- Evidence tiers: `config/evidence_tiers.yaml`

## Workflow: Gene Note

### Step 1: Identify Gene
User specifies gene symbol (e.g., CYP2D6, BDNF, APOE).

### Step 2: Query SQLite
```bash
sqlite3 data/genome.db "SELECT rsid, genotype, source, r2_quality FROM snps WHERE rsid IN (SELECT json_each.value FROM genes, json_each(genes.rsids) WHERE gene_symbol='SYMBOL')"
```
If gene not in genes table, search by chromosome region:
```bash
sqlite3 data/genome.db "SELECT rsid, genotype, r2_quality FROM snps WHERE chromosome='CHR' AND position BETWEEN START AND END AND r2_quality > 0.8"
```

### Step 3: Research Context
- Check existing vault notes for cross-references
- Look up gene in enrichments table
- Note drug interactions (CPIC/DPWG if pharmacogene)

### Step 4: Create Note
Follow template exactly (`Templates/_Gene.md`). Required sections:
1. **What This Gene Does** — biology, function, mechanism
2. **Personal Genotype** — table from SQLite data with evidence tiers
3. **Health Relevance** — by domain subsections
4. **Drug Interactions** — table if applicable
5. **Gene-Gene Interactions** — cross-references to existing vault genes
6. **What Changes This** — modifiable factors (BDNF exit ramp philosophy)
7. **Confidence & Caveats** — evidence tier, limitations, link to [[Genetic Determinism - Limits and Caveats]]
8. **Sources** — real published citations only

### Step 5: Wire Navigation
- Add to relevant System notes' `genes:` frontmatter
- Update MoC (Dataview handles automatically)
- Cross-link to related Phenotype notes

### Step 6: Validate (optional)
If genome-validate is configured, run validation on the new note.

## Rules
- **Query SQLite FIRST** — never guess genotypes
- **Every claim needs an evidence tier** (E1-E5)
- **Gene-gene interactions must reference existing vault genes**
- **Always end with what can change** (the exit ramp)
- **For imputed variants**: always note r2_quality, flag if < 0.8
- **Use experience-based naming** for phenotypes, not deficit language

## Workflow: System Note
Similar but uses `Templates/_System.md`. Aggregates genes by biological system.

## Workflow: Phenotype Note
Uses `Templates/_Phenotype.md`. Bridges genetics to lived experience.

## Output
- New note at `Genes/SYMBOL.md`, `Systems/Name.md`, or `Phenotypes/Name.md`
- Updated cross-references in related notes
- Validation report (if enabled)
