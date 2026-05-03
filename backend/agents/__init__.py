from typing import Any


def __getattr__(name: str) -> Any:
    if name == "ReportAgent":
        from agents.report_agent import ReportAgent

        return ReportAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ReportAgent"]
