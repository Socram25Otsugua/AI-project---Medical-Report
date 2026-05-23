from app.prompts import (
    FORM_REVIEW_SYSTEM_PROMPT,
    SUMMARY_ACTIONS_SYSTEM_PROMPT,
    SUMMARY_PATIENT_EVAL_SYSTEM_PROMPT,
)


def test_review_prompt_includes_required_sections():
    assert "Output must be valid JSON" in FORM_REVIEW_SYSTEM_PROMPT
    assert "completeness_score" in FORM_REVIEW_SYSTEM_PROMPT
    assert "deficiencies" in FORM_REVIEW_SYSTEM_PROMPT
    assert "safety_flags" in FORM_REVIEW_SYSTEM_PROMPT


def test_summary_actions_prompt_mentions_abcde_and_questions():
    assert "ABCDE" in SUMMARY_ACTIONS_SYSTEM_PROMPT
    assert "questions_for_participants" in SUMMARY_ACTIONS_SYSTEM_PROMPT
    assert "immediate_actions" in SUMMARY_ACTIONS_SYSTEM_PROMPT
    assert "monitoring_parameters" in SUMMARY_ACTIONS_SYSTEM_PROMPT
    assert "escalation_criteria" in SUMMARY_ACTIONS_SYSTEM_PROMPT


def test_summary_patient_eval_prompt_has_status_schema():
    assert "status" in SUMMARY_PATIENT_EVAL_SYSTEM_PROMPT
    assert "ok|concerning|critical|unknown" in SUMMARY_PATIENT_EVAL_SYSTEM_PROMPT
    assert "red_flags" in SUMMARY_PATIENT_EVAL_SYSTEM_PROMPT
