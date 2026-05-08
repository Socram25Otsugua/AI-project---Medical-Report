from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from tools.rag import load_or_build_vectorstore, rag_search


@dataclass(frozen=True)
class MedicalGuidelinesMCP:
    """
    MCP-style helper to retrieve maritime guidelines from local RAG store.
    """

    name: str = "medical_guidelines_mcp"
    description: str = "Retrieve relevant maritime medical guidelines for a clinical query."

    def retrieve(self, query: str, k: int = 3) -> Dict[str, Any]:
        try:
            rag = load_or_build_vectorstore()
            docs = rag_search(rag.vectorstore, query=query, k=k)
            results = [
                {
                    "content": d.page_content,
                    "source": d.metadata.get("source", "unknown"),
                }
                for d in docs
            ]
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "results": []}

    def get_context_string(self, query: str, k: int = 3) -> str:
        result = self.retrieve(query=query, k=k)
        if not result["success"] or not result["results"]:
            return "No specific guidelines found. Use standard ABCDE maritime medical protocols."
        return "\n\n".join([r["content"] for r in result["results"]])


medical_guidelines_mcp = MedicalGuidelinesMCP()
