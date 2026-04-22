from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.rag import load_or_build_vectorstore
from app.schemas import AnalyzeResult, ReportInput, ResponseResult, ReviewResult
from app.settings import settings
from app.llm_orchestrator import generate_next_step, review_report


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.post(f"{settings.api_prefix}/reports/review", response_model=ReviewResult)
def review_endpoint(payload: ReportInput):
    rag = load_or_build_vectorstore()
    data = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    return data


@app.post(f"{settings.api_prefix}/reports/respond", response_model=ResponseResult)
def respond_endpoint(payload: ReportInput):
    rag = load_or_build_vectorstore()
    review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    data = generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
    return data


@app.post(f"{settings.api_prefix}/reports/analyze", response_model=AnalyzeResult)
def analyze_endpoint(payload: ReportInput):
    rag = load_or_build_vectorstore()
    review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    response = generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
    return {"review": review, "response": response}

