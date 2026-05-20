from app.prompts import PATIENT_EVAL_SYSTEM_PROMPT, RESPONSE_SYSTEM_PROMPT, REVIEW_SYSTEM_PROMPT


def test_review_prompt_includes_required_sections():
    assert "Output must be valid JSON" in REVIEW_SYSTEM_PROMPT
    assert "completeness_score" in REVIEW_SYSTEM_PROMPT
    assert "deficiencies" in REVIEW_SYSTEM_PROMPT
    assert "safety_flags" in REVIEW_SYSTEM_PROMPT


def test_response_prompt_mentions_abcde_and_questions():
    assert "ABCDE" in RESPONSE_SYSTEM_PROMPT
    assert "questions_for_participants" in RESPONSE_SYSTEM_PROMPT
    assert "next_step_message" in RESPONSE_SYSTEM_PROMPT


def test_patient_eval_prompt_has_status_schema():
    assert "status" in PATIENT_EVAL_SYSTEM_PROMPT
    assert "ok|concerning|critical|unknown" in PATIENT_EVAL_SYSTEM_PROMPT
    assert "red_flags" in PATIENT_EVAL_SYSTEM_PROMPT
