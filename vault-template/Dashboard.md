---
type: dashboard
created_date: '{{date}}'
tags:
  - navigation
  - dashboard
---

# Your Genome Dashboard

> "Normal willpower, different hardware. Fully rewirable."
> Genetics explains WHY you are the way you are, not what's wrong with you.

## What do you need right now?

### For You
- **Something feels off** — search by concern, not by gene -> [[Question Index]]
- **I need a protocol** — evidence-ranked actions -> [[Interventions Dashboard]]
- **Check my progress** — what's done, what's next -> [[#Progress]]

### For Your Doctor
- **Emergency drug info** — print and keep in your wallet -> [[Wallet Card]]
- **Full prescriber brief** — one page for your doctor -> [[Prescriber Summary]]
- **Lab tests to request** — what to measure and why -> [[Complete Testing Guide]]

### Go Deeper
- **By body system** — how your biology works together -> [[MoC - All Systems]]
- **By lived experience** — genetics meets daily life -> [[MoC - Phenotypes]]
- **By gene** — individual gene deep-dives -> [[MoC - All Genes]]

---

## Your Profile

```dataview
TABLE system_name AS "System", coverage AS "Coverage", key_finding AS "Key Finding", status AS "Status"
FROM "Systems"
WHERE type = "system"
SORT priority ASC
```

---

## Evidence & Caveats

> This vault uses a **5-tier evidence system**:
> - **E1** (clinical-grade): Drug metabolism, CPIC guidelines — act on these
> - **E2** (well-replicated): Multiple GWAS, strong evidence — likely reliable
> - **E3** (supported): Some studies, plausible mechanism — interpret cautiously
> - **E4-E5** (suggestive/speculative): Hypotheses, not diagnoses
>
> **Genetics is not destiny.** 40-70% of outcomes are environment, behavior, and choice.
> See [[Genetic Determinism - Limits and Caveats]] for the full picture.

---

## Progress

```dataview
TABLE WITHOUT ID
  "Gene Notes" AS "Category",
  length(rows) AS "Created"
FROM "Genes"
WHERE type = "gene"
GROUP BY true
```

```dataview
TABLE WITHOUT ID
  "Systems Covered" AS "Category",
  length(rows) AS "Created"
FROM "Systems"
WHERE type = "system"
GROUP BY true
```

```dataview
TABLE WITHOUT ID
  "Lab Results" AS "Category",
  length(rows) AS "Entries"
FROM "Biomarkers"
WHERE type = "biomarker"
GROUP BY true
```

---

## Pending Actions

```dataview
TASK
FROM ""
WHERE !completed AND (priority = "critical" OR priority = "high")
SORT choice(priority = "critical", "0", "1") ASC, file.name ASC
```

---

## Recent Activity

```dataview
TABLE file.mtime AS "Updated", type AS "Type"
FROM ""
WHERE type AND file.name != "Dashboard"
SORT file.mtime DESC
LIMIT 10
```

---

## Pipeline Status

- **Database**: `data/genome.db`
- **Last import**: check `pipeline_runs` table
- **Imputation**: see [[Imputation Guide]] for expanding your data
