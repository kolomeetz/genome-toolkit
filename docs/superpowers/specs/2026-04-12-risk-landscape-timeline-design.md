# Risk Landscape: Honest Risk Communication + Action Timeline

**Issue:** #27
**Date:** 2026-04-12
**Status:** Approved

## Overview

Two enhancements to the Risk Landscape view:
1. **Honest risk communication** — disclaimer clarifying qualitative nature + per-cause confidence dots
2. **Action timeline** — screenings from config + gene actions from vault, grouped by frequency

## 1. Honest Risk Communication

### Disclaimer (InfoCallout update)

Replace current InfoCallout text with:

> Population bars show how common each cause of death is for **{demographic}**. Your personal bar reflects the number and severity of relevant genetic variants found — **it is a qualitative assessment, not a calibrated risk score or PRS**. Having variants does not predict outcomes — it shows where awareness and prevention can make a difference.

### Confidence Dots

Each MortalityRow displays 1-3 dots next to the status text indicating assessment confidence.

**Scoring algorithm:**
- Count matched genes (`n`) and compute average evidence tier numeric value (E1=1, E2=2, ..., E5=5)
- 3 filled dots: `n >= 3 && avgTier <= 2`
- 2 filled dots: `n >= 2 || avgTier <= 3`
- 1 filled dot: `n >= 1`
- 0 filled dots: no matched genes

**Visual spec:**
- 3 circles, 6px diameter, 3px gap
- Filled: `var(--sig-benefit)` (green)
- Unfilled: `var(--border-strong)` (dark gray)
- Hover tooltip: "{n} genes analyzed, avg evidence {tier}"
- Placed inline after statusText, before expand chevron

## 2. Action Timeline

### Config Schema

Each cause in `config/risk-landscape.yaml` gains a `screenings` array:

```yaml
- cause: Cardiovascular Disease
  pct: 31
  relevant_genes: [MTHFR, APOE, LPA]
  screenings:
    - name: Blood pressure check
      frequency: quarterly
      type: monitor
    - name: Lipid panel (total, LDL, HDL, triglycerides)
      frequency: annually
      type: monitor
    - name: ApoB / Lp(a) test
      frequency: once
      type: discuss
      gene: APOE
```

**Fields:**
- `name` (string, required): screening/action description
- `frequency` (enum, required): `quarterly | biannual | annually | once`
- `type` (enum, required): `consider | monitor | discuss`
- `gene` (string, optional): links screening to a specific gene

### Frequency Groups

4 groups displayed in order, each with a distinct color:
1. **QUARTERLY** — `var(--sig-risk)` (amber)
2. **BIANNUAL** — `var(--sig-monitor)` (gold)
3. **ANNUALLY** — `var(--sig-benefit)` (green)
4. **ONCE / AS NEEDED** — `var(--primary)` (indigo)

Empty groups are hidden.

### Data Merge

The `useRiskData` hook merges two sources per cause:

1. **Config screenings** — from `risk-landscape.yaml`, already have `frequency` field
2. **Vault gene actions** — from `/api/vault/genes/{symbol}/actions` for actionable genes

Vault actions are classified by frequency using keyword matching:
- "quarterly", "every 3 months", "3-monthly" → `quarterly`
- "biannual", "every 6 months", "twice a year" → `biannual`
- "annual", "yearly", "every year" → `annually`
- Everything else → `once`

### Timeline UI (in ExpandedDetail)

Replaces the current flat action card list. Appears after gene cards.

Each frequency group:
- Colored left border (3px) matching the frequency color
- Group header: frequency label in uppercase, matching color, 11px, 0.1em letter-spacing
- Items inside group:
  - Name (13px)
  - Source line (11px, secondary color): "General screening" or "{gene_symbol} — Gene-specific"
  - Checklist add button (reuses existing ActionMiniCard + button pattern)

### Types

```typescript
type TimelineFrequency = 'quarterly' | 'biannual' | 'annually' | 'once'

interface TimelineItem {
  name: string
  type: 'consider' | 'monitor' | 'discuss'
  frequency: TimelineFrequency
  gene?: string        // gene symbol if gene-specific
  source: 'screening' | 'vault'
}

interface TimelineGroup {
  frequency: TimelineFrequency
  label: string
  color: string
  items: TimelineItem[]
}
```

`MortalityCause` gains:
```typescript
interface MortalityCause {
  // ... existing fields ...
  timeline?: TimelineGroup[]
  confidence: { filled: number; total: 3; tooltip: string }
}
```

## 3. Files to Change

| File | Change |
|---|---|
| `config/risk-landscape.yaml` | Add `screenings` array to each cause |
| `frontend/src/hooks/useRiskData.ts` | Add `TimelineGroup` types, merge config screenings + vault actions, compute confidence score |
| `frontend/src/components/risk/RiskLandscape.tsx` | New `ConfidenceDots` component, new `TimelineSection` component in `ExpandedDetail`, updated `InfoCallout` text |

## 4. Out of Scope

- Demographic input controls (done in previous session)
- Custom priority pinning (separate iteration)
- Lab/lifestyle data integration (future)
- PRS calculation (requires external data pipeline)
