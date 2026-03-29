---
type: moc
created_date: '{{date}}'
tags:
  - navigation
  - moc
---

# Map of Content — Phenotypes

Phenotypes bridge genetics to lived experience. Start here if you want to understand **why you experience things the way you do**.

```dataview
TABLE trait AS "Phenotype", description AS "Experience", evidence_tier AS "Evidence", join(contributing_systems, ", ") AS "Systems"
FROM "Phenotypes"
WHERE type = "phenotype"
SORT evidence_tier ASC
```
