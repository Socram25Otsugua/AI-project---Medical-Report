from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional

try:
    from bson import ObjectId
    from pymongo import MongoClient
    from pymongo.collection import Collection
except Exception:  # pragma: no cover - handled at runtime when dependency missing
    ObjectId = None  # type: ignore[assignment]
    MongoClient = None  # type: ignore[assignment]
    Collection = Any  # type: ignore[assignment]

from app.settings import settings


@lru_cache(maxsize=1)
def _client() -> Any:
    if MongoClient is None:
        raise RuntimeError("MongoDB support requires pymongo. Install backend requirements first.")
    return MongoClient(settings.mongo_uri)


def reports_collection() -> Collection:
    db = _client()[settings.mongo_db]
    return db[settings.mongo_collection_reports]


def _oid(s: str) -> ObjectId:
    if ObjectId is None:
        raise RuntimeError("MongoDB support requires pymongo. Install backend requirements first.")
    return ObjectId(s)


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d


def list_reports(*, limit: int = 50) -> List[Dict[str, Any]]:
    col = reports_collection()
    cur = col.find({}, sort=[("createdAt", -1)]).limit(limit)
    return [_serialize(x) for x in cur]


def create_report(doc: Dict[str, Any]) -> Dict[str, Any]:
    col = reports_collection()
    res = col.insert_one(doc)
    out = dict(doc)
    out["id"] = str(res.inserted_id)
    return out


def delete_report(report_id: str) -> bool:
    col = reports_collection()
    res = col.delete_one({"_id": _oid(report_id)})
    return res.deleted_count == 1


def clear_reports() -> int:
    col = reports_collection()
    res = col.delete_many({})
    return int(res.deleted_count or 0)

