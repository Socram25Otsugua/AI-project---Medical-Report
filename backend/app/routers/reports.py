from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from app.models.schemas import AnalyzeResult, ChatTurnInput, ChatTurnResult, ReportInput, ResponseResult, ReviewResult
from app.routers.deps import get_rag
from app.services.chat_service import chat_doctor_turn
from app.services.conversation_state import clear_state
from app.services.patient_eval_chain import evaluate_patient
from app.services.response_chain import generate_next_step
from app.services.review_chain import review_report
from app.tools.rag import RagDeps


router = APIRouter(tags=["reports"])


def _run_full_analysis(rag: RagDeps, session_id: str, report_text: str) -> Dict[str, Any]:
    review = review_report(rag=rag, session_id=session_id, report_text=report_text)
    response = generate_next_step(
        rag=rag, session_id=session_id, report_text=report_text, review_json=review
    )
    patient_evaluation = evaluate_patient(
        rag=rag, session_id=session_id, report_text=report_text, review_json=review
    )
    return {"review": review, "response": response, "patient_evaluation": patient_evaluation}


@router.post("/reports/review", response_model=ReviewResult)
def review_endpoint(payload: ReportInput):
    rag = get_rag()
    return review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)


@router.post("/reports/respond", response_model=ResponseResult)
def respond_endpoint(payload: ReportInput):
    rag = get_rag()
    review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    return generate_next_step(
        rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review
    )


@router.post("/reports/analyze", response_model=AnalyzeResult)
def analyze_endpoint(payload: ReportInput):
    rag = get_rag()
    return _run_full_analysis(rag, payload.session_id, payload.report_text)


@router.post("/reports/chat-turn", response_model=ChatTurnResult)
def chat_turn_endpoint(payload: ChatTurnInput):
    rag = get_rag()
    return chat_doctor_turn(
        rag=rag,
        session_id=payload.session_id,
        report_text=payload.report_text,
        user_message=payload.user_message,
    )


@router.post("/reports/finalize-summary", response_model=AnalyzeResult)
def finalize_summary_endpoint(payload: ReportInput):
    rag = get_rag()
    result = _run_full_analysis(rag, payload.session_id, payload.report_text)
    clear_state(payload.session_id)
    return result
