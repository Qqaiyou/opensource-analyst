"""对话 ReAct 图工厂 — 构建 LangGraph ReAct 循环。

图结构:
    call_model ⇄ tool_node → END

call_model:
    ReactAgent 调用 LLM（含 search_code + MCP bound tools）
    返回 AIMessage（含 tool_calls 或最终文本回复）

tool_node:
    执行实际的工具调用（search_code + MCP tools）
    返回 ToolMessage 追加到 messages

tools_condition:
    最后一条消息有 tool_calls → tool_node → call_model
    否则 → END
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.tools import StructuredTool
from langchain_core.messages import ToolMessage

from opensource_analyst.graph.conversation_state import ConversationState
from opensource_analyst.agents.react_agent import ReactAgent
from opensource_analyst.mcp.client import MCPClientManager
from opensource_analyst.rag.retriever import CodeRetriever
from opensource_analyst.vectorstore.chroma import VectorStore

logger = logging.getLogger(__name__)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(h)
logger.setLevel(logging.DEBUG)

_conversation_react_agent = ReactAgent()


def _build_search_code_tool(owner: str, repo: str) -> StructuredTool:
    """创建 search_code 工具，绑定到指定 repo 的向量存储."""

    collection = f"{owner}_{repo}"

    async def _search_code_impl(query: str) -> str:
        """搜索代码库中的相关代码片段。"""
        try:
            store = VectorStore(collection)
            retriever = CodeRetriever(store)
            results = retriever.search(query, k=5)
            if not results:
                return "（未找到相关代码片段。请先运行 /analyze 完成代码索引。）"

            parts: list[str] = []
            for i, r in enumerate(results, 1):
                source = r.get("metadata", {}).get("source", "unknown")
                content = r.get("content", "")
                score = r.get("score")
                score_str = f" [相似度: {score:.2f}]" if score else ""
                parts.append(f"🔹 片段 {i} — {source}{score_str}\n```\n{content}\n```")
            return "\n\n".join(parts)
        except Exception as e:
            return f"代码搜索失败: {e}"

    return StructuredTool.from_function(
        coroutine=_search_code_impl,
        name="search_code",
        description="搜索代码库中的相关代码片段。当需要查看具体实现、函数逻辑、代码示例时使用。",
    )


async def _call_model_node(state: ConversationState) -> dict[str, Any]:
    """调用 LLM（含 bound tools）。"""
    if state.get("error"):
        return {}

    mcp_tool_dicts = state.get("mcp_tools") or []
    search_tool = _build_search_code_tool(state["repo_owner"], state["repo_name"])
    all_tools: list = [search_tool] + _mcptools_from_dicts(mcp_tool_dicts)

    try:
        response = await _conversation_react_agent.react(state, all_tools)
        return {"messages": [response]}
    except Exception as e:
        logger.exception("call_model 失败")
        return {"error": str(e)}


async def _tool_node(state: ConversationState) -> dict[str, Any]:
    """执行工具调用，返回 ToolMessage 列表。"""
    messages = list(state.get("messages", []))
    last_msg = messages[-1] if messages else None

    if last_msg is None or not hasattr(last_msg, "tool_calls"):
        return {}

    tool_calls = getattr(last_msg, "tool_calls", None)
    if not tool_calls:
        return {}

    mcp_tool_dicts = state.get("mcp_tools") or []
    search_tool = _build_search_code_tool(state["repo_owner"], state["repo_name"])
    all_tools: dict[str, Any] = {"search_code": search_tool}
    for td in mcp_tool_dicts:
        all_tools[td["name"]] = _mcp_tool_from_dict(td)

    tool_results: list[ToolMessage] = []
    for tc in tool_calls:
        tool_name = tc.get("name", "")
        tool_args = tc.get("args", {})
        tool_call_id = tc.get("id", "")

        if tool_name in all_tools:
            try:
                func = all_tools[tool_name]
                result = await func.ainvoke(tool_args)
                content = str(result)
            except Exception as e:
                content = f"工具调用失败: {e}"
                logger.warning("工具 '%s' 失败: %s", tool_name, e)
        else:
            content = f"未知工具: {tool_name}"

        tool_results.append(ToolMessage(content=content, tool_call_id=tool_call_id, name=tool_name))

    return {"messages": tool_results}


def _tools_condition(state: ConversationState) -> str:
    """检查最后一条 AI 消息是否有 tool_calls。"""
    messages = state.get("messages", [])
    if not messages:
        return "__end__"

    last_msg = messages[-1]
    if hasattr(last_msg, "tool_calls") and getattr(last_msg, "tool_calls"):
        return "tools"
    return "__end__"


async def build_conversation_graph(
    mcp_manager: MCPClientManager | None = None,
) -> CompiledStateGraph:
    """构建并编译对话 ReAct 图。

    Args:
        mcp_manager: 外部 MCPClientManager，用于在 tool_node 中调用 MCP 工具。

    Returns:
        编译好的 CompiledStateGraph
    """
    graph = StateGraph(ConversationState)

    graph.add_node("call_model", _call_model_node)
    graph.add_node("tool_node", _tool_node)

    graph.set_entry_point("call_model")

    graph.add_conditional_edges(
        "call_model",
        _tools_condition,
        {"tools": "tool_node", "__end__": END},
    )
    graph.add_edge("tool_node", "call_model")

    return graph.compile()


def _mcptools_from_dicts(tool_dicts: list[dict]) -> list[StructuredTool]:
    """从序列化的 MCP 工具字典还原 tools。"""
    return [_mcp_tool_from_dict(td) for td in tool_dicts]


def _mcp_tool_from_dict(td: dict) -> StructuredTool:
    """从字典创建 MCP tool wrapper。工具由 API 层通过 _shared_mcp_manager 执行。"""
    name = td.get("name", "unknown")
    server_name = td.get("server_name", "")
    description = td.get("description", "")

    async def _mcp_call(arguments: str = "{}") -> str:
        try:
            args_dict = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError:
            args_dict = {}
        if _shared_mcp_manager is None:
            return "[MCP] MCP 管理器未初始化"
        # 从 tool name 反推原始 MCP tool name（去掉 mcp_{server}_ 前缀）
        orig_tool_name = name
        prefix = f"mcp_{server_name}_"
        if orig_tool_name.startswith(prefix):
            orig_tool_name = orig_tool_name[len(prefix):]
        result = await _shared_mcp_manager.call_tool(server_name, orig_tool_name, args_dict)
        if result.is_error:
            return f"[MCP Error] {result.content}"
        return json.dumps(result.content, ensure_ascii=False, indent=2)

    return StructuredTool.from_function(
        coroutine=_mcp_call,
        name=name,
        description=f"[MCP/{server_name}] {description}",
    )


# 模块级 MCP manager（由 API 层设置）
_shared_mcp_manager: MCPClientManager | None = None


def set_mcp_manager(manager: MCPClientManager | None) -> None:
    """设置模块级共享的 MCPClientManager（由 API 层调用）。"""
    global _shared_mcp_manager
    _shared_mcp_manager = manager
