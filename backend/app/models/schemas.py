from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ReportInput(BaseModel):
    session_id: str = Field(..., description="Training session identifier (memory).")
    report_text: str = Field(..., description="Pasted Radio Medical Record text (or transcription).")
    locale: Literal["en-UK"] = "en-UK"


class ChatTurnInput(ReportInput):
    user_message: str = Field(default="", description="Optional user follow-up message for conversational turns.")


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
    vitals_score: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Coverage of key structured vitals extracted from the report (regex MCP).",
    )
    vitals_feedback: list[str] = Field(
        default_factory=list,
        description="Short explanation of which key vitals were captured and what is missing.",
    )


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


class ChatTurnResult(BaseModel):
    assistant_message: str
    questions_for_participants: list[str] = Field(default_factory=list)
    pending_questions: list[str] = Field(default_factory=list)
    can_finalize_summary: bool = False


class HistoryItemIn(BaseModel):
    createdAt: int = Field(..., description="Unix ms timestamp")
    sourceLabel: str
    reportText: str
    result: dict[str, Any]
    mode: Literal["form", "text"] | None = None
    indicators: dict[str, Any] | None = None


class HistoryItemOut(HistoryItemIn):
    id: str
