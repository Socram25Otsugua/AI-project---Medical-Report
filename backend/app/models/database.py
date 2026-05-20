from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List


def _db_path() -> Path:
    backend_root = Path(__file__).resolve().parents[2]
    data_dir = backend_root / ".data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "history.sqlite3"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_schema() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                createdAt INTEGER NOT NULL,
                sourceLabel TEXT NOT NULL,
                reportText TEXT NOT NULL,
                result_json TEXT NOT NULL,
                mode TEXT,
                indicators_json TEXT
            )
            """
        )


_init_schema()


def _serialize_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": str(row["id"]),
        "createdAt": int(row["createdAt"]),
        "sourceLabel": str(row["sourceLabel"]),
        "reportText": str(row["reportText"]),
        "result": json.loads(str(row["result_json"])),
        "mode": row["mode"],
        "indicators": json.loads(str(row["indicators_json"])) if row["indicators_json"] else None,
    }


def list_reports(*, limit: int = 50) -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM reports ORDER BY createdAt DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    return [_serialize_row(r) for r in rows]


def create_report(doc: Dict[str, Any]) -> Dict[str, Any]:
    report_id = str(uuid.uuid4())
    result_json = json.dumps(doc.get("result", {}), ensure_ascii=False)
    indicators_json = None
    if doc.get("indicators") is not None:
        indicators_json = json.dumps(doc.get("indicators"), ensure_ascii=False)

    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO reports (id, createdAt, sourceLabel, reportText, result_json, mode, indicators_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                int(doc.get("createdAt", 0)),
                str(doc.get("sourceLabel", "")),
                str(doc.get("reportText", "")),
                result_json,
                doc.get("mode"),
                indicators_json,
            ),
        )

    out = dict(doc)
    out["id"] = report_id
    return out


def delete_report(report_id: str) -> bool:
    with _conn() as conn:
        res = conn.execute("DELETE FROM reports WHERE id = ?", (str(report_id),))
        return res.rowcount == 1


def clear_reports() -> int:
    with _conn() as conn:
        before = conn.execute("SELECT COUNT(*) AS c FROM reports").fetchone()
        conn.execute("DELETE FROM reports")
    return int(before["c"] if before else 0)
