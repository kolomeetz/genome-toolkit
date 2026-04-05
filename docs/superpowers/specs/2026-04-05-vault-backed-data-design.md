# Vault-Backed Data: Replace Mock Data with Real API

**Date:** 2026-04-05
**Goal:** Replace ~680 lines of hardcoded mock data across 4 frontend sections with vault-backed API data + config YAML for reference content.

## Architecture

### Backend: `/api/vault/genes` endpoint

Single endpoint reads ALL vault gene notes, parses YAML frontmatter, and returns structured gene data. Frontend hooks filter by domain.

**Response shape:**
```json
{
  "genes": [{
    "symbol": "MTHFR",
    "full_name": "Methylenetetrahydrofolate Reductase",
    "chromosome": "1",
    "systems": ["Methylation Pathway", "Cardiovascular"],
    "personal_variants": [{"rsid": "rs1801133", "genotype": "T/T", "significance": "C677T homozygous"}],
    "evidence_tier": "E2",
    "personal_status": "risk",
    "relevance": "high",
    "description": "...",
    "tags": ["gene", "methylation"],
    "study_count": 89,
    "has_vault_note": true
  }],
  "total": 126
}
```

**Implementation:** Extend existing `/api/mental-health/genes` pattern in `mental_health.py`. Read `Genes/*.md`, parse YAML frontmatter with `yaml.safe_load`, strip Obsidian wikilinks from `systems` field (`[[Dopamine System]]` → `Dopamine System`).

**Study count:** Parse from vault note body (look for "studies" or "sources" mentions) OR use `studyCount` if added to frontmatter. Fallback to count of PubMed-style citations in the note body.

### Backend: `/api/vault/actions/{gene_symbol}` endpoint

Parse the markdown body of a gene note to extract structured actions. Look for sections like `## Recommended Actions`, `## Actions`, bullet lists with action keywords (Consider, Monitor, Discuss, Avoid).

**Response shape:**
```json
{
  "actions": [{
    "type": "consider",
    "title": "Methylfolate supplementation (400-800 mcg/day)",
    "gene_symbol": "MTHFR",
    "evidence_tier": "E2",
    "health_domain": "cardiovascular"
  }]
}
```

### Config YAML: `config/risk-landscape.yaml`

Epidemiological reference data — population mortality stats for demographic groups. This is reference data, not personal genomic data.

```yaml
demographic: { sex: male, age_range: "30-44", ancestry: european }
causes:
  - cause: Cardiovascular Disease
    pct: 31
    relevant_genes: [MTHFR, APOE, LPA]
    relevant_systems: [Methylation Pathway, Lipid Metabolism]
  - cause: Cancer
    pct: 24
    relevant_genes: [BRCA1, BRCA2, CHEK2, APC]
    ...
```

### Config YAML: `config/substances.yaml`

Curated harm reduction content per substance. Maps substances to relevant genes/enzymes.

```yaml
substances:
  - name: Alcohol
    relevant_genes: [ALDH2, ADH1B, GABRA2, GAD1]
    relevant_enzymes: [CYP2E1]
    harm_reduction: "Track your drinks..."
  - name: MDMA / Ecstasy
    relevant_genes: [CYP2D6, DRD2, COMT, SLC6A4]
    ...
```

### Config YAML: `config/pgx-drugs.yaml`

Drug class → enzyme mapping with clinical guidance.

```yaml
enzymes:
  - symbol: CYP2D6
    drug_cards:
      - class: SSRIs
        drugs: [Fluoxetine, Paroxetine, Fluvoxamine]
        impact_by_status:
          poor: { impact: warn, text: "Use alternative SSRI" }
          intermediate: { impact: adjust, text: "Consider dose reduction" }
          normal: { impact: ok, text: "Standard dosing" }
```

### Frontend: Data hooks

**`useVaultGenes()`** — Fetches `/api/vault/genes` once, caches in state. Returns `{ genes, loading }`.

**`useRiskLandscape()`** — Loads `config/risk-landscape.yaml` via `/api/config/risk-landscape` + vault genes. Maps genes to causes, computes personal risk bars from gene status.

**`useAddictionData()`** — Filters vault genes by addiction-related systems + loads substances config. Groups genes by pathway.

**`usePGxData()`** — Filters vault genes by PGx systems + loads drug config. Maps enzyme status to drug impacts.

**`useMentalHealthData()`** — Refactor existing hook to use `useVaultGenes()` instead of MOCK_SECTIONS.

### Frontend: Component changes

All components receive data from hooks instead of hardcoded arrays. Loading states shown while fetching. Empty states for sections with no data.

## Files to create/modify

### New files:
- `backend/app/routes/vault.py` — Vault gene endpoint
- `config/risk-landscape.yaml` — Mortality reference data
- `config/substances.yaml` — Substance harm reduction content
- `config/pgx-drugs.yaml` — Drug-enzyme mappings

### Modified files:
- `backend/app/main.py` — Mount vault router + config endpoint
- `frontend/src/hooks/useVaultGenes.ts` — New shared hook
- `frontend/src/hooks/useMentalHealthData.ts` — Refactor to use vault API
- `frontend/src/hooks/useRiskData.ts` — New hook
- `frontend/src/hooks/useAddictionData.ts` — New hook
- `frontend/src/hooks/usePGxData.ts` — New hook
- `frontend/src/components/risk/RiskLandscape.tsx` — Remove CAUSES mock, use hook
- `frontend/src/components/addiction/AddictionProfile.tsx` — Remove PATHWAYS/SUBSTANCES mock
- `frontend/src/components/pgx/PGxPanel.tsx` — Remove MOCK_PGX
- `frontend/src/components/mental-health/MentalHealthDashboard.tsx` — Use refactored hook

## Migration strategy

1. Build backend endpoint + config files first
2. Create useVaultGenes hook
3. Migrate each section one at a time, verifying each works
4. Remove all mock data arrays last
