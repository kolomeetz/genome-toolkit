"""Tests for PDF export route."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.app.routes.export import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_export_pdf_success(client):
    resp = await client.post("/api/export/pdf", json={
        "markdown": "# Test\n\nHello world.\n",
        "report_type": "pgx",
    })
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:5] == b"%PDF-"
    assert "genome-report-pgx" in resp.headers["content-disposition"]


@pytest.mark.asyncio
async def test_export_pdf_with_metadata(client):
    resp = await client.post("/api/export/pdf", json={
        "markdown": "# Test\n\nContent.\n",
        "report_type": "mental-health",
        "metadata": {"title": "Custom", "date": "2026-01-01"},
    })
    assert resp.status_code == 200
    assert resp.content[:5] == b"%PDF-"


@pytest.mark.asyncio
async def test_export_pdf_empty_markdown(client):
    resp = await client.post("/api/export/pdf", json={
        "markdown": "",
        "report_type": "pgx",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_export_pdf_invalid_type(client):
    resp = await client.post("/api/export/pdf", json={
        "markdown": "# Test\n",
        "report_type": "bogus",
    })
    assert resp.status_code == 400
