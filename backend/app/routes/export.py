"""PDF export route."""
from datetime import date

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from backend.app.services.pdf_renderer import render_pdf


router = APIRouter()


class ExportRequest(BaseModel):
    markdown: str
    report_type: str
    metadata: dict | None = None


@router.post("/api/export/pdf")
async def export_pdf(req: ExportRequest):
    try:
        pdf_bytes = render_pdf(req.markdown, req.report_type, req.metadata)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    today = date.today().isoformat()
    filename = f"genome-report-{req.report_type}-{today}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
