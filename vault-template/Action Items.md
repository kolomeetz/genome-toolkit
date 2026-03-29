---
type: dashboard
created_date: '{{date}}'
tags:
  - navigation
  - actions
---

# Action Items

## Critical Priority
```dataview
TASK
FROM ""
WHERE !completed AND priority = "critical"
SORT file.name ASC
```

## High Priority
```dataview
TASK
FROM ""
WHERE !completed AND priority = "high"
SORT context ASC
```

## Testing & Monitoring
```dataview
TASK
FROM ""
WHERE !completed AND (context = "testing" OR context = "monitoring")
SORT priority ASC
```

## All Pending
```dataview
TASK
FROM ""
WHERE !completed AND priority
SORT choice(priority = "critical", "0", choice(priority = "high", "1", choice(priority = "medium", "2", "3"))) ASC, context ASC
```

## Recently Completed
```dataview
TASK
FROM ""
WHERE completed AND priority
LIMIT 20
```
