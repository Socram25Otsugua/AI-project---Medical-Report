from __future__ import annotations

from fastapi import APIRouter

from models.schemas import AnalyzeResult, ReportInput, ResponseResult, ReviewResult
from tools.rag import load_or_build_vectorstore


router = APIRouter(tags=["reports"])


@router.post("/reports/review", response_model=ReviewResult)
def review_endpoint(payload: ReportInput):
    from main import review_report

    rag = load_or_build_vectorstore()
    data = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    return data


@router.post("/reports/respond", response_model=ResponseResult)
def respond_endpoint(payload: ReportInput):
    from main import generate_next_step, review_report

    rag = load_or_build_vectorstore()
    review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    data = generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
    return data


@router.post("/reports/analyze", response_model=AnalyzeResult)
def analyze_endpoint(payload: ReportInput):
    from main import evaluate_patient, generate_next_step, review_report

    rag = load_or_build_vectorstore()
    review = review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    response = generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
    patient_evaluation = evaluate_patient(
        rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review
    )
    return {"review": review, "response": response, "patient_evaluation": patient_evaluation}
