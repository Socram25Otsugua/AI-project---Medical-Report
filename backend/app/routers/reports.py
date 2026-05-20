from __future__ import annotations

import logging

from fastapi import APIRouter

from pydantic import ValidationError

from app.models.schemas import AnalyzeResult, ChatTurnInput, ChatTurnResult, ReportInput, ResponseResult, ReviewResult
from app.routers.deps import get_rag
from app.services.chat_service import chat_doctor_turn
from app.services.conversation_state import clear_state
from app.services.patient_eval_chain import evaluate_patient
from app.services.response_chain import generate_next_step
from app.services.review_chain import review_report


router = APIRouter(tags=["reports"])
logger = logging.getLogger(__name__)


@router.post("/reports/review", response_model=ReviewResult)
def review_endpoint(payload: ReportInput):
    rag = get_rag()
    data = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    return data


@router.post("/reports/respond", response_model=ResponseResult)
def respond_endpoint(payload: ReportInput):
    rag = get_rag()
    review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    data = generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
    return data


@router.post("/reports/analyze", response_model=AnalyzeResult)
def analyze_endpoint(payload: ReportInput):
    rag = get_rag()
    review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    response = generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
    patient_evaluation = evaluate_patient(
        rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review
    )
    return {"review": review, "response": response, "patient_evaluation": patient_evaluation}


@router.post("/reports/analyze-agent", response_model=AnalyzeResult)
def analyze_with_agent_endpoint(payload: ReportInput):
    rag = get_rag()
    try:
        from agents.report_agent import ReportAgent

        agent = ReportAgent(rag=rag)
        candidate = agent.analyze(session_id=payload.session_id, report_text=payload.report_text)
    except Exception as exc:
        # Keep endpoint available even if optional agent stack is incompatible at runtime.
        logger.warning("analyze-agent fallback to orchestrator flow: %s", exc)
        review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
        response = generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
        patient_evaluation = evaluate_patient(
            rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review
        )
        return {"review": review, "response": response, "patient_evaluation": patient_evaluation}
    try:
        return AnalyzeResult.model_validate(candidate).model_dump()
    except ValidationError as exc:
        logger.warning("analyze-agent returned invalid schema, fallback to orchestrator flow: %s", exc)
        review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
        response = generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
        patient_evaluation = evaluate_patient(
            rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review
        )
        return {"review": review, "response": response, "patient_evaluation": patient_evaluation}


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
    review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    response = generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
    patient_evaluation = evaluate_patient(
        rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review
    )
    clear_state(payload.session_id)
    return {"review": review, "response": response, "patient_evaluation": patient_evaluation}
