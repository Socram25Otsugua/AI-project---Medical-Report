from __future__ import annotations

from typing import Any, Dict

from app.services.form_analysis.form_review_chain import analyze_form
from app.services.summary.summary_actions_chain import generate_summary_actions
from app.services.summary.summary_patient_eval_chain import generate_patient_evaluation
from app.tools.rag import RagDeps


def build_clinical_summary(rag: RagDeps, session_id: str, report_text: str) -> Dict[str, Any]:
    """Run form review, summary actions, and patient evaluation for finalize-summary."""
    review = analyze_form(rag=rag, session_id=session_id, report_text=report_text)
    response = generate_summary_actions(
        rag=rag, session_id=session_id, report_text=report_text, review_json=review
    )
    patient_evaluation = generate_patient_evaluation(
        rag=rag, session_id=session_id, report_text=report_text, review_json=review
    )
    return {"review": review, "response": response, "patient_evaluation": patient_evaluation}
