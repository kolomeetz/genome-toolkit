---
type: system
system_name:
coverage:
genes: []
phenotypes: []
protocols: []
key_finding:
status:
priority:
created_date: '{{date}}'
tags:
  - system
---

# {{system_name}}

## System Overview

## Personal Profile

```dataview
TABLE gene_symbol AS "Gene", personal_variants[0].genotype AS "Genotype", evidence_tier AS "Evidence", description AS "Effect"
FROM "Genes"
WHERE contains(systems, this.file.link)
SORT evidence_tier ASC
```

## Compound Effect

## What This Feels Like

## Interventions

## Coverage Gaps

## Open Questions

## Related Notes
```dataview
LIST FROM outgoing([[]])
WHERE file.name != this.file.name
SORT file.mtime DESC
LIMIT 10
```
