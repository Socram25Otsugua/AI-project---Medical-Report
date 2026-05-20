from __future__ import annotations

import json
from typing import Dict

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from app.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_CHAT_TEMPERATURE
from app.prompts import CHAT_DOCTOR_SYSTEM_PROMPT


class ChatDoctorResult(BaseModel):
    assistant_message: str
    questions_for_participants: list[str] = Field(default_factory=list)
    answered_questions: list[str] = Field(default_factory=list)


_HISTORY_STORE: Dict[str, ChatMessageHistory] = {}
_WITH_HISTORY: RunnableWithMessageHistory | None = None


def _get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in _HISTORY_STORE:
        _HISTORY_STORE[session_id] = ChatMessageHistory()
    return _HISTORY_STORE[session_id]


def _get_chain() -> RunnableWithMessageHistory:
    global _WITH_HISTORY
    if _WITH_HISTORY is not None:
        return _WITH_HISTORY

    llm = ChatOllama(
        model=OLLAMA_CHAT_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=OLLAMA_CHAT_TEMPERATURE,
    )
    parser = JsonOutputParser(pydantic_object=ChatDoctorResult)
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=CHAT_DOCTOR_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{payload}\n\nReturn only JSON."),
        ]
    )
    chain = prompt | llm | parser
    _WITH_HISTORY = RunnableWithMessageHistory(
        chain,
        _get_session_history,
        input_messages_key="payload",
        history_messages_key="history",
    )
    return _WITH_HISTORY


def invoke_short_term_chat_turn(session_id: str, payload: dict) -> dict:
    chain = _get_chain()
    result = chain.invoke(
        {"payload": json.dumps(payload, ensure_ascii=False)},
        config={"configurable": {"session_id": session_id}},
    )
    return result if isinstance(result, dict) else dict(result)
