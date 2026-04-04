# Genome Toolkit Web — MVP Design Spec

## Overview

Self-hosted web platform for exploring personal genomic data. Users import their 23andMe/AncestryDNA/VCF files and browse variants through a searchable table with AI assistant powered by Claude Agent SDK.

**MVP scope:** Import pipeline + SNP Browser + AI chat

**Target user:** Anyone with raw genetic data who wants to understand their variants. Self-hosted on their own machine.

## Architecture

Hybrid: Python Agent SDK backend + React SPA frontend. Single process, single port.

```
React SPA (Vite)
  ├── SNPTable (TanStack Table + Virtual)
  ├── CommandPalette (Cmd+K, SSE stream)
  ├── FilterBar (search + dropdowns)
  └── VariantDrawer (slide-out detail)
        │ HTTP/REST          │ SSE
        ▼                    ▼
FastAPI
  ├── /api/snps      — paginated variant queries
  ├── /api/genes     — gene listing + detail
  ├── /api/import    — file import trigger
  ├── /api/chat      — SSE stream (Agent SDK)
  └── /api/sessions  — session management
        │                    │
        ▼                    ▼
  genome.db              Python Agent SDK
  (variants +            (per-session agents
   annotations)           with tools)
  users.db
  (sessions, chat,
   prefs, imports)
```

### Key decisions

- **FastAPI** is the only server. Serves API, SSE stream, and built SPA static files.
- **SSE** for agent streaming (not WebSocket) — simpler, stateless-compatible.
- **Agent-per-Session** — each user session gets a dedicated agent instance with conversation history persisted in users.db. Enables contextual references ("that gene we discussed").
- **File paths, not uploads** — user provides path on disk (e.g. `~/Downloads/23andme.txt`). No file size limits, no upload overhead. Self-hosted = trusted environment, no filesystem restrictions.
- **Existing parsers reused** — 23andMe, AncestryDNA, MyHeritage, VCF parsers from `genome_toolkit/` are imported directly, not rewritten.

## Data Model

### genome.db (variant storage)

```sql
-- Existing table (up to 3.4M rows with imputed data)
variants(
    rsid TEXT,
    chromosome TEXT,
    position INTEGER,
    genotype TEXT,
    gene_symbol TEXT,
    source TEXT,           -- 23andme, ancestry, imputed, etc.
    quality REAL,
    is_imputed BOOLEAN
)

-- New: clinical context for UI
clinical_annotations(
    rsid TEXT PRIMARY KEY,
    significance TEXT,      -- risk, benefit, neutral, reduced, unknown
    condition TEXT,
    evidence_tier TEXT,     -- E1-E5
    summary TEXT,           -- one-line for table column
    pharmacogenomic BOOLEAN
)

gene_metadata(
    symbol TEXT PRIMARY KEY,
    full_name TEXT,
    chromosome TEXT,
    system TEXT,            -- Drug Metabolism, Dopamine System, etc.
    description TEXT
)
```

### users.db (application state)

```sql
sessions(
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    last_active TIMESTAMP,
    agent_history JSON      -- serialized agent conversation
)

chat_messages(
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    role TEXT,               -- user, assistant, tool
    content TEXT,
    timestamp TIMESTAMP
)

imports(
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    file_path TEXT,
    provider TEXT,           -- 23andme, ancestry, myheritage, vcf
    variant_count INTEGER,
    imported_at TIMESTAMP,
    status TEXT              -- pending, processing, done, error
)

user_preferences(
    key TEXT PRIMARY KEY,
    value JSON
)
```

### Principles

- genome.db is append-only for variants. Never modifies existing rows.
- clinical_annotations populated during import + enriched by agent on demand.
- users.db is deletable without losing genomic data.
- Single genome.db per instance (single-user self-hosted).

## API Endpoints

### Data API (REST)

```
GET  /api/snps?page=1&limit=50&search=&chr=&gene=&significance=
     Paginated variants with clinical annotations joined.

GET  /api/snps/:rsid
     Full detail for a single variant.

GET  /api/genes
     List of genes with variant counts per gene.

GET  /api/genes/:symbol
     Gene detail + all its variants.

GET  /api/stats
     Summary: total variants, counts by significance, by chromosome.

POST /api/import
     Body: { "file_path": "~/Downloads/23andme.txt" }
     Starts async import, returns import_id.

GET  /api/import/:id/status
     SSE stream of import progress events.
```

### Chat API (SSE)

```
POST /api/chat
     Body: { "session_id": "abc", "message": "what's rs1800497?" }
     Returns SSE stream:

     event: text_delta
     data: {"content": "rs1800497 is..."}

     event: tool_call
     data: {"tool": "query_snps", "args": {"rsid": "rs1800497"}}

     event: tool_result
     data: {"tool": "query_snps", "result": {...}}

     event: ui_action
     data: {"action": "filter_table", "params": {"rsid": "rs1800497"}}

     event: done
     data: {}
```

The `ui_action` event type allows the agent to control the frontend — filter the table, highlight a row, open the variant drawer. The frontend listens for these events on the SSE stream and dispatches corresponding UI updates.

### Session API

```
POST /api/sessions          Create new session
GET  /api/sessions/:id      Restore session with chat history
```

## Agent Tools

The Claude agent (Python Agent SDK) has these tools registered:

| Tool | Purpose | Trigger example |
|------|---------|----------------|
| `query_snps` | Search/filter variants in genome.db | "show all risk variants in CYP2D6" |
| `import_file` | Parse genetic file, load into genome.db | "import ~/Downloads/23andme.txt" |
| `explain_variant` | Clinical annotation for an rsID | "what does rs1800497 mean?" |
| `explain_gene` | Gene description + user's variants | "tell me about MTHFR" |
| `get_stats` | Summary statistics for loaded data | "how many variants do I have?" |
| `update_table_view` | Send filter/highlight/scroll commands to frontend | agent filters table in response to queries |

Agent-per-session: each session creates a dedicated agent instance. Conversation history stored in users.db, restored on reconnect. This enables contextual references across messages.

## Frontend Components

### SNPTable
- TanStack Table + TanStack Virtual for virtualizing up to 3.4M rows.
- Server-side pagination via `/api/snps` with query params.
- Column sorting (rsID, gene, chromosome, significance).
- Multi-column filtering synced with FilterBar.
- Row click opens VariantDrawer.
- Listens for `ui_action` SSE events to apply agent-driven filters/highlights.

### CommandPalette
- Triggered by Cmd+K (or Ctrl+K).
- Overlay on top of the table, dismissible with Esc.
- Text input → POST to `/api/chat` → SSE stream rendered with react-markdown.
- Displays streaming text deltas, tool call indicators, and final responses.
- On `ui_action` events, dispatches to table/drawer.
- Built with `cmdk` library (used by Vercel, Linear).

### FilterBar
- Persistent bar below the top nav.
- Search input (rsID, gene name, free text).
- Dropdown filters: Significance, Chromosome, System.
- Active filter chips with clear button.
- "Clinically relevant" quick filter toggle (default on for first load).
- Syncs with URL search params for shareable state.
- Agent can set filters programmatically via `ui_action` events.

### VariantDrawer
- Slide-out panel from right side on row click.
- Shows: rsID, genotype, gene, chromosome, position, clinical significance, evidence tier, summary, related conditions, protocols.
- "Ask AI about this" button opens CommandPalette pre-filled with variant context.
- Closeable with Esc or click outside.

### OnboardingChat
- Shown on first visit (no variants in genome.db).
- CommandPalette auto-opens, full-screen centered.
- Agent greets user, asks for file path.
- Import progress streamed in chat.
- On completion, transitions to full table view.

## Onboarding Flow

1. User opens app for the first time. Empty state: centered CommandPalette.
2. Agent: "Welcome! I'm your genome assistant. Paste the path to your 23andMe, AncestryDNA, MyHeritage, or VCF file to get started."
3. User types: `~/Downloads/genome_23andme_full.txt`
4. Agent calls `import_file` tool. SSE streams progress: format detection, parsing, variant count updates.
5. Agent: "Done! 960,614 variants loaded. 42 clinically significant, 18 pharmacogenomic. Press Esc to explore your data, or ask me anything."
6. User presses Esc → full SNPTable with "clinically relevant" filter active.

## Project Structure

```
genome-toolkit/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, static mount
│   │   ├── routes/
│   │   │   ├── snps.py          # /api/snps, /api/snps/:rsid
│   │   │   ├── genes.py         # /api/genes
│   │   │   ├── import_.py       # /api/import
│   │   │   ├── chat.py          # /api/chat (SSE stream)
│   │   │   └── sessions.py      # /api/sessions
│   │   ├── agent/
│   │   │   ├── agent.py         # Agent SDK setup, tool registration
│   │   │   ├── tools.py         # query_snps, import_file, explain_variant...
│   │   │   └── session_store.py # persist/restore agent sessions
│   │   ├── db/
│   │   │   ├── genome.py        # genome.db connection, queries
│   │   │   └── users.py         # users.db connection, queries
│   │   └── parsers/             # reuse from genome_toolkit/
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── SNPTable.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   ├── CommandPalette.tsx
│   │   │   ├── VariantDrawer.tsx
│   │   │   └── OnboardingChat.tsx
│   │   ├── hooks/
│   │   │   ├── useChat.ts       # SSE stream + ui_action handler
│   │   │   └── useSNPs.ts       # pagination, filters, search
│   │   └── lib/
│   │       └── sse.ts           # SSE client with event parsing
│   ├── package.json
│   └── vite.config.ts
├── data/                         # runtime, gitignored
│   ├── genome.db
│   └── users.db
├── scripts/
│   └── setup.sh                  # pip install + npm install + init DBs
└── README.md
```

### Python dependencies

- `fastapi`, `uvicorn` — server
- `claude-agent-sdk` — agent
- `aiosqlite` — async SQLite access
- Existing: `python-frontmatter`, `pyyaml`, `rich`

### Frontend dependencies

- `react`, `react-dom`
- `@tanstack/react-table`, `@tanstack/react-virtual`
- `react-markdown` — render agent responses
- `cmdk` — command palette component

### User setup

```bash
git clone <repo> && cd genome-toolkit
./scripts/setup.sh          # installs Python + Node deps, inits DBs
export ANTHROPIC_API_KEY=sk-...
python -m backend.app.main  # serves API + built SPA on :8000
```

## Out of Scope (Future)

- Imputation guide and file preparation
- Triage system integration
- Biomarker tracking
- Assessment tools
- Multi-user / auth
- Vault integration (Obsidian)
- PostgreSQL migration
