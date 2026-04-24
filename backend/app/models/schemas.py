from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ReportInput(BaseModel):
    session_id: str = Field(..., description="Training session identifier (memory).")
    report_text: str = Field(..., description="Pasted Radio Medical Record text (or transcription).")
    locale: Literal["en-UK", "pt-PT"] = "en-UK"


class Deficiency(BaseModel):
    area: str
    issue: str
    severity: Literal["low", "medium", "high"]
    suggestion: str


class ReviewResult(BaseModel):
    extracted: dict[str, Any] = Field(default_factory=dict)
    deficiencies: list[Deficiency] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    completeness_score: int = Field(..., ge=0, le=100)


class ResponseResult(BaseModel):
    next_step_message: str
    rationale_bullets: list[str] = Field(default_factory=list)
    questions_for_participants: list[str] = Field(default_factory=list)


class PatientEvaluation(BaseModel):
    status: Literal["ok", "concerning", "critical", "unknown"]
    summary: str
    suspected_problems: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)


class AnalyzeResult(BaseModel):
    review: ReviewResult
    response: ResponseResult
    patient_evaluation: PatientEvaluation | None = None
