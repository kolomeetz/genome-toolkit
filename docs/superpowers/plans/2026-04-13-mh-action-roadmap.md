# MH Action Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a collapsible, prioritized action list at the top of the Mental Health dashboard that answers "what should I do first?"

**Architecture:** New `ActionRoadmap` component aggregates all actions from existing props, scores each by gene status + evidence + action type, and renders a ranked top-5 list with expand. No new API calls — purely frontend data transformation.

**Tech Stack:** React 19, TypeScript, Vitest, @testing-library/react

---

## File Structure

| File | Responsibility |
|---|---|
| `frontend/src/components/mental-health/ActionRoadmap.tsx` | **New** — scoring logic + ranked list UI |
| `frontend/src/components/mental-health/MentalHealthDashboard.tsx` | Wire ActionRoadmap between FilterBar and Legend |
| `frontend/src/__tests__/ActionRoadmap.test.tsx` | **New** — tests for scoring, rendering, collapse, filters |

---

### Task 1: Create ActionRoadmap component with tests

**Files:**
- Create: `frontend/src/__tests__/ActionRoadmap.test.tsx`
- Create: `frontend/src/components/mental-health/ActionRoadmap.tsx`

- [ ] **Step 1: Write failing tests**

Create `frontend/src/__tests__/ActionRoadmap.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ActionRoadmap } from '../components/mental-health/ActionRoadmap'
import type { ActionData, GeneData, PathwaySection } from '../types/genomics'

const mockGenes: GeneData[] = [
  {
    symbol: 'MTHFR', variant: 'C677T', rsid: 'rs1801133', genotype: 'T/T',
    status: 'actionable', evidenceTier: 'E1', studyCount: 50,
    description: 'Reduced folate conversion.', actionCount: 2,
    categories: ['mood'], pathway: 'Methylation Pathway',
  },
  {
    symbol: 'SLC6A4', variant: '5-HTTLPR', rsid: 'rs25531', genotype: 'S/L',
    status: 'monitor', evidenceTier: 'E2', studyCount: 30,
    description: 'Serotonin transporter.', actionCount: 1,
    categories: ['mood'], pathway: 'Serotonin & Neuroplasticity',
  },
  {
    symbol: 'BDNF', variant: 'Val66Met', rsid: 'rs6265', genotype: 'G/G',
    status: 'optimal', evidenceTier: 'E2', studyCount: 20,
    description: 'Normal BDNF function.', actionCount: 1,
    categories: ['mood'], pathway: 'Serotonin & Neuroplasticity',
  },
]

const mockSections: PathwaySection[] = [
  {
    narrative: { pathway: 'Methylation Pathway', status: 'actionable', body: '', priority: '', hint: '', geneCount: 1, actionCount: 2 },
    genes: [mockGenes[0]],
  },
  {
    narrative: { pathway: 'Serotonin & Neuroplasticity', status: 'monitor', body: '', priority: '', hint: '', geneCount: 2, actionCount: 2 },
    genes: [mockGenes[1], mockGenes[2]],
  },
]

const mockActions: Record<string, ActionData[]> = {
  MTHFR: [
    { id: 'mthfr-0', type: 'consider', title: 'Methylfolate 400-800mcg/day', description: '', evidenceTier: 'E1', studyCount: 50, tags: [], geneSymbol: 'MTHFR', done: false },
    { id: 'mthfr-1', type: 'monitor', title: 'Test homocysteine levels', description: '', evidenceTier: 'E1', studyCount: 50, tags: [], geneSymbol: 'MTHFR', done: false },
  ],
  SLC6A4: [
    { id: 'slc6a4-0', type: 'discuss', title: 'Discuss SSRI dose with psychiatrist', description: '', evidenceTier: 'E2', studyCount: 30, tags: [], geneSymbol: 'SLC6A4', done: false },
  ],
  BDNF: [
    { id: 'bdnf-0', type: 'try', title: 'Morning sunlight 15-20min', description: '', evidenceTier: 'E2', studyCount: 20, tags: [], geneSymbol: 'BDNF', done: false },
  ],
}

describe('ActionRoadmap', () => {
  it('renders roadmap header', () => {
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} />)
    expect(screen.getByText('ACTION ROADMAP')).toBeInTheDocument()
  })

  it('renders top 5 actions by default (or all if fewer)', () => {
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} />)
    expect(screen.getByText('Methylfolate 400-800mcg/day')).toBeInTheDocument()
    expect(screen.getByText('Test homocysteine levels')).toBeInTheDocument()
    expect(screen.getByText('Discuss SSRI dose with psychiatrist')).toBeInTheDocument()
    expect(screen.getByText('Morning sunlight 15-20min')).toBeInTheDocument()
  })

  it('ranks actionable E1 genes first', () => {
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} />)
    const items = screen.getAllByTestId('roadmap-item')
    // MTHFR actions should be first (actionable=30 + E1=25 + type)
    expect(items[0]).toHaveTextContent('MTHFR')
  })

  it('shows gene symbol and metadata for each action', () => {
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} />)
    expect(screen.getByText(/MTHFR.*Actionable.*E1/)).toBeInTheDocument()
  })

  it('calls onAddToChecklist when + button clicked', () => {
    const onAdd = vi.fn()
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={onAdd} />)
    const addButtons = screen.getAllByLabelText('Add to checklist')
    fireEvent.click(addButtons[0])
    expect(onAdd).toHaveBeenCalledTimes(1)
  })

  it('respects category filter', () => {
    render(
      <ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} activeCategory="sleep" />,
    )
    // No genes have sleep category in mock data
    expect(screen.queryByTestId('roadmap-item')).not.toBeInTheDocument()
  })

  it('respects action type filter', () => {
    render(
      <ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} activeActionType="discuss" />,
    )
    expect(screen.getByText('Discuss SSRI dose with psychiatrist')).toBeInTheDocument()
    expect(screen.queryByText('Methylfolate 400-800mcg/day')).not.toBeInTheDocument()
  })

  it('shows expand toggle when more than 5 actions', () => {
    // With 4 actions in mock, toggle should NOT show
    render(<ActionRoadmap sections={mockSections} actions={mockActions} onAddToChecklist={vi.fn()} />)
    expect(screen.queryByText(/SHOW ALL/)).not.toBeInTheDocument()
  })

  it('hides roadmap when no actions available', () => {
    render(<ActionRoadmap sections={mockSections} actions={{}} onAddToChecklist={vi.fn()} />)
    expect(screen.queryByText('ACTION ROADMAP')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/__tests__/ActionRoadmap.test.tsx`

Expected: FAIL — module not found.

- [ ] **Step 3: Implement ActionRoadmap component**

Create `frontend/src/components/mental-health/ActionRoadmap.tsx`:

```tsx
import { useState } from 'react'
import type { ActionData, GeneData, PathwaySection, Category, ActionType } from '../../types/genomics'

interface RankedAction {
  action: ActionData
  gene: GeneData
  score: number
}

const STATUS_SCORES: Record<string, number> = {
  actionable: 30, monitor: 20, optimal: 10, neutral: 0,
}

const EVIDENCE_SCORES: Record<string, number> = {
  E1: 25, E2: 20, E3: 15, E4: 10, E5: 5,
}

const TYPE_SCORES: Record<string, number> = {
  discuss: 4, monitor: 3, consider: 2, try: 1,
}

function scoreAction(action: ActionData, gene: GeneData): number {
  return (STATUS_SCORES[gene.status] ?? 0)
    + (EVIDENCE_SCORES[gene.evidenceTier] ?? 10)
    + (TYPE_SCORES[action.type] ?? 1)
}

function rankColor(score: number): string {
  if (score >= 50) return 'var(--sig-risk)'
  if (score >= 30) return 'var(--sig-reduced)'
  return 'var(--sig-benefit)'
}

const DEFAULT_VISIBLE = 5

interface ActionRoadmapProps {
  sections: PathwaySection[]
  actions: Record<string, ActionData[]>
  onAddToChecklist: (action: ActionData) => void
  checklistIds?: Set<string>
  activeCategory?: Category | null
  activeActionType?: ActionType | null
}

export function ActionRoadmap({
  sections,
  actions,
  onAddToChecklist,
  checklistIds = new Set(),
  activeCategory = null,
  activeActionType = null,
}: ActionRoadmapProps) {
  const [expanded, setExpanded] = useState(false)

  // Build gene lookup from sections
  const geneMap = new Map<string, GeneData>()
  for (const section of sections) {
    for (const gene of section.genes) {
      geneMap.set(gene.symbol, gene)
    }
  }

  // Collect, filter, score, and rank all actions
  const ranked: RankedAction[] = []
  for (const [symbol, geneActions] of Object.entries(actions)) {
    const gene = geneMap.get(symbol)
    if (!gene) continue

    // Category filter
    if (activeCategory && !gene.categories.includes(activeCategory)) continue

    for (const action of geneActions) {
      // Action type filter
      if (activeActionType && action.type !== activeActionType) continue

      ranked.push({
        action,
        gene,
        score: scoreAction(action, gene),
      })
    }
  }

  // Sort descending by score, then alphabetically by gene symbol
  ranked.sort((a, b) => b.score - a.score || a.gene.symbol.localeCompare(b.gene.symbol))

  if (ranked.length === 0) return null

  const visible = expanded ? ranked : ranked.slice(0, DEFAULT_VISIBLE)
  const hasMore = ranked.length > DEFAULT_VISIBLE

  return (
    <div style={{
      padding: '12px 24px',
      borderBottom: '1px dashed var(--border-dashed)',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 600,
          color: 'var(--sig-risk)',
          letterSpacing: '0.1em',
        }}>
          ACTION ROADMAP
        </span>
        {hasMore && (
          <button
            onClick={() => setExpanded(prev => !prev)}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 'var(--font-size-xs)',
              color: 'var(--text-tertiary)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
              letterSpacing: '0.08em',
            }}
          >
            {expanded ? 'SHOW LESS' : `SHOW ALL ${ranked.length}`}
          </button>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {visible.map((item, idx) => {
          const added = checklistIds.has(item.action.id)
          return (
            <div
              key={item.action.id}
              data-testid="roadmap-item"
              style={{
                display: 'flex',
                gap: 10,
                alignItems: 'flex-start',
                padding: '8px 0',
                borderBottom: idx < visible.length - 1 ? '1px solid var(--border)' : undefined,
              }}
            >
              <div style={{
                width: 22,
                height: 22,
                borderRadius: '50%',
                background: rankColor(item.score),
                color: 'var(--bg)',
                fontSize: 'var(--font-size-xs)',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}>
                {idx + 1}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 'var(--font-size-sm)', lineHeight: 1.5 }}>
                  {item.action.title}
                </div>
                <div style={{
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--text-tertiary)',
                  marginTop: 1,
                }}>
                  {item.gene.symbol} &middot; {item.gene.status.charAt(0).toUpperCase() + item.gene.status.slice(1)} &middot; {item.gene.evidenceTier} &middot; {item.action.type.charAt(0).toUpperCase() + item.action.type.slice(1)}
                </div>
              </div>
              <button
                aria-label={added ? 'Added to checklist' : 'Add to checklist'}
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--font-size-xs)',
                  padding: '2px 6px',
                  border: `1px solid ${added ? 'var(--sig-benefit)' : 'var(--border)'}`,
                  borderRadius: 2,
                  background: 'none',
                  color: added ? 'var(--sig-benefit)' : 'var(--text-tertiary)',
                  cursor: added ? 'default' : 'pointer',
                  flexShrink: 0,
                  opacity: added ? 0.4 : 0.6,
                }}
                disabled={added}
                onClick={() => onAddToChecklist(item.action)}
                onMouseEnter={e => { if (!added) e.currentTarget.style.opacity = '1' }}
                onMouseLeave={e => { e.currentTarget.style.opacity = added ? '0.4' : '0.6' }}
              >
                {added ? 'ADDED' : '+'}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/__tests__/ActionRoadmap.test.tsx`

Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/mental-health/ActionRoadmap.tsx frontend/src/__tests__/ActionRoadmap.test.tsx
git commit -m "feat(#24): add ActionRoadmap component with scoring and tests"
```

---

### Task 2: Wire ActionRoadmap into MentalHealthDashboard

**Files:**
- Modify: `frontend/src/components/mental-health/MentalHealthDashboard.tsx`

- [ ] **Step 1: Add import**

Add at the top of `frontend/src/components/mental-health/MentalHealthDashboard.tsx`, after the existing imports:

```typescript
import { ActionRoadmap } from './ActionRoadmap'
```

- [ ] **Step 2: Insert ActionRoadmap between FilterBar and Legend**

In the component's return JSX, after the `<FilterBar ... />` closing tag and before the `{/* Color legend */}` comment, add:

```tsx
      <ActionRoadmap
        sections={data}
        actions={actions}
        onAddToChecklist={onAddToChecklist ? (action) => onAddToChecklist(action) : () => {}}
        checklistIds={checklistIds}
        activeCategory={activeCategory}
        activeActionType={activeActionType}
      />
```

- [ ] **Step 3: Run all frontend tests**

Run: `cd frontend && npx vitest run`

Expected: All test files pass (including existing MentalHealthDashboard tests + new ActionRoadmap tests).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/mental-health/MentalHealthDashboard.tsx
git commit -m "feat(#24): wire ActionRoadmap into MentalHealthDashboard"
```

---

### Task 3: Full test suite verification

**Files:** None (verification only)

- [ ] **Step 1: Run full frontend test suite**

Run: `cd frontend && npx vitest run`

Expected: All test files pass with 0 failures.

- [ ] **Step 2: Run full backend test suite**

Run: `cd /Users/glebkalinin/genome-toolkit && python -m pytest -x -q`

Expected: All tests pass.

- [ ] **Step 3: Commit (if any fixups needed)**

```bash
git add -A && git commit -m "test(#24): verify action roadmap integration"
```
