# Page-Aware Chat Context — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the AI chat agent aware of which page the user is viewing and what data is on screen, so questions are answered in context.

**Architecture:** Frontend builds a plain-text page context summary from current view + hook data, passes it through the chat pipeline to the backend, which injects it into the agent's system prompt. Each message carries fresh context.

**Tech Stack:** TypeScript (frontend), Python/FastAPI (backend), Claude Agent SDK

---

### Task 1: Create `buildPageContext` with tests (TDD)

**Files:**
- Create: `frontend/src/lib/pageContext.ts`
- Create: `frontend/src/__tests__/pageContext.test.ts`

- [ ] **Step 1: Write the failing tests**

```ts
// frontend/src/__tests__/pageContext.test.ts
import { describe, it, expect } from 'vitest'
import { buildPageContext } from '../lib/pageContext'
import type { PageContextData } from '../lib/pageContext'

describe('buildPageContext', () => {
  it('returns risk page context with causes and genes', () => {
    const data: PageContextData = {
      mentalHealth: { sections: [], totalGenes: 0, totalActions: 0 },
      checklist: { pendingCount: 0, doneCount: 0, items: [] },
      snps: { result: { items: [], total: 0, page: 1, limit: 100 }, filters: { search: '', chromosome: '', source: '', clinical: true, significance: '', gene: '', condition: '', zygosity: '', page: 1, limit: 100 }, selectedSNP: null },
    }
    const ctx = buildPageContext('risk', data)
    expect(ctx).toContain('RISK LANDSCAPE')
    expect(ctx.length).toBeGreaterThan(20)
  })

  it('returns mental-health context with pathway and gene info', () => {
    const data: PageContextData = {
      mentalHealth: {
        sections: [{
          narrative: { pathway: 'Methylation', status: 'actionable', body: '', priority: '', hint: '', geneCount: 2, actionCount: 3 },
          genes: [
            { symbol: 'MTHFR', variant: 'C677T', rsid: 'rs1801133', genotype: 'T/T', status: 'actionable', evidenceTier: 'E2', studyCount: 12, description: 'Reduced folate.', actionCount: 1, categories: ['mood'], pathway: 'Methylation' },
            { symbol: 'COMT', variant: 'Val158Met', rsid: 'rs4680', genotype: 'A/G', status: 'monitor', evidenceTier: 'E2', studyCount: 30, description: 'Intermediate.', actionCount: 2, categories: ['mood'], pathway: 'Methylation' },
          ],
        }],
        totalGenes: 2,
        totalActions: 3,
      },
      checklist: { pendingCount: 1, doneCount: 0, items: [] },
      snps: { result: { items: [], total: 0, page: 1, limit: 100 }, filters: { search: '', chromosome: '', source: '', clinical: true, significance: '', gene: '', condition: '', zygosity: '', page: 1, limit: 100 }, selectedSNP: null },
    }
    const ctx = buildPageContext('mental-health', data)
    expect(ctx).toContain('MENTAL HEALTH')
    expect(ctx).toContain('Methylation')
    expect(ctx).toContain('MTHFR')
    expect(ctx).toContain('2 genes')
    expect(ctx).toContain('3 actions')
  })

  it('returns pgx context', () => {
    const data: PageContextData = {
      mentalHealth: { sections: [], totalGenes: 0, totalActions: 0 },
      checklist: { pendingCount: 0, doneCount: 0, items: [] },
      snps: { result: { items: [], total: 0, page: 1, limit: 100 }, filters: { search: '', chromosome: '', source: '', clinical: true, significance: '', gene: '', condition: '', zygosity: '', page: 1, limit: 100 }, selectedSNP: null },
    }
    const ctx = buildPageContext('pgx', data)
    expect(ctx).toContain('PGX / DRUG METABOLISM')
  })

  it('returns addiction context', () => {
    const data: PageContextData = {
      mentalHealth: { sections: [], totalGenes: 0, totalActions: 0 },
      checklist: { pendingCount: 0, doneCount: 0, items: [] },
      snps: { result: { items: [], total: 0, page: 1, limit: 100 }, filters: { search: '', chromosome: '', source: '', clinical: true, significance: '', gene: '', condition: '', zygosity: '', page: 1, limit: 100 }, selectedSNP: null },
    }
    const ctx = buildPageContext('addiction', data)
    expect(ctx).toContain('ADDICTION & REWARD')
  })

  it('returns snps context with filter info', () => {
    const data: PageContextData = {
      mentalHealth: { sections: [], totalGenes: 0, totalActions: 0 },
      checklist: { pendingCount: 0, doneCount: 0, items: [] },
      snps: {
        result: { items: [], total: 3400000, page: 1, limit: 100 },
        filters: { search: 'MTHFR', chromosome: '1', source: '', clinical: true, significance: '', gene: 'MTHFR', condition: '', zygosity: '', page: 1, limit: 100 },
        selectedSNP: { rsid: 'rs1801133', chromosome: '1', position: 11856378, genotype: 'T/T', is_rsid: true, source: 'genotyped', r2_quality: null, significance: 'Pathogenic', disease: 'MTHFR deficiency', gene_symbol: 'MTHFR' },
      },
    }
    const ctx = buildPageContext('snps', data)
    expect(ctx).toContain('SNP BROWSER')
    expect(ctx).toContain('3,400,000')
    expect(ctx).toContain('MTHFR')
    expect(ctx).toContain('rs1801133')
    expect(ctx).toContain('Pathogenic')
  })

  it('includes checklist summary when items exist', () => {
    const data: PageContextData = {
      mentalHealth: { sections: [], totalGenes: 0, totalActions: 0 },
      checklist: { pendingCount: 3, doneCount: 1, items: [] },
      snps: { result: { items: [], total: 0, page: 1, limit: 100 }, filters: { search: '', chromosome: '', source: '', clinical: true, significance: '', gene: '', condition: '', zygosity: '', page: 1, limit: 100 }, selectedSNP: null },
    }
    const ctx = buildPageContext('risk', data)
    expect(ctx).toContain('3 pending')
    expect(ctx).toContain('1 done')
  })

  it('handles empty mental-health data gracefully', () => {
    const data: PageContextData = {
      mentalHealth: { sections: [], totalGenes: 0, totalActions: 0 },
      checklist: { pendingCount: 0, doneCount: 0, items: [] },
      snps: { result: { items: [], total: 0, page: 1, limit: 100 }, filters: { search: '', chromosome: '', source: '', clinical: true, significance: '', gene: '', condition: '', zygosity: '', page: 1, limit: 100 }, selectedSNP: null },
    }
    const ctx = buildPageContext('mental-health', data)
    expect(ctx).toContain('MENTAL HEALTH')
    expect(ctx).toContain('0 genes')
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/__tests__/pageContext.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Implement `buildPageContext`**

```ts
// frontend/src/lib/pageContext.ts
import type { PathwaySection } from '../types/genomics'
import type { SNP, SNPFilters, SNPResult } from '../hooks/useSNPs'

export interface PageContextData {
  mentalHealth: {
    sections: PathwaySection[]
    totalGenes: number
    totalActions: number
  }
  checklist: {
    pendingCount: number
    doneCount: number
    items: { title: string; gene_symbol: string }[]
  }
  snps: {
    result: SNPResult
    filters: SNPFilters
    selectedSNP: SNP | null
  }
}

const VIEW_NAMES: Record<string, string> = {
  'risk': 'RISK LANDSCAPE',
  'mental-health': 'MENTAL HEALTH',
  'pgx': 'PGX / DRUG METABOLISM',
  'addiction': 'ADDICTION & REWARD',
  'snps': 'SNP BROWSER',
}

export function buildPageContext(view: string, data: PageContextData): string {
  const lines: string[] = []
  const name = VIEW_NAMES[view] || view.toUpperCase()
  lines.push(`You are on the ${name} page.`)

  // View-specific context
  if (view === 'mental-health') {
    lines.push(buildMentalHealthContext(data))
  } else if (view === 'snps') {
    lines.push(buildSNPsContext(data))
  } else if (view === 'risk') {
    lines.push('This page shows the top causes of mortality ranked by population prevalence, overlaid with the user\'s personal genetic risk factors.')
    lines.push('Use your genome tools to look up specific risk genes if the user asks about a cause.')
  } else if (view === 'pgx') {
    lines.push('This page shows pharmacogenomic enzyme activity (CYP2D6, CYP2C19, etc.), drug metabolism predictions, and substance-specific harm reduction notes.')
    lines.push('Use your genome tools to look up specific enzyme genes if the user asks about a drug.')
  } else if (view === 'addiction') {
    lines.push('This page shows addiction & reward pathways (dopamine, opioid, GABA, endocannabinoid), substance-specific harm reduction cards, and pathway gene analysis.')
    lines.push('Use your genome tools to look up specific addiction-related genes if the user asks.')
  }

  // Checklist summary (always)
  if (data.checklist.pendingCount > 0 || data.checklist.doneCount > 0) {
    lines.push(`Checklist: ${data.checklist.pendingCount} pending, ${data.checklist.doneCount} done.`)
  }

  return lines.filter(Boolean).join('\n')
}

function buildMentalHealthContext(data: PageContextData): string {
  const { sections, totalGenes, totalActions } = data.mentalHealth
  const lines: string[] = []
  lines.push(`${totalGenes} genes analyzed, ${totalActions} actions available.`)

  for (const section of sections) {
    const n = section.narrative
    const geneList = section.genes.map(g => {
      const status = g.status === 'actionable' ? '!' : g.status === 'monitor' ? '~' : ''
      return `${status}${g.symbol} ${g.variant} ${g.genotype}`
    }).join(', ')
    lines.push(`${n.pathway} [${n.status}]: ${n.geneCount} genes, ${n.actionCount} actions. Genes: ${geneList}`)
  }

  return lines.join('\n')
}

function buildSNPsContext(data: PageContextData): string {
  const { result, filters, selectedSNP } = data.snps
  const lines: string[] = []
  lines.push(`Showing ${result.total.toLocaleString()} variants.`)

  const activeFilters: string[] = []
  if (filters.search) activeFilters.push(`search="${filters.search}"`)
  if (filters.chromosome) activeFilters.push(`chr=${filters.chromosome}`)
  if (filters.gene) activeFilters.push(`gene=${filters.gene}`)
  if (filters.significance) activeFilters.push(`significance=${filters.significance}`)
  if (filters.condition) activeFilters.push(`condition="${filters.condition}"`)
  if (filters.clinical) activeFilters.push('clinical=on')
  if (filters.source) activeFilters.push(`source=${filters.source}`)
  if (filters.zygosity) activeFilters.push(`zygosity=${filters.zygosity}`)
  if (activeFilters.length > 0) {
    lines.push(`Active filters: ${activeFilters.join(', ')}`)
  }

  if (selectedSNP) {
    lines.push(`Selected variant: ${selectedSNP.rsid} (${selectedSNP.gene_symbol || 'no gene'}, ${selectedSNP.genotype}, ${selectedSNP.significance || 'no significance'})`)
  }

  return lines.join('\n')
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/__tests__/pageContext.test.ts`
Expected: all 7 PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/pageContext.ts frontend/src/__tests__/pageContext.test.ts
git commit -m "feat: add buildPageContext for page-aware AI chat"
```

---

### Task 2: Thread `pageContext` through SSE and useChat

**Files:**
- Modify: `frontend/src/lib/sse.ts`
- Modify: `frontend/src/hooks/useChat.ts`

- [ ] **Step 1: Update `streamChat` to accept and send `pageContext`**

In `frontend/src/lib/sse.ts`, change the function signature and POST body:

```ts
export async function* streamChat(
  sessionId: string,
  message: string,
  signal?: AbortSignal,
  pageContext?: string,
): AsyncGenerator<SSEEvent> {
  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      ...(pageContext ? { page_context: pageContext } : {}),
    }),
    signal,
  })
```

- [ ] **Step 2: Update `useChat.send` to accept and pass `pageContext`**

In `frontend/src/hooks/useChat.ts`, update the `send` callback signature:

```ts
  const send = useCallback(async (text: string, pageContext?: string) => {
    if (!sessionId || streaming) return

    // ... existing setup code ...

    try {
      for await (const event of streamChat(sessionId, text, abort.signal, pageContext)) {
```

Update the deps array — no new deps needed since `pageContext` is a parameter.

- [ ] **Step 3: Run existing tests to verify nothing breaks**

Run: `cd frontend && npx vitest run src/__tests__/sse.test.ts src/__tests__/useChat.test.ts`
Expected: all PASS (pageContext is optional, existing calls don't pass it)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/sse.ts frontend/src/hooks/useChat.ts
git commit -m "feat: thread pageContext through streamChat and useChat.send"
```

---

### Task 3: Wire `buildPageContext` into App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Import and build context in send wrapper**

Add import at top of App.tsx:

```ts
import { buildPageContext } from './lib/pageContext'
import type { PageContextData } from './lib/pageContext'
```

- [ ] **Step 2: Create a `getPageContext` helper inside App**

Add after the existing `send` wrapper (around line 129):

```ts
  const getPageContext = useCallback((): string => {
    const data: PageContextData = {
      mentalHealth: {
        sections: mentalHealth.sections,
        totalGenes: mentalHealth.totalGenes,
        totalActions: mentalHealth.totalActions,
      },
      checklist: {
        pendingCount: checklist.pendingCount,
        doneCount: checklist.doneCount,
        items: checklist.items,
      },
      snps: {
        result,
        filters,
        selectedSNP,
      },
    }
    return buildPageContext(view, data)
  }, [view, mentalHealth, checklist, result, filters, selectedSNP])
```

- [ ] **Step 3: Update the `send` wrapper to include context**

Replace the existing `send` wrapper (~line 123-129):

```ts
  const send = useCallback((text: string) => {
    const ctx = getPageContext()
    if (voice.voiceEnabled) {
      rawSend('[VOICE] ' + text, ctx)
    } else {
      rawSend(text, ctx)
    }
  }, [rawSend, voice.voiceEnabled, getPageContext])
```

- [ ] **Step 4: Run full test suite**

Run: `cd frontend && npx vitest run`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: wire buildPageContext into App.tsx send wrapper"
```

---

### Task 4: Backend — accept and inject `page_context`

**Files:**
- Modify: `backend/app/routes/chat.py`
- Modify: `backend/app/agent/agent.py`

- [ ] **Step 1: Add `page_context` to ChatRequest model**

In `backend/app/routes/chat.py`, update the model:

```python
class ChatRequest(BaseModel):
    session_id: str
    message: str
    page_context: str | None = None
```

- [ ] **Step 2: Pass `page_context` to agent session creation**

In `backend/app/routes/chat.py`, update `get_or_create_client` and `event_stream`:

```python
    async def get_or_create_client(session_id: str, page_context: str | None = None):
        """Get existing client or create new one. Handles stale connections."""
        client = _active_clients.get(session_id)
        if client is not None:
            # Update system prompt with fresh page context
            if page_context:
                client.options.system_prompt = build_system_prompt(page_context)
            return client

        client, _ = await create_agent_session(page_context=page_context)
        await client.connect()
        _active_clients[session_id] = client
        return client

    async def event_stream():
        text_parts = []
        try:
            client = await get_or_create_client(req.session_id, req.page_context)
```

- [ ] **Step 3: Update `create_agent_session` and add `build_system_prompt`**

In `backend/app/agent/agent.py`, add the helper and update the function:

```python
def build_system_prompt(page_context: str | None = None) -> str:
    """Build system prompt, optionally injecting page context."""
    if not page_context:
        return SYSTEM_PROMPT
    return (
        SYSTEM_PROMPT
        + "\n\n## User's Current Page Context\n"
        + page_context
        + "\n\nUse this context to give relevant answers. The user can see this data on their screen right now."
    )


async def create_agent_session(
    cwd: str | None = None,
    page_context: str | None = None,
) -> tuple[ClaudeSDKClient, str | None]:
```

And update the options inside `create_agent_session`:

```python
    options = ClaudeAgentOptions(
        system_prompt=build_system_prompt(page_context),
        # ... rest unchanged
    )
```

- [ ] **Step 4: Verify backend starts without errors**

Run: `cd /Users/glebkalinin/genome-toolkit && python -c "from backend.app.agent.agent import build_system_prompt; print(build_system_prompt('test')[:100])"`
Expected: prints system prompt text starting with "You are a genome data assistant..."

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/chat.py backend/app/agent/agent.py
git commit -m "feat: backend accepts page_context and injects into system prompt"
```

---

### Task 5: Full integration test

**Files:** None (manual verification)

- [ ] **Step 1: Run full frontend test suite**

Run: `cd frontend && npx vitest run`
Expected: all 338+ tests PASS

- [ ] **Step 2: Start the app and verify**

Run the dev server. Navigate to Risk page. Open Ask AI. Type "What should I focus on?" — the agent should respond with risk-specific context without needing the user to mention "risk page".

Switch to PGx page. Ask "Any drug interactions I should know about?" — agent should respond in PGx context.

- [ ] **Step 3: Push**

```bash
git push
```
