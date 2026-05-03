from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.llm_orchestrator import evaluate_patient, generate_next_step, review_report
from app.settings import settings
from models.schemas import AnalyzeResult, ReportInput, ResponseResult, ReviewResult
from tools.rag import RagDeps, load_or_build_vectorstore

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_rag_deps: RagDeps | None = None


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
    from agents.report_agent import ReportAgent

    agent = ReportAgent(rag=_get_rag())
    return agent.analyze(session_id=payload.session_id, report_text=payload.report_text)
