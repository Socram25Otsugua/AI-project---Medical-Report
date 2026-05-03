from __future__ import annotations

from typing import Any, Dict

from langchain_core.tools import tool

from tools.rag import RagDeps, rag_search


def make_rag_lookup_tool(rag: RagDeps):
    @tool
    def rag_lookup(query: str) -> Dict[str, Any]:
        """RAG: search the local knowledge base and return source excerpts."""
        docs = rag_search(rag.vectorstore, query=query, k=4)
        return {
            "results": [
                {"source": d.metadata.get("source", "unknown"), "text": d.page_content[:2000]}
                for d in docs
            ]
        }

    return rag_lookup
