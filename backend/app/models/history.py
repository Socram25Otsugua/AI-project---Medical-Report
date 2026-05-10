from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class HistoryItemIn(BaseModel):
    createdAt: int = Field(..., description="Unix ms timestamp")
    sourceLabel: str
    reportText: str
    result: dict[str, Any]
    mode: Literal["form", "text"] | None = None
    indicators: dict[str, Any] | None = None


class HistoryItemOut(HistoryItemIn):
    id: str

