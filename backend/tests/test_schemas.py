import pytest
from pydantic import ValidationError

from app.schemas import AnalyzeResult, ReportInput, ReviewResult


def test_report_input_defaults_locale():
    payload = ReportInput(session_id="s1", report_text="example report")
    assert payload.locale == "en-UK"


def test_report_input_rejects_unknown_locale():
    with pytest.raises(ValidationError):
        ReportInput(session_id="s1", report_text="example report", locale="en-US")


def test_review_result_completeness_score_bounds():
    with pytest.raises(ValidationError):
        ReviewResult(completeness_score=101)

    valid = ReviewResult(completeness_score=80)
    assert valid.completeness_score == 80


def test_analyze_result_parses_nested_payload():
    result = AnalyzeResult(
        review={
            "extracted": {"patient": "X"},
            "deficiencies": [],
            "safety_flags": [],
            "completeness_score": 75,
            "vitals_score": 0,
        },
        response={
            "next_step_message": "Continue ABCDE.",
            "rationale_bullets": ["Structured approach."],
            "questions_for_participants": ["Any allergies?"],
        },
        patient_evaluation={
            "status": "unknown",
            "summary": "Insufficient data.",
            "suspected_problems": [],
            "red_flags": [],
        },
    )
    assert result.review.completeness_score == 75
    assert result.review.vitals_score == 0
    assert result.response.next_step_message.startswith("Continue")
    assert result.patient_evaluation is not None
    assert result.patient_evaluation.status == "unknown"
