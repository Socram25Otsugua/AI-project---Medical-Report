from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from app.models.schemas import AnalyzeResult, ChatTurnInput, ChatTurnResult, ReportInput, ResponseResult, ReviewResult
from app.routers.deps import get_rag
from app.services.chat import clear_state, run_chat_turn
from app.services.form_analysis import analyze_form
from app.services.summary import build_clinical_summary, generate_summary_actions


router = APIRouter(tags=["reports"])


@router.post("/reports/review", response_model=ReviewResult)
def review_endpoint(payload: ReportInput):
    rag = get_rag()
    return analyze_form(rag=rag, session_id=payload.session_id, report_text=payload.report_text)


@router.post("/reports/respond", response_model=ResponseResult)
def respond_endpoint(payload: ReportInput):
    rag = get_rag()
    review = analyze_form(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    return generate_summary_actions(
        rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review
    )


@router.post("/reports/analyze", response_model=AnalyzeResult)
def analyze_endpoint(payload: ReportInput):
    rag = get_rag()
    return build_clinical_summary(rag, payload.session_id, payload.report_text)


@router.post("/reports/chat-turn", response_model=ChatTurnResult)
def chat_turn_endpoint(payload: ChatTurnInput):
    rag = get_rag()
    return run_chat_turn(
        rag=rag,
        session_id=payload.session_id,
        report_text=payload.report_text,
        user_message=payload.user_message,
    )


@router.post("/reports/finalize-summary", response_model=AnalyzeResult)
def finalize_summary_endpoint(payload: ReportInput):
    rag = get_rag()
    result = build_clinical_summary(rag, payload.session_id, payload.report_text)
    clear_state(payload.session_id)
    return result
