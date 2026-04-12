"""API route tests for GWAS, TTS, settings, and health endpoints.

Uses httpx.AsyncClient with ASGITransport to test FastAPI routes.
The real lifespan is replaced with a lightweight test lifespan that
creates a temporary genome.db, avoiding the need for real data files
or migration scripts.
"""
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# Helper: build a minimal genome DB on disk
# ---------------------------------------------------------------------------

async def _create_test_genome_db(db_path: Path):
    """Create a minimal genome.db with required tables and sample rows."""
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
        await conn.execute(
            "CREATE INDEX idx_snps_chr_pos ON snps(chromosome, position)"
        )
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS enrichments (
                rsid TEXT NOT NULL,
                source TEXT NOT NULL,
                data TEXT,
                PRIMARY KEY (rsid, source)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS gene_snp_map (
                rsid TEXT NOT NULL,
                gene_symbol TEXT NOT NULL,
                PRIMARY KEY (rsid, gene_symbol)
            )
        """)
        test_snps = [
            ("rs1065852", "22", 42526694, "CT", 1, "genotyped", None),
            ("rs4680", "22", 19951271, "GA", 1, "genotyped", None),
        ]
        await conn.executemany(
            "INSERT INTO snps (rsid, chromosome, position, genotype, is_rsid, source, r2_quality) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            test_snps,
        )
        await conn.commit()


# ---------------------------------------------------------------------------
# Fixture: patched FastAPI app with test lifespan
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(tmp_path):
    """Yield an httpx AsyncClient wired to the FastAPI app with a test DB."""
    db_path = tmp_path / "genome.db"
    users_db_path = tmp_path / "users.db"
    await _create_test_genome_db(db_path)

    from backend.app.db.genome import GenomeDB
    from backend.app.db.users import UsersDB
    import backend.app.main as main_mod

    test_genome_db = GenomeDB(db_path)
    test_users_db = UsersDB(users_db_path)

    # Connect the test databases before any requests
    await test_genome_db.connect()
    await test_users_db.connect()
    await test_users_db.init_schema()

    # Build a fresh FastAPI app with a no-op lifespan that reuses our
    # already-connected test DBs.  We re-include every router from main.
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    @asynccontextmanager
    async def noop_lifespan(app):
        yield

    test_app = FastAPI(lifespan=noop_lifespan)
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Save originals so routes that do `from backend.app.main import genome_db`
    # pick up the test instance.
    original_genome_db = main_mod.genome_db
    original_users_db = main_mod.users_db
    main_mod.genome_db = test_genome_db
    main_mod.users_db = test_users_db

    # Re-register all API routers on the test app
    from backend.app.routes.snps import router as snps_router
    from backend.app.routes.sessions import router as sessions_router
    from backend.app.routes.chat import router as chat_router
    from backend.app.routes.tts import router as tts_router
    from backend.app.routes.mental_health import router as mental_health_router
    from backend.app.routes.checklist import router as checklist_router
    from backend.app.routes.vault import router as vault_router
    from backend.app.routes.gwas_analytics import router as gwas_analytics_router
    from backend.app.routes.gwas import router as gwas_router
    from backend.app.routes.starter_prompts import router as starter_prompts_router

    test_app.include_router(snps_router)
    test_app.include_router(sessions_router)
    test_app.include_router(chat_router)
    test_app.include_router(tts_router)
    test_app.include_router(mental_health_router)
    test_app.include_router(checklist_router)
    test_app.include_router(vault_router)
    test_app.include_router(gwas_analytics_router)
    test_app.include_router(gwas_router)
    test_app.include_router(starter_prompts_router)

    # Re-register inline routes from main.py
    @test_app.get("/api/health")
    async def health():
        stats = await main_mod.genome_db.get_stats()
        return {"status": "ok", "variants": stats["total"]}

    @test_app.get("/api/settings/views")
    async def get_visible_views():
        settings = main_mod._load_user_settings()
        display = settings.get("display", {})
        configured = display.get("views", main_mod.ALL_VIEWS)
        if "snps" not in configured:
            configured = ["snps"] + configured
        return {"views": configured}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    main_mod.genome_db = original_genome_db
    main_mod.users_db = original_users_db
    await test_genome_db.close()
    await test_users_db.close()


# ===================================================================
# Health
# ===================================================================

@pytest.mark.asyncio
async def test_health_returns_ok(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "variants" in data
    assert isinstance(data["variants"], int)


# ===================================================================
# Settings / views
# ===================================================================

@pytest.mark.asyncio
async def test_settings_views_returns_list(client):
    resp = await client.get("/api/settings/views")
    assert resp.status_code == 200
    data = resp.json()
    assert "views" in data
    assert isinstance(data["views"], list)
    # snps is always included
    assert "snps" in data["views"]


# ===================================================================
# TTS providers
# ===================================================================

@pytest.mark.asyncio
async def test_tts_providers_returns_list(client):
    resp = await client.get("/api/tts/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert "active" in data
    assert "providers" in data
    assert isinstance(data["providers"], list)
    # browser provider is always present
    ids = [p["id"] for p in data["providers"]]
    assert "browser" in ids


# ===================================================================
# TTS voices
# ===================================================================

@pytest.mark.asyncio
async def test_tts_voices_returns_response(client):
    resp = await client.get("/api/tts/voices")
    assert resp.status_code == 200
    data = resp.json()
    assert "provider" in data
    assert "voices" in data
    assert isinstance(data["voices"], list)


# ===================================================================
# TTS POST — empty text
# ===================================================================

@pytest.mark.asyncio
async def test_tts_post_empty_text_returns_400(client):
    resp = await client.post("/api/tts", json={"text": ""})
    assert resp.status_code == 400
    assert "required" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tts_post_whitespace_only_returns_400(client):
    resp = await client.post("/api/tts", json={"text": "   "})
    assert resp.status_code == 400


# ===================================================================
# GWAS traits listing
# ===================================================================

@pytest.mark.asyncio
async def test_gwas_traits_returns_list(client):
    resp = await client.get("/api/gwas/traits")
    assert resp.status_code == 200
    data = resp.json()
    assert "traits" in data
    assert isinstance(data["traits"], list)


# ===================================================================
# GWAS overlap
# ===================================================================

@pytest.mark.asyncio
async def test_gwas_overlap_returns_structure(client):
    resp = await client.get("/api/gwas/overlap")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_pleiotropic" in data


# ===================================================================
# GWAS summary
# ===================================================================

@pytest.mark.asyncio
async def test_gwas_summary_returns_structure(client):
    resp = await client.get("/api/gwas/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "traits" in data
    assert "overall" in data


# ===================================================================
# GWAS gene-map
# ===================================================================

@pytest.mark.asyncio
async def test_gwas_gene_map_returns_structure(client):
    resp = await client.get("/api/gwas/gene-map")
    assert resp.status_code == 200
    data = resp.json()
    assert "genes" in data
    assert "total_genes_with_hits" in data


# ===================================================================
# GWAS per-trait — missing trait returns 404
# ===================================================================

@pytest.mark.asyncio
async def test_gwas_trait_not_found(client):
    resp = await client.get("/api/gwas/nonexistent-trait")
    assert resp.status_code == 404


# ===================================================================
# GWAS PRS — missing trait returns 404
# ===================================================================

@pytest.mark.asyncio
async def test_gwas_prs_not_found(client):
    resp = await client.get("/api/gwas/nonexistent-trait/prs")
    assert resp.status_code == 404


# ===================================================================
# GWAS risk-landscape-context
# ===================================================================

@pytest.mark.asyncio
async def test_gwas_risk_landscape_context(client):
    resp = await client.get("/api/gwas/risk-landscape-context")
    assert resp.status_code == 200
    data = resp.json()
    assert "causes" in data


# ===================================================================
# GWAS addiction-summary
# ===================================================================

@pytest.mark.asyncio
async def test_gwas_addiction_summary(client):
    resp = await client.get("/api/gwas/addiction-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "trait" in data
    assert data["trait"] == "substance-use"


# ===================================================================
# Unit test: _count_effect_alleles
# ===================================================================

def test_count_effect_alleles_basic():
    from backend.app.routes.gwas import _count_effect_alleles

    assert _count_effect_alleles("AG", "A") == 1
    assert _count_effect_alleles("AA", "A") == 2
    assert _count_effect_alleles("GG", "A") == 0
    assert _count_effect_alleles("A/G", "G") == 1
    assert _count_effect_alleles(None, "A") is None
    assert _count_effect_alleles("AG", None) is None
    assert _count_effect_alleles("", "A") is None
    assert _count_effect_alleles("AGT", "A") is None  # triploid / indel
    assert _count_effect_alleles("AG", "AT") is None  # multi-char effect allele
