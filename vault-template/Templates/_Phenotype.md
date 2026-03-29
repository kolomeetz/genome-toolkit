---
type: phenotype
trait:
contributing_genes: []
contributing_systems: []
heritability_estimate:
evidence_tier:
framing: understanding
description:
protocols: []
created_date: '{{date}}'
tags:
  - phenotype
---

# {{trait}}

## The Experience

## Genetic Contributors

```dataview
TABLE gene_symbol AS "Gene", personal_variants[0].genotype AS "Genotype", evidence_tier AS "Evidence"
FROM "Genes"
WHERE contains(file.inlinks, this.file.link) OR contains(this.contributing_genes, file.link)
SORT evidence_tier ASC
```

## Non-Genetic Contributors

## The Reframe

## What Helps

## What Doesn't Help

## Caveats

> See [[Genetic Determinism - Limits and Caveats]]
