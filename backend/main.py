from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.services.conversation_state import clear_state
from app.services.llm_orchestrator import chat_doctor_turn, evaluate_patient, generate_next_step, review_report
from app.settings import settings
from app.models.schemas import AnalyzeResult, ChatTurnInput, ChatTurnResult, ReportInput, ResponseResult, ReviewResult
from tools.rag import RagDeps, load_or_build_vectorstore

from app.models.history import HistoryItemIn, HistoryItemOut
from app.services.mongo import clear_reports, create_report, delete_report, list_reports

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_rag_deps: RagDeps | None = None
logger = logging.getLogger(__name__)


def _get_rag() -> RagDeps:
    global _rag_deps
    if _rag_deps is None:
        _rag_deps = load_or_build_vectorstore()
    return _rag_deps


@app.get("/health")
def health():
    return {"ok": True}


@app.post(f"{settings.api_prefix}/reports/review", response_model=ReviewResult)
def review_endpoint(payload: ReportInput):
    rag = _get_rag()
    return review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)


@app.post(f"{settings.api_prefix}/reports/respond", response_model=ResponseResult)
def respond_endpoint(payload: ReportInput):
    rag = _get_rag()
    review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    return generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)


@app.post(f"{settings.api_prefix}/reports/analyze", response_model=AnalyzeResult)
def analyze_endpoint(payload: ReportInput):
    rag = _get_rag()
    review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    response = generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
    patient_evaluation = evaluate_patient(
        rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review
    )
    return {"review": review, "response": response, "patient_evaluation": patient_evaluation}


@app.post(f"{settings.api_prefix}/reports/analyze-agent", response_model=AnalyzeResult)
def analyze_with_agent_endpoint(payload: ReportInput):
    rag = _get_rag()
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


@app.post(f"{settings.api_prefix}/reports/chat-turn", response_model=ChatTurnResult)
def chat_turn_endpoint(payload: ChatTurnInput):
    rag = _get_rag()
    return chat_doctor_turn(
        rag=rag,
        session_id=payload.session_id,
        report_text=payload.report_text,
        user_message=payload.user_message,
    )


@app.post(f"{settings.api_prefix}/reports/finalize-summary", response_model=AnalyzeResult)
def finalize_summary_endpoint(payload: ReportInput):
    rag = _get_rag()
    review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    response = generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
    patient_evaluation = evaluate_patient(
        rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review
    )
    clear_state(payload.session_id)
    return {"review": review, "response": response, "patient_evaluation": patient_evaluation}


@app.get(f"{settings.api_prefix}/reports/history", response_model=list[HistoryItemOut])
def history_list_endpoint(limit: int = 50):
    return list_reports(limit=limit)


@app.post(f"{settings.api_prefix}/reports/history", response_model=HistoryItemOut)
def history_create_endpoint(payload: HistoryItemIn):
    doc = payload.model_dump()
    return create_report(doc)


@app.delete(f"{settings.api_prefix}/reports/history", response_model=dict)
def history_clear_endpoint():
    deleted = clear_reports()
    return {"deleted": deleted}


@app.delete(f"{settings.api_prefix}/reports/history/{{report_id}}", response_model=dict)
def history_delete_one_endpoint(report_id: str):
    ok = delete_report(report_id)
    return {"deleted": ok}
