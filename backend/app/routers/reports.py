from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import AnalyzeResult, ReportInput, ResponseResult, ReviewResult


router = APIRouter(tags=["reports"])


@router.post("/reports/review", response_model=ReviewResult)
def review_endpoint(payload: ReportInput):
    from app import main as app_main

    rag = app_main.load_or_build_vectorstore()
    data = app_main.review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    return data


@router.post("/reports/respond", response_model=ResponseResult)
def respond_endpoint(payload: ReportInput):
    from app import main as app_main

    rag = app_main.load_or_build_vectorstore()
    review = app_main.review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    data = app_main.generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
    return data


@router.post("/reports/analyze", response_model=AnalyzeResult)
def analyze_endpoint(payload: ReportInput):
    from app import main as app_main

    rag = app_main.load_or_build_vectorstore()
    review = app_main.review_report(rag=rag, session_id=payload.session_id, report_text=payload.report_text)
    response = app_main.generate_next_step(rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review)
    patient_evaluation = app_main.evaluate_patient(
        rag=rag, session_id=payload.session_id, report_text=payload.report_text, review_json=review
    )
    return {"review": review, "response": response, "patient_evaluation": patient_evaluation}
