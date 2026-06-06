"""对话 Pydantic 模型."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ConversationStartRequest(BaseModel):
    task_id: str = Field(..., description="已完成分析任务的 ID")


class ConversationStartResponse(BaseModel):
    conversation_id: str
    repo_url: str
    task_id: str


class ConversationMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ReasoningStep(BaseModel):
    step_type: str  # "thought" | "tool_call" | "observation"
    content: str
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    timestamp: str


class ConversationMessageResponse(BaseModel):
    conversation_id: str
    user_message: str
    assistant_response: str
    reasoning_steps: list[ReasoningStep]
    timestamp: str


class HistoryMessage(BaseModel):
    role: str
    content: str
    reasoning_steps: list[ReasoningStep] | None = None
    timestamp: str


class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    repo_url: str
    messages: list[HistoryMessage]
    analysis_summary: dict[str, Any] | None = None
