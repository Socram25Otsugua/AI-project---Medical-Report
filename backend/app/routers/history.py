from __future__ import annotations

from fastapi import APIRouter

from app.models.database import clear_reports, create_report, delete_report, list_reports
from app.models.schemas import HistoryItemIn, HistoryItemOut

router = APIRouter(tags=["history"])


@router.get("/reports/history", response_model=list[HistoryItemOut])
def history_list_endpoint(limit: int = 50):
    return list_reports(limit=limit)


@router.post("/reports/history", response_model=HistoryItemOut)
def history_create_endpoint(payload: HistoryItemIn):
    doc = payload.model_dump()
    return create_report(doc)


@router.delete("/reports/history", response_model=dict)
def history_clear_endpoint():
    deleted = clear_reports()
    return {"deleted": deleted}


@router.delete("/reports/history/{report_id}", response_model=dict)
def history_delete_one_endpoint(report_id: str):
    ok = delete_report(report_id)
    return {"deleted": ok}
