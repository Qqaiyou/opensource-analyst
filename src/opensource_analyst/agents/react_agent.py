"""React Agent — 单个 ReAct Agent，绑定 search_code + MCP 工具.

负责在对话图中作为 call_model 节点的核心逻辑：
1. 接收 ConversationState（含 messages + 分析摘要）
2. 构造系统提示词
3. 调用 LLM（绑定 search_code + MCP tools）
4. 返回 AIMessage（含 tool_calls 或最终回复）
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from opensource_analyst.agents.base import BaseAgent
from opensource_analyst.prompts.conversation import CONVERSATION_SYSTEM_PROMPT
from opensource_analyst.rag.retriever import CodeRetriever
from opensource_analyst.vectorstore.chroma import VectorStore
from opensource_analyst.mcp.client import MCPClientManager
from opensource_analyst.graph.conversation_state import ConversationState

logger = logging.getLogger(__name__)


@tool
async def search_code(query: str) -> str:
    """搜索代码库中的相关代码片段。

    当需要查看具体实现、函数逻辑、代码示例时使用此工具。
    返回语义最相关的代码片段及其文件路径。

    Args:
        query: 搜索查询，描述要查找的代码内容
    """
    raise RuntimeError("search_code 工具未被正确初始化，请在 build_conversation_graph 中设置 tool context。")


class ReactAgent(BaseAgent):
    """ReAct 对话 Agent — LLM + 工具调用的单 Agent 循环.

    与分析管线中的 Agent 不同，ReactAgent 直接参与多轮对话，
    每次 call_model 都基于完整的 messages 历史 + 系统提示词。

    使用方式:
        agent = ReactAgent()
        # 在 conversation graph 的 call_model 节点中调用
        result = await agent.react(state)
    """

    def __init__(
        self,
        model: str = "deepseek-chat",
        temperature: float = 0.3,
    ) -> None:
        super().__init__(model=model, temperature=temperature)

    async def react(
        self,
        state: ConversationState,
        all_tools: list,
    ) -> Any:
        """ReAct 推理入口。

        在调用此方法前，graph 应已经保证：
        - state["messages"] 已包含历史对话（含最新的 HumanMessage）
        - state["analysis_summary"] 已加载分析结果

        Returns:
            AIMessage: LLM 返回的消息（可能含 tool_calls）
        """
        analysis_summary = state.get("analysis_summary") or "（分析报告未加载，请先运行 /analyze）"

        system_prompt = CONVERSATION_SYSTEM_PROMPT.format(
            repo_url=state["repo_url"],
            analysis_summary=analysis_summary,
        )

        llm_with_tools = self.bind_tools(all_tools)
        messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

        logger.info("ReAct 调用 — 消息数: %d (前3条: %s), 工具数: %d",
                     len(messages),
                     [(type(m).__name__, str(m.content)[:50]) for m in messages[:3]],
                     len(all_tools))

        return await llm_with_tools.ainvoke(messages)
