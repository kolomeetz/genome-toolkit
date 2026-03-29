---
type: dashboard
created_date: '{{date}}'
tags:
  - navigation
  - interventions
---

# Interventions Dashboard

Evidence-ranked actions based on your genetic profile.

## Tier 1: Strong Evidence (E1-E2)
```dataview
TABLE WITHOUT ID
  link(file.link, protocol_name) AS "Intervention",
  evidence_tier AS "Evidence",
  join(target_systems, ", ") AS "Systems Addressed"
FROM "Protocols"
WHERE evidence_tier = "E1-E2" OR evidence_tier = "E2" OR evidence_tier = "E1"
SORT evidence_tier ASC
```

## Tier 2: Good Evidence (E2-E3)
```dataview
TABLE WITHOUT ID
  link(file.link, protocol_name) AS "Intervention",
  evidence_tier AS "Evidence",
  join(target_systems, ", ") AS "Systems Addressed"
FROM "Protocols"
WHERE evidence_tier = "E2-E3"
SORT protocol_name ASC
```

## Tier 3: Supported (E3-E4)
```dataview
TABLE WITHOUT ID
  link(file.link, protocol_name) AS "Intervention",
  evidence_tier AS "Evidence",
  join(target_systems, ", ") AS "Systems Addressed"
FROM "Protocols"
WHERE evidence_tier = "E3" OR evidence_tier = "E3-E4"
SORT evidence_tier ASC
```

## All Protocols
```dataview
TABLE protocol_name AS "Protocol", actionability AS "Tier", evidence_tier AS "Evidence", description AS "Purpose", join(target_systems, ", ") AS "Systems"
FROM "Protocols"
WHERE type = "protocol"
SORT actionability ASC, evidence_tier ASC
```
