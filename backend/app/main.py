from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.reports import router as reports_router
from app.services.llm_orchestrator import evaluate_patient, generate_next_step, review_report
from app.services.rag import load_or_build_vectorstore
from app.settings import settings


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(reports_router, prefix=settings.api_prefix)

