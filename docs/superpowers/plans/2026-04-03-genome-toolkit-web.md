# Genome Toolkit Web — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-hosted web platform for browsing personal genomic data with AI chat assistant.

**Architecture:** FastAPI backend serving REST API + SSE chat stream + built React SPA. Anthropic Python SDK with tool use for the AI agent (not Agent SDK — it requires CLI subprocess, unsuitable for web servers). SQLite for storage (genome.db for variants, users.db for app state).

**Tech Stack:** Python 3.10+ / FastAPI / aiosqlite / anthropic SDK / React 18 / Vite / TanStack Table / cmdk

**Design Language:** Retro scientific instrument panel aesthetic inspired by reference images:
- Background: warm cream `#e8e4dc`
- Primary: muted steel blue `#5b7ea1`
- Accent: terracotta `#c4724e`
- Typography: monospace (`IBM Plex Mono`), uppercase labels with `letter-spacing: 0.15em`, underscore separators
- Borders: thin `1px` lines, dashed for secondary elements
- Spacing: very generous (24-32px between sections)
- UI elements: thin-bordered buttons/inputs, no shadows, no border-radius > 2px

**Important:** The existing `genome.db` uses table `snps` (not `variants`), with columns: `rsid`, `chromosome`, `position`, `genotype`, `is_rsid`, `source`, `r2_quality`, `imported_at`. It also has `genes`, `enrichments`, `phenotypes`, `notes` tables. Use the real schema, not the idealized one from the spec.

---

### Task 1: Backend Scaffold

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/requirements.txt`

- [ ] **Step 1: Create backend package structure**

```bash
mkdir -p backend/app/routes backend/app/db backend/app/agent
touch backend/__init__.py backend/app/__init__.py backend/app/routes/__init__.py backend/app/db/__init__.py backend/app/agent/__init__.py
```

- [ ] **Step 2: Write requirements.txt**

Create `backend/requirements.txt`:

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
aiosqlite>=0.20.0
anthropic>=0.52.0
python-frontmatter>=1.0.0
PyYAML>=6.0
sse-starlette>=2.0.0
```

- [ ] **Step 3: Write FastAPI app entry point**

Create `backend/app/main.py`:

```python
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.db.genome import GenomeDB
from backend.app.db.users import UsersDB

app = FastAPI(title="Genome Toolkit", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(os.environ.get("GENOME_DATA_DIR", "./data"))
GENOME_DB_PATH = Path(os.environ.get("GENOME_DB_PATH", str(DATA_DIR / "genome.db")))
USERS_DB_PATH = DATA_DIR / "users.db"

genome_db = GenomeDB(GENOME_DB_PATH)
users_db = UsersDB(USERS_DB_PATH)


@app.on_event("startup")
async def startup():
    await genome_db.connect()
    await users_db.connect()
    await users_db.init_schema()


@app.on_event("shutdown")
async def shutdown():
    await genome_db.close()
    await users_db.close()


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Verify it starts**

```bash
cd /path/to/genome-toolkit
pip install -r backend/requirements.txt
GENOME_DB_PATH=~/genome-vault/data/genome.db python -c "from backend.app.main import app; print('OK')"
```

Expected: `OK` (import succeeds — server doesn't need to run yet, db classes don't exist yet so this will fail until Task 2).

- [ ] **Step 5: Commit**

```bash
git add backend/ && git commit -m "feat: scaffold backend package with FastAPI entry point"
```

---

### Task 2: Database Layer — GenomeDB

**Files:**
- Create: `backend/app/db/genome.py`
- Create: `tests/backend/__init__.py`
- Create: `tests/backend/test_genome_db.py`

- [ ] **Step 1: Write failing test for GenomeDB**

Create `tests/backend/__init__.py` (empty).

Create `tests/backend/test_genome_db.py`:

```python
import pytest
import aiosqlite
from pathlib import Path

from backend.app.db.genome import GenomeDB


@pytest.fixture
async def genome_db(tmp_path):
    db_path = tmp_path / "test_genome.db"
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("""
            CREATE TABLE snps (
                rsid TEXT PRIMARY KEY,
                chromosome TEXT NOT NULL,
                position INTEGER NOT NULL,
                genotype TEXT NOT NULL,
                is_rsid BOOLEAN NOT NULL DEFAULT 1,
                source TEXT DEFAULT 'genotyped',
                r2_quality REAL,
                imported_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await conn.execute("CREATE INDEX idx_snps_chr_pos ON snps(chromosome, position)")
        await conn.execute("""
            CREATE TABLE genes (
                gene_symbol TEXT PRIMARY KEY,
                full_name TEXT,
                chromosome TEXT,
                rsids TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE enrichments (
                rsid TEXT NOT NULL,
                source TEXT NOT NULL,
                data TEXT NOT NULL,
                fetched_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT,
                PRIMARY KEY (rsid, source)
            )
        """)
        # Insert test data
        test_snps = [
            ("rs1065852", "22", 42526694, "CT", 1, "genotyped", None),
            ("rs4680", "22", 19951271, "GA", 1, "genotyped", None),
            ("rs1800497", "11", 113270828, "CT", 1, "genotyped", None),
            ("rs1801133", "1", 11856378, "CT", 1, "genotyped", None),
            ("rs1799971", "6", 154360797, "AG", 1, "genotyped", None),
            ("i713426", "1", 1000000, "AA", 0, "genotyped", None),
            ("rs999999", "1", 2000000, "GG", 1, "imputed", 0.85),
        ]
        await conn.executemany(
            "INSERT INTO snps (rsid, chromosome, position, genotype, is_rsid, source, r2_quality) VALUES (?, ?, ?, ?, ?, ?, ?)",
            test_snps,
        )
        await conn.commit()

    db = GenomeDB(db_path)
    await db.connect()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_count_snps(genome_db):
    count = await genome_db.count()
    assert count == 7


@pytest.mark.asyncio
async def test_query_paginated(genome_db):
    result = await genome_db.query_snps(page=1, limit=3)
    assert len(result["items"]) == 3
    assert result["total"] == 7
    assert result["page"] == 1


@pytest.mark.asyncio
async def test_query_search_by_rsid(genome_db):
    result = await genome_db.query_snps(search="rs4680")
    assert len(result["items"]) == 1
    assert result["items"][0]["rsid"] == "rs4680"


@pytest.mark.asyncio
async def test_query_filter_chromosome(genome_db):
    result = await genome_db.query_snps(chromosome="22")
    assert len(result["items"]) == 2
    assert all(item["chromosome"] == "22" for item in result["items"])


@pytest.mark.asyncio
async def test_query_filter_source(genome_db):
    result = await genome_db.query_snps(source="imputed")
    assert len(result["items"]) == 1
    assert result["items"][0]["rsid"] == "rs999999"


@pytest.mark.asyncio
async def test_get_snp_by_rsid(genome_db):
    snp = await genome_db.get_snp("rs4680")
    assert snp is not None
    assert snp["genotype"] == "GA"
    assert snp["chromosome"] == "22"


@pytest.mark.asyncio
async def test_get_snp_not_found(genome_db):
    snp = await genome_db.get_snp("rs0000000")
    assert snp is None


@pytest.mark.asyncio
async def test_get_stats(genome_db):
    stats = await genome_db.get_stats()
    assert stats["total"] == 7
    assert stats["genotyped"] == 6
    assert stats["imputed"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/backend/test_genome_db.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'backend.app.db.genome'`

- [ ] **Step 3: Implement GenomeDB**

Create `backend/app/db/genome.py`:

```python
from pathlib import Path

import aiosqlite


class GenomeDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self):
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def count(self) -> int:
        async with self._conn.execute("SELECT COUNT(*) FROM snps") as cursor:
            row = await cursor.fetchone()
            return row[0]

    async def query_snps(
        self,
        page: int = 1,
        limit: int = 50,
        search: str | None = None,
        chromosome: str | None = None,
        source: str | None = None,
    ) -> dict:
        conditions = []
        params = []

        if search:
            conditions.append("(rsid LIKE ? OR rsid = ?)")
            params.extend([f"%{search}%", search])

        if chromosome:
            conditions.append("chromosome = ?")
            params.append(chromosome)

        if source:
            conditions.append("source = ?")
            params.append(source)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Count total
        count_sql = f"SELECT COUNT(*) FROM snps {where}"
        async with self._conn.execute(count_sql, params) as cursor:
            total = (await cursor.fetchone())[0]

        # Fetch page
        offset = (page - 1) * limit
        data_sql = f"SELECT rsid, chromosome, position, genotype, is_rsid, source, r2_quality FROM snps {where} ORDER BY chromosome, position LIMIT ? OFFSET ?"
        async with self._conn.execute(data_sql, params + [limit, offset]) as cursor:
            rows = await cursor.fetchall()
            items = [dict(row) for row in rows]

        return {"items": items, "total": total, "page": page, "limit": limit}

    async def get_snp(self, rsid: str) -> dict | None:
        sql = "SELECT rsid, chromosome, position, genotype, is_rsid, source, r2_quality FROM snps WHERE rsid = ?"
        async with self._conn.execute(sql, [rsid]) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_stats(self) -> dict:
        stats = {}
        async with self._conn.execute("SELECT COUNT(*) FROM snps") as c:
            stats["total"] = (await c.fetchone())[0]
        async with self._conn.execute("SELECT COUNT(*) FROM snps WHERE source = 'genotyped'") as c:
            stats["genotyped"] = (await c.fetchone())[0]
        async with self._conn.execute("SELECT COUNT(*) FROM snps WHERE source = 'imputed'") as c:
            stats["imputed"] = (await c.fetchone())[0]
        async with self._conn.execute("SELECT COUNT(DISTINCT chromosome) FROM snps") as c:
            stats["chromosomes"] = (await c.fetchone())[0]
        return stats
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/backend/test_genome_db.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/genome.py tests/backend/ && git commit -m "feat: add GenomeDB async SQLite wrapper with query/filter/stats"
```

---

### Task 3: Database Layer — UsersDB

**Files:**
- Create: `backend/app/db/users.py`
- Create: `tests/backend/test_users_db.py`

- [ ] **Step 1: Write failing test**

Create `tests/backend/test_users_db.py`:

```python
import pytest
from backend.app.db.users import UsersDB


@pytest.fixture
async def users_db(tmp_path):
    db = UsersDB(tmp_path / "test_users.db")
    await db.connect()
    await db.init_schema()
    yield db
    await db.close()


@pytest.mark.asyncio
async def test_create_session(users_db):
    session = await users_db.create_session()
    assert "id" in session
    assert "created_at" in session


@pytest.mark.asyncio
async def test_get_session(users_db):
    created = await users_db.create_session()
    fetched = await users_db.get_session(created["id"])
    assert fetched is not None
    assert fetched["id"] == created["id"]


@pytest.mark.asyncio
async def test_save_and_get_messages(users_db):
    session = await users_db.create_session()
    sid = session["id"]
    await users_db.save_message(sid, "user", "hello")
    await users_db.save_message(sid, "assistant", "hi there")
    messages = await users_db.get_messages(sid)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_save_agent_history(users_db):
    session = await users_db.create_session()
    sid = session["id"]
    history = [{"role": "user", "content": "test"}]
    await users_db.save_agent_history(sid, history)
    fetched = await users_db.get_session(sid)
    assert fetched["agent_history"] == history


@pytest.mark.asyncio
async def test_create_import(users_db):
    session = await users_db.create_session()
    imp = await users_db.create_import(session["id"], "/tmp/test.txt", "23andme")
    assert imp["status"] == "pending"
    assert imp["provider"] == "23andme"


@pytest.mark.asyncio
async def test_update_import(users_db):
    session = await users_db.create_session()
    imp = await users_db.create_import(session["id"], "/tmp/test.txt", "23andme")
    await users_db.update_import(imp["id"], status="done", variant_count=960614)
    updated = await users_db.get_import(imp["id"])
    assert updated["status"] == "done"
    assert updated["variant_count"] == 960614
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/backend/test_users_db.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement UsersDB**

Create `backend/app/db/users.py`:

```python
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite


class UsersDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self):
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def init_schema(self):
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL,
                agent_history TEXT DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
            CREATE TABLE IF NOT EXISTS imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                provider TEXT NOT NULL,
                variant_count INTEGER,
                imported_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
        """)

    async def create_session(self) -> dict:
        sid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        await self._conn.execute(
            "INSERT INTO sessions (id, created_at, last_active) VALUES (?, ?, ?)",
            [sid, now, now],
        )
        await self._conn.commit()
        return {"id": sid, "created_at": now, "last_active": now, "agent_history": []}

    async def get_session(self, session_id: str) -> dict | None:
        async with self._conn.execute("SELECT * FROM sessions WHERE id = ?", [session_id]) as c:
            row = await c.fetchone()
            if not row:
                return None
            d = dict(row)
            d["agent_history"] = json.loads(d["agent_history"]) if d["agent_history"] else []
            return d

    async def save_agent_history(self, session_id: str, history: list):
        now = datetime.now(timezone.utc).isoformat()
        await self._conn.execute(
            "UPDATE sessions SET agent_history = ?, last_active = ? WHERE id = ?",
            [json.dumps(history), now, session_id],
        )
        await self._conn.commit()

    async def save_message(self, session_id: str, role: str, content: str):
        now = datetime.now(timezone.utc).isoformat()
        await self._conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            [session_id, role, content, now],
        )
        await self._conn.commit()

    async def get_messages(self, session_id: str) -> list[dict]:
        async with self._conn.execute(
            "SELECT role, content, timestamp FROM chat_messages WHERE session_id = ? ORDER BY id",
            [session_id],
        ) as c:
            return [dict(row) for row in await c.fetchall()]

    async def create_import(self, session_id: str, file_path: str, provider: str) -> dict:
        async with self._conn.execute(
            "INSERT INTO imports (session_id, file_path, provider) VALUES (?, ?, ?) RETURNING *",
            [session_id, file_path, provider],
        ) as c:
            row = await c.fetchone()
            await self._conn.commit()
            return dict(row)

    async def update_import(self, import_id: int, **kwargs):
        sets = []
        params = []
        for key, val in kwargs.items():
            sets.append(f"{key} = ?")
            params.append(val)
        params.append(import_id)
        await self._conn.execute(f"UPDATE imports SET {', '.join(sets)} WHERE id = ?", params)
        await self._conn.commit()

    async def get_import(self, import_id: int) -> dict | None:
        async with self._conn.execute("SELECT * FROM imports WHERE id = ?", [import_id]) as c:
            row = await c.fetchone()
            return dict(row) if row else None
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/backend/test_users_db.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/users.py tests/backend/test_users_db.py && git commit -m "feat: add UsersDB for sessions, chat messages, and imports"
```

---

### Task 4: SNP API Routes

**Files:**
- Create: `backend/app/routes/snps.py`
- Create: `tests/backend/test_snps_route.py`

- [ ] **Step 1: Write failing test**

Create `tests/backend/test_snps_route.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app, genome_db, users_db


@pytest.fixture(autouse=True)
async def setup_dbs(tmp_path):
    """Point app at temp databases with test data."""
    import aiosqlite

    # Create genome.db with test data
    gdb_path = tmp_path / "genome.db"
    async with aiosqlite.connect(gdb_path) as conn:
        await conn.execute("""
            CREATE TABLE snps (
                rsid TEXT PRIMARY KEY,
                chromosome TEXT NOT NULL,
                position INTEGER NOT NULL,
                genotype TEXT NOT NULL,
                is_rsid BOOLEAN NOT NULL DEFAULT 1,
                source TEXT DEFAULT 'genotyped',
                r2_quality REAL,
                imported_at TEXT DEFAULT (datetime('now'))
            )
        """)
        test_snps = [
            ("rs1065852", "22", 42526694, "CT", 1, "genotyped", None),
            ("rs4680", "22", 19951271, "GA", 1, "genotyped", None),
            ("rs1800497", "11", 113270828, "CT", 1, "genotyped", None),
        ]
        await conn.executemany(
            "INSERT INTO snps (rsid, chromosome, position, genotype, is_rsid, source, r2_quality) VALUES (?, ?, ?, ?, ?, ?, ?)",
            test_snps,
        )
        await conn.commit()

    genome_db.db_path = gdb_path
    await genome_db.connect()

    udb_path = tmp_path / "users.db"
    users_db.db_path = udb_path
    await users_db.connect()
    await users_db.init_schema()

    yield

    await genome_db.close()
    await users_db.close()


@pytest.mark.asyncio
async def test_list_snps():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/snps")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_snps_with_search():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/snps?search=rs4680")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["rsid"] == "rs4680"


@pytest.mark.asyncio
async def test_get_snp_detail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/snps/rs4680")
        assert resp.status_code == 200
        data = resp.json()
        assert data["rsid"] == "rs4680"
        assert data["genotype"] == "GA"


@pytest.mark.asyncio
async def test_get_snp_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/snps/rs0000000")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_stats():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/backend/test_snps_route.py -v
```

Expected: FAIL — route does not exist.

- [ ] **Step 3: Implement SNP routes**

Create `backend/app/routes/snps.py`:

```python
from fastapi import APIRouter, HTTPException, Query

from backend.app.main import genome_db

router = APIRouter(prefix="/api")


@router.get("/snps")
async def list_snps(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    search: str | None = None,
    chr: str | None = None,
    source: str | None = None,
):
    return await genome_db.query_snps(
        page=page, limit=limit, search=search, chromosome=chr, source=source
    )


@router.get("/snps/{rsid}")
async def get_snp(rsid: str):
    snp = await genome_db.get_snp(rsid)
    if not snp:
        raise HTTPException(status_code=404, detail="Variant not found")
    return snp


@router.get("/stats")
async def get_stats():
    return await genome_db.get_stats()
```

Add to `backend/app/main.py` after the health endpoint:

```python
from backend.app.routes.snps import router as snps_router
app.include_router(snps_router)
```

- [ ] **Step 4: Run tests**

```bash
pip install httpx  # needed for ASGI test client
pytest tests/backend/test_snps_route.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/snps.py backend/app/main.py tests/backend/test_snps_route.py && git commit -m "feat: add /api/snps and /api/stats REST endpoints"
```

---

### Task 5: Frontend Scaffold + Design System

**Files:**
- Create: `frontend/` (Vite + React + TypeScript scaffold)
- Create: `frontend/src/styles/theme.css`

- [ ] **Step 1: Scaffold Vite project**

```bash
cd /path/to/genome-toolkit
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install @tanstack/react-table @tanstack/react-virtual react-markdown cmdk
```

- [ ] **Step 2: Create design system CSS**

Create `frontend/src/styles/theme.css`:

```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&display=swap');

:root {
  /* Core palette */
  --bg: #e8e4dc;
  --bg-raised: #f0ece5;
  --bg-inset: #dedad2;

  --primary: #5b7ea1;
  --primary-dim: #8da4bc;
  --primary-strong: #3d6089;

  --accent: #c4724e;
  --accent-dim: #d4a08a;
  --accent-strong: #a8573a;

  --text: #3a3a38;
  --text-secondary: #7a7a76;
  --text-tertiary: #a0a09a;

  --border: #c4c0b8;
  --border-strong: #9a968e;
  --border-dashed: #b8b4ac;

  /* Significance colors */
  --sig-risk: #c4524e;
  --sig-benefit: #5a8a5e;
  --sig-reduced: #c49a4e;
  --sig-neutral: #7a7a76;
  --sig-unknown: #a0a09a;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;

  /* Typography */
  --font-mono: 'IBM Plex Mono', 'Menlo', monospace;
  --font-size-xs: 10px;
  --font-size-sm: 11px;
  --font-size-md: 13px;
  --font-size-lg: 16px;
  --font-size-xl: 20px;
  --font-size-2xl: 28px;

  --tracking-wide: 0.15em;
  --tracking-normal: 0.04em;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-mono);
  font-size: var(--font-size-md);
  font-weight: 400;
  letter-spacing: var(--tracking-normal);
  -webkit-font-smoothing: antialiased;
}

/* Instrument panel labels */
.label {
  font-size: var(--font-size-xs);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  color: var(--text-secondary);
}

.label--accent {
  color: var(--accent);
}

.label--primary {
  color: var(--primary);
}

/* Separator lines */
.separator {
  border: none;
  border-top: 1px solid var(--border);
  margin: var(--space-lg) 0;
}

.separator--dashed {
  border-top-style: dashed;
  border-color: var(--border-dashed);
}

/* Instrument panel buttons */
.btn {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border-strong);
  background: transparent;
  color: var(--text);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.btn:hover {
  background: var(--bg-inset);
  border-color: var(--primary);
  color: var(--primary);
}

.btn--active {
  background: var(--primary);
  color: var(--bg);
  border-color: var(--primary);
}

.btn--accent {
  border-color: var(--accent);
  color: var(--accent);
}

/* Input fields */
.input {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  letter-spacing: var(--tracking-normal);
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border);
  background: var(--bg-raised);
  color: var(--text);
  outline: none;
  width: 100%;
}

.input:focus {
  border-color: var(--primary);
}

.input::placeholder {
  color: var(--text-tertiary);
}

/* Significance badges */
.badge {
  font-size: var(--font-size-xs);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  padding: 2px 8px;
  border: 1px solid;
  display: inline-block;
}

.badge--risk { color: var(--sig-risk); border-color: var(--sig-risk); }
.badge--benefit { color: var(--sig-benefit); border-color: var(--sig-benefit); }
.badge--reduced { color: var(--sig-reduced); border-color: var(--sig-reduced); }
.badge--neutral { color: var(--sig-neutral); border-color: var(--sig-neutral); }

/* Scrollbar styling */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-inset); }
::-webkit-scrollbar-thumb { background: var(--border-strong); }
```

- [ ] **Step 3: Update App.tsx with shell layout**

Replace `frontend/src/App.tsx`:

```tsx
import './styles/theme.css'

function App() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top bar */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 'var(--space-md) var(--space-lg)',
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          <span style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, color: 'var(--accent)' }}>
            GENOME_TOOLKIT
          </span>
          <span className="label" style={{ color: 'var(--text-tertiary)' }}>
            STATUS: READY
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
          <button className="btn" style={{ fontSize: 'var(--font-size-xs)' }}>
            ASK_AI // CMD+K
          </button>
        </div>
      </header>

      {/* Main content */}
      <main style={{ flex: 1, padding: 'var(--space-lg)' }}>
        <p className="label label--primary">SNP_BROWSER // AWAITING_DATA</p>
      </main>

      {/* Status bar */}
      <footer style={{
        padding: 'var(--space-xs) var(--space-lg)',
        borderTop: '1px dashed var(--border-dashed)',
        display: 'flex',
        justifyContent: 'space-between',
      }}>
        <span className="label">SIGNAL_PHASE: IDLE</span>
        <span className="label">V0.1.0</span>
      </footer>
    </div>
  )
}

export default App
```

- [ ] **Step 4: Configure Vite proxy**

Replace `frontend/vite.config.ts`:

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 5: Verify frontend builds and renders**

```bash
cd /path/to/genome-toolkit/frontend
npm run build
npm run dev &
# Visit http://localhost:5173 — should show cream background, "GENOME_TOOLKIT" header with instrument panel typography
kill %1
```

- [ ] **Step 6: Commit**

```bash
cd /path/to/genome-toolkit
git add frontend/ && git commit -m "feat: scaffold frontend with retro instrument panel design system"
```

---

### Task 6: SNP Table Component

**Files:**
- Create: `frontend/src/hooks/useSNPs.ts`
- Create: `frontend/src/components/SNPTable.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create useSNPs hook**

Create `frontend/src/hooks/useSNPs.ts`:

```ts
import { useState, useEffect, useCallback } from 'react'

export interface SNP {
  rsid: string
  chromosome: string
  position: number
  genotype: string
  is_rsid: boolean
  source: string
  r2_quality: number | null
}

export interface SNPFilters {
  search: string
  chromosome: string
  source: string
  page: number
  limit: number
}

export interface SNPResult {
  items: SNP[]
  total: number
  page: number
  limit: number
}

const DEFAULT_FILTERS: SNPFilters = {
  search: '',
  chromosome: '',
  source: '',
  page: 1,
  limit: 100,
}

export function useSNPs() {
  const [filters, setFilters] = useState<SNPFilters>(DEFAULT_FILTERS)
  const [result, setResult] = useState<SNPResult>({ items: [], total: 0, page: 1, limit: 100 })
  const [loading, setLoading] = useState(false)

  const fetchSNPs = useCallback(async (f: SNPFilters) => {
    setLoading(true)
    const params = new URLSearchParams()
    params.set('page', String(f.page))
    params.set('limit', String(f.limit))
    if (f.search) params.set('search', f.search)
    if (f.chromosome) params.set('chr', f.chromosome)
    if (f.source) params.set('source', f.source)

    try {
      const resp = await fetch(`/api/snps?${params}`)
      if (resp.ok) {
        const data = await resp.json()
        setResult(data)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSNPs(filters)
  }, [filters, fetchSNPs])

  const updateFilters = useCallback((partial: Partial<SNPFilters>) => {
    setFilters(prev => ({ ...prev, page: 1, ...partial }))
  }, [])

  const setPage = useCallback((page: number) => {
    setFilters(prev => ({ ...prev, page }))
  }, [])

  return { result, filters, loading, updateFilters, setPage, refetch: () => fetchSNPs(filters) }
}
```

- [ ] **Step 2: Create SNPTable component**

Create `frontend/src/components/SNPTable.tsx`:

```tsx
import { useMemo } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
  type ColumnDef,
} from '@tanstack/react-table'
import type { SNP, SNPResult } from '../hooks/useSNPs'

const col = createColumnHelper<SNP>()

function SignificanceBadge({ source }: { source: string }) {
  // Placeholder — will be enriched with clinical_annotations later
  if (source === 'imputed') {
    return <span className="badge badge--neutral">IMPUTED</span>
  }
  return <span className="badge badge--neutral">--</span>
}

const columns: ColumnDef<SNP, any>[] = [
  col.accessor('rsid', {
    header: 'RSID',
    cell: info => (
      <span style={{ color: 'var(--primary)', cursor: 'pointer' }}>
        {info.getValue()}
      </span>
    ),
  }),
  col.accessor('chromosome', { header: 'CHR' }),
  col.accessor('position', {
    header: 'POSITION',
    cell: info => info.getValue().toLocaleString(),
  }),
  col.accessor('genotype', {
    header: 'GENOTYPE',
    cell: info => (
      <span style={{ fontWeight: 500 }}>{info.getValue()}</span>
    ),
  }),
  col.accessor('source', {
    header: 'SOURCE',
    cell: info => <SignificanceBadge source={info.getValue()} />,
  }),
]

interface Props {
  data: SNPResult
  loading: boolean
  onRowClick?: (snp: SNP) => void
  onPageChange?: (page: number) => void
}

export function SNPTable({ data, loading, onRowClick, onPageChange }: Props) {
  const table = useReactTable({
    data: data.items,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount: Math.ceil(data.total / data.limit),
  })

  const totalPages = Math.ceil(data.total / data.limit)

  return (
    <div>
      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(header => (
                  <th
                    key={header.id}
                    className="label"
                    style={{
                      textAlign: 'left',
                      padding: 'var(--space-sm) var(--space-md)',
                      borderBottom: '1px solid var(--border-strong)',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length} style={{ padding: 'var(--space-xl)', textAlign: 'center' }}>
                  <span className="label">LOADING // SCANNING_VARIANTS...</span>
                </td>
              </tr>
            ) : data.items.length === 0 ? (
              <tr>
                <td colSpan={columns.length} style={{ padding: 'var(--space-xl)', textAlign: 'center' }}>
                  <span className="label">NO_SIGNAL // NO_VARIANTS_FOUND</span>
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row, i) => (
                <tr
                  key={row.id}
                  onClick={() => onRowClick?.(row.original)}
                  style={{
                    cursor: onRowClick ? 'pointer' : 'default',
                    background: i % 2 === 0 ? 'transparent' : 'var(--bg-raised)',
                    borderBottom: '1px solid var(--border)',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-inset)')}
                  onMouseLeave={e => (e.currentTarget.style.background = i % 2 === 0 ? 'transparent' : 'var(--bg-raised)')}
                >
                  {row.getVisibleCells().map(cell => (
                    <td
                      key={cell.id}
                      style={{
                        padding: 'var(--space-sm) var(--space-md)',
                        fontSize: 'var(--font-size-sm)',
                      }}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 'var(--space-md)',
        borderTop: '1px dashed var(--border-dashed)',
      }}>
        <span className="label">
          SHOWING {((data.page - 1) * data.limit) + 1}--
          {Math.min(data.page * data.limit, data.total)} OF {data.total.toLocaleString()} VARIANTS
        </span>
        <div style={{ display: 'flex', gap: 'var(--space-xs)' }}>
          <button
            className="btn"
            disabled={data.page <= 1}
            onClick={() => onPageChange?.(data.page - 1)}
          >
            PREV
          </button>
          <span className="label" style={{ padding: 'var(--space-sm)', lineHeight: '24px' }}>
            {data.page} // {totalPages.toLocaleString()}
          </span>
          <button
            className="btn"
            disabled={data.page >= totalPages}
            onClick={() => onPageChange?.(data.page + 1)}
          >
            NEXT
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Wire up App.tsx**

Update `frontend/src/App.tsx` to use the table:

```tsx
import './styles/theme.css'
import { useSNPs } from './hooks/useSNPs'
import { SNPTable } from './components/SNPTable'

function App() {
  const { result, filters, loading, updateFilters, setPage } = useSNPs()

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top bar */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 'var(--space-md) var(--space-lg)',
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
          <span style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, color: 'var(--accent)' }}>
            GENOME_TOOLKIT
          </span>
          <span className="label" style={{ color: 'var(--text-tertiary)' }}>
            {result.total > 0
              ? `${result.total.toLocaleString()} VARIANTS_LOADED`
              : 'AWAITING_DATA'}
          </span>
        </div>
        <button className="btn" style={{ fontSize: 'var(--font-size-xs)' }}>
          ASK_AI // CMD+K
        </button>
      </header>

      {/* Filter bar */}
      <div style={{
        display: 'flex',
        gap: 'var(--space-sm)',
        padding: 'var(--space-sm) var(--space-lg)',
        borderBottom: '1px dashed var(--border-dashed)',
        alignItems: 'center',
      }}>
        <input
          className="input"
          placeholder="SEARCH // RSID, GENE, POSITION..."
          style={{ maxWidth: 400 }}
          value={filters.search}
          onChange={e => updateFilters({ search: e.target.value })}
        />
        <select
          className="input"
          style={{ maxWidth: 160 }}
          value={filters.chromosome}
          onChange={e => updateFilters({ chromosome: e.target.value })}
        >
          <option value="">ALL_CHR</option>
          {Array.from({ length: 22 }, (_, i) => i + 1).map(n => (
            <option key={n} value={String(n)}>CHR_{n}</option>
          ))}
          <option value="X">CHR_X</option>
          <option value="Y">CHR_Y</option>
          <option value="MT">CHR_MT</option>
        </select>
        <select
          className="input"
          style={{ maxWidth: 160 }}
          value={filters.source}
          onChange={e => updateFilters({ source: e.target.value })}
        >
          <option value="">ALL_SOURCES</option>
          <option value="genotyped">GENOTYPED</option>
          <option value="imputed">IMPUTED</option>
        </select>
      </div>

      {/* Table */}
      <main style={{ flex: 1 }}>
        <SNPTable
          data={result}
          loading={loading}
          onPageChange={setPage}
        />
      </main>

      {/* Status bar */}
      <footer style={{
        padding: 'var(--space-xs) var(--space-lg)',
        borderTop: '1px dashed var(--border-dashed)',
        display: 'flex',
        justifyContent: 'space-between',
      }}>
        <span className="label">SIGNAL_PHASE: {loading ? 'SCANNING' : 'IDLE'}</span>
        <span className="label">V0.1.0</span>
      </footer>
    </div>
  )
}

export default App
```

- [ ] **Step 4: Delete unused default files**

```bash
rm frontend/src/App.css frontend/src/index.css frontend/src/assets/react.svg 2>/dev/null
```

Update `frontend/src/main.tsx` — remove `import './index.css'` if present.

- [ ] **Step 5: Build and verify**

```bash
cd /path/to/genome-toolkit/frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 6: Commit**

```bash
cd /path/to/genome-toolkit
git add frontend/src/ && git commit -m "feat: add SNP table with filters, pagination, instrument panel design"
```

---

### Task 7: Chat Backend — Anthropic API with Tools

**Files:**
- Create: `backend/app/agent/tools.py`
- Create: `backend/app/agent/agent.py`
- Create: `tests/backend/test_agent_tools.py`

- [ ] **Step 1: Write failing test for tools**

Create `tests/backend/test_agent_tools.py`:

```python
import pytest
from unittest.mock import AsyncMock
from backend.app.agent.tools import TOOL_DEFINITIONS, execute_tool


@pytest.mark.asyncio
async def test_tool_definitions_are_valid():
    """All tool definitions have required fields."""
    for tool in TOOL_DEFINITIONS:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool


@pytest.mark.asyncio
async def test_execute_query_snps():
    mock_db = AsyncMock()
    mock_db.query_snps.return_value = {
        "items": [{"rsid": "rs4680", "genotype": "GA"}],
        "total": 1,
        "page": 1,
        "limit": 50,
    }
    result = await execute_tool("query_snps", {"search": "rs4680"}, genome_db=mock_db)
    assert "rs4680" in result
    mock_db.query_snps.assert_called_once()


@pytest.mark.asyncio
async def test_execute_get_stats():
    mock_db = AsyncMock()
    mock_db.get_stats.return_value = {"total": 3405188, "genotyped": 601845, "imputed": 2803343}
    result = await execute_tool("get_stats", {}, genome_db=mock_db)
    assert "3,405,188" in result or "3405188" in result


@pytest.mark.asyncio
async def test_execute_unknown_tool():
    result = await execute_tool("nonexistent", {})
    assert "unknown" in result.lower() or "error" in result.lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/backend/test_agent_tools.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement tool definitions and executor**

Create `backend/app/agent/tools.py`:

```python
import json

TOOL_DEFINITIONS = [
    {
        "name": "query_snps",
        "description": "Search and filter the user's genetic variants. Returns matching SNPs with rsID, chromosome, position, genotype, and source. Use this when the user asks about specific variants, genes, chromosomes, or wants to explore their data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Search by rsID or gene name (e.g. 'rs4680', 'CYP2D6')",
                },
                "chromosome": {
                    "type": "string",
                    "description": "Filter by chromosome (e.g. '1', '22', 'X', 'MT')",
                },
                "source": {
                    "type": "string",
                    "enum": ["genotyped", "imputed"],
                    "description": "Filter by data source",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 20)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_snp_detail",
        "description": "Get full details for a specific variant by rsID. Use when the user asks about a specific SNP like 'what is rs1800497'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "rsid": {
                    "type": "string",
                    "description": "The rsID to look up (e.g. 'rs4680')",
                },
            },
            "required": ["rsid"],
        },
    },
    {
        "name": "get_stats",
        "description": "Get summary statistics about the user's loaded genetic data: total variants, genotyped count, imputed count, chromosomes covered.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "update_table_view",
        "description": "Update the SNP browser table in the user's UI. Use this to filter, search, or highlight specific variants in response to the user's questions. The frontend will apply these filters to the visible table.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Set the search field",
                },
                "chromosome": {
                    "type": "string",
                    "description": "Set chromosome filter",
                },
                "source": {
                    "type": "string",
                    "description": "Set source filter",
                },
                "highlight_rsid": {
                    "type": "string",
                    "description": "Highlight a specific rsID in the table",
                },
            },
            "required": [],
        },
    },
]


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    genome_db=None,
    users_db=None,
) -> str:
    if tool_name == "query_snps":
        result = await genome_db.query_snps(
            search=tool_input.get("search"),
            chromosome=tool_input.get("chromosome"),
            source=tool_input.get("source"),
            limit=tool_input.get("limit", 20),
        )
        items = result["items"]
        if not items:
            return "No variants found matching your query."
        lines = [f"Found {result['total']} variants. Showing first {len(items)}:\n"]
        for snp in items:
            lines.append(
                f"- {snp['rsid']}: chr{snp['chromosome']}:{snp['position']} "
                f"genotype={snp['genotype']} source={snp['source']}"
            )
        return "\n".join(lines)

    elif tool_name == "get_snp_detail":
        snp = await genome_db.get_snp(tool_input["rsid"])
        if not snp:
            return f"Variant {tool_input['rsid']} not found in your data."
        return json.dumps(snp, indent=2)

    elif tool_name == "get_stats":
        stats = await genome_db.get_stats()
        return (
            f"Your genome data:\n"
            f"- Total variants: {stats['total']:,}\n"
            f"- Genotyped: {stats['genotyped']:,}\n"
            f"- Imputed: {stats['imputed']:,}\n"
            f"- Chromosomes: {stats['chromosomes']}"
        )

    elif tool_name == "update_table_view":
        # This tool's result is intercepted by the SSE handler to emit ui_action events.
        # The text result goes to Claude's context.
        return f"Table view updated with filters: {json.dumps(tool_input)}"

    else:
        return f"Error: unknown tool '{tool_name}'"
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/backend/test_agent_tools.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Implement agent runner**

Create `backend/app/agent/agent.py`:

```python
import anthropic
from typing import AsyncIterator

from backend.app.agent.tools import TOOL_DEFINITIONS, execute_tool

SYSTEM_PROMPT = """You are a genome data assistant for a personal genomics toolkit. You help users understand their genetic variants (SNPs), explain clinical significance, and navigate their data.

You have access to the user's genetic data stored in a SQLite database. Use the provided tools to query their variants and update the UI table.

Guidelines:
- Be concise and scientifically accurate
- When discussing variants, always mention the rsID, genotype, and what it means
- Use the update_table_view tool to filter the UI table when showing specific variants
- If asked about a gene, search for variants in that gene
- Explain significance in plain language: what the variant does, not just that it exists
- Note when data is imputed (lower confidence) vs genotyped (directly measured)"""


async def run_agent_turn(
    messages: list[dict],
    genome_db,
    users_db=None,
) -> AsyncIterator[dict]:
    """Run one agent turn. Yields SSE-compatible event dicts."""
    client = anthropic.AsyncAnthropic()

    while True:
        stream = client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
            thinking={"type": "adaptive"},
        )

        full_response = None
        async with stream as s:
            async for event in s:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield {"event": "text_delta", "data": {"content": event.delta.text}}
                    elif event.delta.type == "thinking_delta":
                        pass  # Don't stream thinking to user

            full_response = await s.get_final_message()

        # Append assistant response to messages
        messages.append({"role": "assistant", "content": full_response.content})

        # If no tool calls, we're done
        if full_response.stop_reason != "tool_use":
            break

        # Execute tool calls
        tool_results = []
        for block in full_response.content:
            if block.type == "tool_use":
                yield {
                    "event": "tool_call",
                    "data": {"tool": block.name, "args": block.input},
                }

                result_text = await execute_tool(
                    block.name, block.input, genome_db=genome_db, users_db=users_db
                )

                yield {
                    "event": "tool_result",
                    "data": {"tool": block.name, "result": result_text[:500]},
                }

                # Emit ui_action for update_table_view
                if block.name == "update_table_view":
                    yield {
                        "event": "ui_action",
                        "data": {"action": "filter_table", "params": block.input},
                    }

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                })

        messages.append({"role": "user", "content": tool_results})

    yield {"event": "done", "data": {}}
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/agent/ tests/backend/test_agent_tools.py && git commit -m "feat: add agent tools and Anthropic API runner with SSE event streaming"
```

---

### Task 8: Chat SSE Endpoint

**Files:**
- Create: `backend/app/routes/chat.py`
- Create: `backend/app/routes/sessions.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Implement session routes**

Create `backend/app/routes/sessions.py`:

```python
from fastapi import APIRouter, HTTPException

from backend.app.main import users_db

router = APIRouter(prefix="/api")


@router.post("/sessions")
async def create_session():
    return await users_db.create_session()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = await users_db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await users_db.get_messages(session_id)
    return {**session, "messages": messages}
```

- [ ] **Step 2: Implement chat SSE route**

Create `backend/app/routes/chat.py`:

```python
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.app.main import genome_db, users_db
from backend.app.agent.agent import run_agent_turn

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/chat")
async def chat(req: ChatRequest):
    session = await users_db.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    await users_db.save_message(req.session_id, "user", req.message)

    # Build messages from history
    api_messages = []
    for msg in session.get("agent_history", []):
        api_messages.append(msg)

    api_messages.append({"role": "user", "content": req.message})

    async def event_stream():
        assistant_text_parts = []
        try:
            async for event in run_agent_turn(api_messages, genome_db=genome_db, users_db=users_db):
                if event["event"] == "text_delta":
                    assistant_text_parts.append(event["data"]["content"])
                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"]),
                }
        finally:
            # Save assistant response
            full_text = "".join(assistant_text_parts)
            if full_text:
                await users_db.save_message(req.session_id, "assistant", full_text)
            # Save conversation history for context
            await users_db.save_agent_history(req.session_id, api_messages)

    return EventSourceResponse(event_stream())
```

- [ ] **Step 3: Register routes in main.py**

Add to `backend/app/main.py` after the snps router include:

```python
from backend.app.routes.sessions import router as sessions_router
from backend.app.routes.chat import router as chat_router

app.include_router(sessions_router)
app.include_router(chat_router)
```

- [ ] **Step 4: Test manually**

```bash
cd /path/to/genome-toolkit
GENOME_DB_PATH=~/genome-vault/data/genome.db uvicorn backend.app.main:app --reload --port 8000 &

# Create session
curl -X POST http://localhost:8000/api/sessions

# Test chat (use session ID from above)
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<SESSION_ID>", "message": "How many variants do I have?"}'

kill %1
```

Expected: SSE stream with text_delta events, tool calls, and a done event.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routes/ backend/app/main.py && git commit -m "feat: add /api/chat SSE endpoint and /api/sessions routes"
```

---

### Task 9: Command Palette (Cmd+K)

**Files:**
- Create: `frontend/src/hooks/useChat.ts`
- Create: `frontend/src/components/CommandPalette.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create SSE client library**

Create `frontend/src/lib/sse.ts`:

```ts
export interface SSEEvent {
  event: string
  data: any
}

export async function* streamChat(
  sessionId: string,
  message: string,
  signal?: AbortSignal,
): AsyncGenerator<SSEEvent> {
  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
    signal,
  })

  if (!resp.ok) throw new Error(`Chat failed: ${resp.status}`)
  if (!resp.body) throw new Error('No response body')

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    let currentEvent = ''
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7)
      } else if (line.startsWith('data: ') && currentEvent) {
        try {
          const data = JSON.parse(line.slice(6))
          yield { event: currentEvent, data }
        } catch {
          // skip malformed data
        }
        currentEvent = ''
      }
    }
  }
}
```

- [ ] **Step 2: Create useChat hook**

Create `frontend/src/hooks/useChat.ts`:

```ts
import { useState, useCallback, useRef, useEffect } from 'react'
import { streamChat, type SSEEvent } from '../lib/sse'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface UIAction {
  action: string
  params: Record<string, string>
}

export function useChat(onUIAction?: (action: UIAction) => void) {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const [streamingText, setStreamingText] = useState('')
  const abortRef = useRef<AbortController | null>(null)

  // Create session on mount
  useEffect(() => {
    fetch('/api/sessions', { method: 'POST' })
      .then(r => r.json())
      .then(s => setSessionId(s.id))
  }, [])

  const send = useCallback(async (text: string) => {
    if (!sessionId || streaming) return

    setMessages(prev => [...prev, { role: 'user', content: text }])
    setStreaming(true)
    setStreamingText('')

    const abort = new AbortController()
    abortRef.current = abort

    let accumulated = ''
    try {
      for await (const event of streamChat(sessionId, text, abort.signal)) {
        if (event.event === 'text_delta') {
          accumulated += event.data.content
          setStreamingText(accumulated)
        } else if (event.event === 'ui_action' && onUIAction) {
          onUIAction(event.data)
        } else if (event.event === 'done') {
          break
        }
      }
    } catch (e) {
      if ((e as Error).name !== 'AbortError') {
        accumulated += '\n\n[Connection error]'
      }
    }

    if (accumulated) {
      setMessages(prev => [...prev, { role: 'assistant', content: accumulated }])
    }
    setStreamingText('')
    setStreaming(false)
  }, [sessionId, streaming, onUIAction])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { messages, streaming, streamingText, send, cancel, sessionId }
}
```

- [ ] **Step 3: Create CommandPalette component**

Create `frontend/src/components/CommandPalette.tsx`:

```tsx
import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import type { ChatMessage } from '../hooks/useChat'

interface Props {
  open: boolean
  onClose: () => void
  messages: ChatMessage[]
  streaming: boolean
  streamingText: string
  onSend: (text: string) => void
}

export function CommandPalette({ open, onClose, messages, streaming, streamingText, onSend }: Props) {
  const [input, setInput] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [messages, streamingText])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        if (open) onClose()
        else {
          // Will be handled by parent
        }
      }
      if (e.key === 'Escape' && open) {
        onClose()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || streaming) return
    onSend(input.trim())
    setInput('')
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(58, 58, 56, 0.3)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '15vh',
        zIndex: 1000,
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div style={{
        width: '100%',
        maxWidth: 640,
        background: 'var(--bg-raised)',
        border: '1px solid var(--primary)',
        maxHeight: '60vh',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Messages area */}
        {messages.length > 0 && (
          <div
            ref={scrollRef}
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: 'var(--space-md)',
              maxHeight: '40vh',
              borderBottom: '1px dashed var(--border-dashed)',
            }}
          >
            {messages.map((msg, i) => (
              <div key={i} style={{ marginBottom: 'var(--space-md)' }}>
                <span className="label" style={{ color: msg.role === 'user' ? 'var(--accent)' : 'var(--primary)' }}>
                  {msg.role === 'user' ? 'YOU //' : 'AI //'}
                </span>
                <div style={{
                  marginTop: 'var(--space-xs)',
                  fontSize: 'var(--font-size-sm)',
                  lineHeight: 1.6,
                }}>
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))}
            {streaming && streamingText && (
              <div style={{ marginBottom: 'var(--space-md)' }}>
                <span className="label label--primary">AI //</span>
                <div style={{
                  marginTop: 'var(--space-xs)',
                  fontSize: 'var(--font-size-sm)',
                  lineHeight: 1.6,
                }}>
                  <ReactMarkdown>{streamingText}</ReactMarkdown>
                  <span style={{ animation: 'blink 1s infinite', color: 'var(--primary)' }}>_</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Input */}
        <form onSubmit={handleSubmit} style={{
          display: 'flex',
          alignItems: 'center',
          padding: 'var(--space-sm) var(--space-md)',
          gap: 'var(--space-sm)',
        }}>
          <span style={{ color: 'var(--primary)', fontWeight: 600 }}>&gt;</span>
          <input
            ref={inputRef}
            className="input"
            style={{
              border: 'none',
              background: 'transparent',
              flex: 1,
              fontSize: 'var(--font-size-md)',
            }}
            placeholder={messages.length === 0 ? "ASK_ABOUT_YOUR_GENOME..." : "FOLLOW_UP..."}
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={streaming}
          />
          <span className="label" style={{ whiteSpace: 'nowrap' }}>ESC // CLOSE</span>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Wire CommandPalette into App.tsx**

Update `frontend/src/App.tsx` — add to imports:

```tsx
import { useChat, type UIAction } from './hooks/useChat'
import { CommandPalette } from './components/CommandPalette'
import { useState, useEffect, useCallback } from 'react'
```

Add inside the `App` function, before the return:

```tsx
const [cmdkOpen, setCmdkOpen] = useState(false)

const handleUIAction = useCallback((action: UIAction) => {
  if (action.action === 'filter_table') {
    updateFilters({
      search: action.params.search || '',
      chromosome: action.params.chromosome || '',
      source: action.params.source || '',
    })
  }
}, [updateFilters])

const { messages, streaming, streamingText, send } = useChat(handleUIAction)

useEffect(() => {
  const handler = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      setCmdkOpen(prev => !prev)
    }
  }
  window.addEventListener('keydown', handler)
  return () => window.removeEventListener('keydown', handler)
}, [])
```

Update the ASK_AI button's onClick:

```tsx
<button className="btn" style={{ fontSize: 'var(--font-size-xs)' }} onClick={() => setCmdkOpen(true)}>
  ASK_AI // CMD+K
</button>
```

Add before closing `</div>` of App:

```tsx
<CommandPalette
  open={cmdkOpen}
  onClose={() => setCmdkOpen(false)}
  messages={messages}
  streaming={streaming}
  streamingText={streamingText}
  onSend={send}
/>
```

- [ ] **Step 5: Build and verify**

```bash
cd /path/to/genome-toolkit/frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 6: Commit**

```bash
cd /path/to/genome-toolkit
git add frontend/src/ && git commit -m "feat: add Cmd+K command palette with SSE streaming chat"
```

---

### Task 10: Import Pipeline Route

**Files:**
- Create: `backend/app/routes/import_.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Implement import route**

Create `backend/app/routes/import_.py`:

```python
import json
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.app.main import genome_db, users_db

# Add scripts/lib to path for provider imports
SCRIPTS_LIB = Path(__file__).resolve().parents[3] / "scripts" / "lib"
sys.path.insert(0, str(SCRIPTS_LIB))

from providers.base import detect_provider, read_header_lines

router = APIRouter(prefix="/api")


class ImportRequest(BaseModel):
    file_path: str
    session_id: str


@router.post("/import")
async def start_import(req: ImportRequest):
    file_path = Path(req.file_path).expanduser().resolve()
    if not file_path.exists():
        raise HTTPException(status_code=400, detail=f"File not found: {file_path}")

    # Detect provider
    try:
        provider_cls, confidence = detect_provider(file_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    header_lines = read_header_lines(file_path)
    provider = provider_cls()
    metadata = provider.metadata(file_path, header_lines)

    # Create import record
    imp = await users_db.create_import(req.session_id, str(file_path), metadata.provider)

    async def event_stream():
        yield {
            "event": "started",
            "data": json.dumps({
                "import_id": imp["id"],
                "provider": metadata.provider,
                "provider_version": metadata.provider_version,
                "assembly": metadata.assembly,
            }),
        }

        # Parse and insert
        records_iter, qc_stats = provider.parse(file_path)
        batch = []
        count = 0

        for record in records_iter:
            batch.append((
                record.source_id,
                record.chromosome,
                record.position,
                record.genotype,
                record.is_rsid,
                "genotyped",
                record.quality,
            ))
            count += 1

            if len(batch) >= 5000:
                await genome_db._conn.executemany(
                    "INSERT OR IGNORE INTO snps (rsid, chromosome, position, genotype, is_rsid, source, r2_quality) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    batch,
                )
                await genome_db._conn.commit()
                batch = []
                yield {
                    "event": "progress",
                    "data": json.dumps({"variants_processed": count}),
                }

        # Flush remaining
        if batch:
            await genome_db._conn.executemany(
                "INSERT OR IGNORE INTO snps (rsid, chromosome, position, genotype, is_rsid, source, r2_quality) VALUES (?, ?, ?, ?, ?, ?, ?)",
                batch,
            )
            await genome_db._conn.commit()

        # Update import record
        await users_db.update_import(imp["id"], status="done", variant_count=count)

        yield {
            "event": "done",
            "data": json.dumps({
                "import_id": imp["id"],
                "total_variants": count,
                "qc": {
                    "total_input": qc_stats.total_input,
                    "passed_qc": qc_stats.passed_qc,
                    "no_calls": qc_stats.no_calls,
                    "indels": qc_stats.indels,
                },
            }),
        }

    return EventSourceResponse(event_stream())
```

- [ ] **Step 2: Register in main.py**

Add to `backend/app/main.py`:

```python
from backend.app.routes.import_ import router as import_router
app.include_router(import_router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routes/import_.py backend/app/main.py && git commit -m "feat: add /api/import endpoint with SSE progress streaming"
```

---

### Task 11: Static File Serving + Setup Script

**Files:**
- Modify: `backend/app/main.py`
- Create: `scripts/setup.sh`
- Modify: `.gitignore`

- [ ] **Step 1: Add static file serving to main.py**

Add to `backend/app/main.py` at the end, after all route registrations:

```python
# Serve built frontend (must be last — catches all non-API routes)
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
```

- [ ] **Step 2: Create setup script**

Create `scripts/setup.sh`:

```bash
#!/bin/bash
set -e

echo "=== GENOME_TOOLKIT // SETUP ==="
echo ""

# Python deps
echo "[1/3] INSTALLING_PYTHON_DEPENDENCIES..."
pip install -r backend/requirements.txt
pip install -e .

# Frontend deps
echo "[2/3] INSTALLING_FRONTEND_DEPENDENCIES..."
cd frontend
npm install
npm run build
cd ..

# Data dir
echo "[3/3] INITIALIZING_DATA_DIRECTORY..."
mkdir -p data

echo ""
echo "=== SETUP_COMPLETE ==="
echo ""
echo "To start:"
echo "  export ANTHROPIC_API_KEY=sk-..."
echo "  export GENOME_DB_PATH=/path/to/genome.db  # optional, defaults to ./data/genome.db"
echo "  uvicorn backend.app.main:app --port 8000"
echo ""
echo "Then open http://localhost:8000"
```

```bash
chmod +x scripts/setup.sh
```

- [ ] **Step 3: Update .gitignore**

Append to `.gitignore`:

```
data/
frontend/node_modules/
frontend/dist/
.superpowers/
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py scripts/setup.sh .gitignore && git commit -m "feat: add static file serving and setup script"
```

---

### Task 12: End-to-End Integration Test

**Files:** None new — manual testing

- [ ] **Step 1: Build frontend**

```bash
cd /path/to/genome-toolkit/frontend && npm run build
```

- [ ] **Step 2: Start server against real genome.db**

```bash
cd /path/to/genome-toolkit
GENOME_DB_PATH=~/genome-vault/data/genome.db uvicorn backend.app.main:app --port 8000
```

- [ ] **Step 3: Verify in browser**

Open http://localhost:8000. Verify:
1. Table loads with SNP data from genome.db
2. Search and chromosome filters work
3. Pagination works
4. Cmd+K opens command palette
5. Chat sends message, streams response
6. Agent can query SNPs and update table filters

- [ ] **Step 4: Fix any issues found**

- [ ] **Step 5: Final commit**

```bash
git add -A && git commit -m "feat: genome toolkit web MVP — SNP browser with AI chat"
```

---

## Notes

**Architecture correction:** This plan uses the `anthropic` Python SDK with streaming tool use instead of Claude Agent SDK. The Agent SDK spawns a CLI subprocess and is designed for terminal agents — not suitable for a web server that needs to handle concurrent HTTP requests and stream SSE events. The Anthropic SDK's `messages.stream()` with tool definitions provides the same agent capabilities in a web-native way.

**Model choice:** Uses `claude-sonnet-4-6` for chat to keep costs manageable during development. Can be upgraded to `claude-opus-4-6` for production.

**Existing code reuse:** Parsers from `scripts/lib/providers/` are imported directly (Task 10). The existing `genome.db` schema is used as-is — no migrations needed for MVP.
