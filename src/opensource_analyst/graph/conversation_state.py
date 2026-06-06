"""对话图共享状态 — ReAct 循环专用.

与分析用的 GraphState 完全分离，通过 add_messages reducer 实现多轮消息累积.
"""

from typing import Any
from typing_extensions import NotRequired, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class ConversationState(TypedDict):
    conversation_id: str
    repo_url: str
    repo_owner: str
    repo_name: str

    # 对话消息（add_messages reducer 自动追加）
    messages: list[BaseMessage]  # add_messages() 在图中自动生效

    # 从分析任务加载的结果（文本摘要，直接注入系统提示词）
    analysis_summary: NotRequired[str | None]

    # 工具上下文
    rag_context: NotRequired[str | None]
    mcp_tools: NotRequired[list[dict[str, Any]] | None]

    # 流式控制
    stream_complete: NotRequired[bool]

    # 错误
    error: NotRequired[str | None]
