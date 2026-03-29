---
type: moc
created_date: '{{date}}'
tags:
  - navigation
  - moc
---

# Map of Content — All Systems

## System Overview
```dataview
TABLE system_name AS "System", coverage AS "Coverage", key_finding AS "Key Finding", status AS "Status"
FROM "Systems"
WHERE type = "system"
SORT priority ASC
```

## Genes by System
```dataview
TABLE system_name AS "System", join(genes, ", ") AS "Genes", join(phenotypes, ", ") AS "Phenotypes"
FROM "Systems"
WHERE type = "system"
SORT priority ASC
```
