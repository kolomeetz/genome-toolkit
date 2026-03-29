---
type: moc
created_date: '{{date}}'
tags:
  - navigation
  - moc
---

# Map of Content — All Genes

## Risk Variants
```dataview
TABLE gene_symbol AS "Gene", description AS "Function & Status", evidence_tier AS "Evidence"
FROM "Genes"
WHERE personal_status = "risk"
SORT gene_symbol ASC
```

## Intermediate Variants
```dataview
TABLE gene_symbol AS "Gene", description AS "Function & Status", evidence_tier AS "Evidence"
FROM "Genes"
WHERE personal_status = "intermediate"
SORT gene_symbol ASC
```

## Optimal / Protective Variants
```dataview
TABLE gene_symbol AS "Gene", description AS "Function & Status", evidence_tier AS "Evidence"
FROM "Genes"
WHERE personal_status = "optimal" OR personal_status = "protective" OR personal_status = "reference"
SORT gene_symbol ASC
```

## Full Gene List
```dataview
TABLE gene_symbol AS "Gene", full_name AS "Full Name", personal_status AS "Status", evidence_tier AS "Evidence", join(systems, ", ") AS "Systems"
FROM "Genes"
WHERE type = "gene"
SORT gene_symbol ASC
```
