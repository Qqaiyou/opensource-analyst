"""对话 API — 交互式 ReAct 对话端点.

端点:
    POST /conversation/start          — 基于已完成的 task_id 创建对话会话
    POST /conversation/{id}/message    — 发送消息，返回完整响应 + 推理步骤
    GET  /conversation/{id}/stream     — SSE 流式输出
    GET  /conversation/{id}/history    — 对话历史
    DELETE /conversation/{id}           — 结束对话
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from opensource_analyst.models.analysis import AnalysisResult
from opensource_analyst.models.conversation import (
    ConversationStartRequest,
    ConversationStartResponse,
    ConversationMessageRequest,
    ConversationMessageResponse,
    ConversationHistoryResponse,
    HistoryMessage,
    ReasoningStep,
)
from opensource_analyst.api.session import get_session_store, ConversationSessionStore
from opensource_analyst.api.analyze import _store as task_store  # 复用分析任务存储
from opensource_analyst.github.client import GitHubClient
from opensource_analyst.graph.conversation import build_conversation_graph, set_mcp_manager
from opensource_analyst.mcp.client import MCPClientManager
from opensource_analyst.mcp.tool_bridge import build_mcp_tools
from opensource_analyst.graph.conversation_state import ConversationState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversation", tags=["conversation"])

# 模块级 MCP manager（启动时由 main.py 设置）
_mcp_manager: MCPClientManager | None = None


def init_conversation_mcp(manager: MCPClientManager | None) -> None:
    """初始化对话模块的 MCP 管理器（由 main.py 在启动时调用）。"""
    global _mcp_manager
    _mcp_manager = manager
    if manager:
        set_mcp_manager(manager)


@router.post("/start", response_model=ConversationStartResponse)
async def start_conversation(req: ConversationStartRequest) -> ConversationStartResponse:
    """基于已完成的 POST /analyze 任务创建对话会话。"""
    store = get_session_store()

    # 从分析任务存储加载结果
    task_data = task_store.get(req.task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"任务 {req.task_id} 不存在")

    if task_data.get("status") != "completed":
        raise HTTPException(status_code=409, detail=f"任务 {req.task_id} 尚未完成（状态: {task_data.get('status')}）")

    repo_url = task_data["repo_url"]
    result_data = task_data.get("result")

    # 解析分析结果
    analysis_result = None
    if result_data:
        try:
            analysis_result = AnalysisResult(**result_data)
        except Exception:
            analysis_result = None

    # 解析 repo owner/name
    try:
        owner, repo = GitHubClient.parse_url(repo_url)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的仓库 URL: {repo_url}")

    # 获取 MCP 工具列表
    mcp_tools: list[dict[str, Any]] = []
    if _mcp_manager:
        try:
            tools = await build_mcp_tools(_mcp_manager)
            for t in tools:
                mcp_tools.append({
                    "name": t.name,
                    "description": t.description or "",
                })
        except Exception:
            logger.warning("获取 MCP 工具列表失败", exc_info=True)

    conv_id = store.create(
        task_id=req.task_id,
        repo_url=repo_url,
        owner=owner,
        repo=repo,
        analysis_result=analysis_result,
        mcp_tools=mcp_tools,
    )

    return ConversationStartResponse(
        conversation_id=conv_id,
        repo_url=repo_url,
        task_id=req.task_id,
    )


@router.post("/{conv_id}/message", response_model=ConversationMessageResponse)
async def send_message(conv_id: str, req: ConversationMessageRequest) -> ConversationMessageResponse:
    """发送对话消息，运行完整的 ReAct 循环直到结束。"""
    store = get_session_store()
    session = store.get(conv_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"会话 {conv_id} 不存在")

    now = datetime.now(timezone.utc).isoformat()

    # 构建 ConversationState
    state: ConversationState = {
        "conversation_id": conv_id,
        "repo_url": session.repo_url,
        "repo_owner": session.repo_owner,
        "repo_name": session.repo_name,
        "messages": [{"role": "user", "content": req.message}],
        "analysis_summary": session.analysis_summary,
        "mcp_tools": session.mcp_tools,
    }

    # 运行 ReAct 循环
    reasoning_steps: list[ReasoningStep] = []
    assistant_response = ""

    try:
        graph = await build_conversation_graph(mcp_manager=_mcp_manager)
        final_state = await graph.ainvoke(state)

        # 提取最终消息
        messages = final_state.get("messages", [])
        if messages:
            # 找到所有 AIMessage 和 ToolMessage
            from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
            for msg in messages[1:]:  # 跳过第一条 HumanMessage
                if isinstance(msg, AIMessage):
                    # 收集 tool_calls 作为推理步骤
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            reasoning_steps.append(ReasoningStep(
                                step_type="tool_call",
                                content=f"调用工具: {tc.get('name', 'unknown')}",
                                tool_name=tc.get("name", "unknown"),
                                tool_args=tc.get("args", {}),
                                timestamp=now,
                            ))
                    # 最终回复
                    if msg.content and not getattr(msg, "tool_calls", None):
                        assistant_response += str(msg.content)
                elif isinstance(msg, ToolMessage):
                    content_preview = str(msg.content)[:300]
                    reasoning_steps.append(ReasoningStep(
                        step_type="observation",
                        content=content_preview,
                        tool_name=msg.name if hasattr(msg, "name") else None,
                        timestamp=now,
                    ))

        # 如果没有显式的 assistant 回复，取最后一条 AIMessage
        if not assistant_response:
            for msg in reversed(messages):
                from langchain_core.messages import AIMessage
                if isinstance(msg, AIMessage) and msg.content:
                    assistant_response = str(msg.content)
                    break

        if not assistant_response:
            assistant_response = "（AI 未生成回复）"

    except Exception as e:
        logger.exception("ReAct 循环失败")
        assistant_response = f"对话处理失败: {e}"
        reasoning_steps.append(ReasoningStep(
            step_type="observation",
            content=f"错误: {e}",
            timestamp=now,
        ))

    # 保存消息到会话历史
    store.add_message(conv_id, "user", req.message)
    store.add_message(conv_id, "assistant", assistant_response, reasoning_steps)

    return ConversationMessageResponse(
        conversation_id=conv_id,
        user_message=req.message,
        assistant_response=assistant_response,
        reasoning_steps=reasoning_steps,
        timestamp=now,
    )


@router.get("/{conv_id}/stream")
async def stream_conversation(conv_id: str, message: str = "") -> StreamingResponse:
    """SSE 流式对话 — 逐步推送推理步骤和回复 token。"""
    store = get_session_store()
    session = store.get(conv_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"会话 {conv_id} 不存在")

    if not message:
        raise HTTPException(status_code=400, detail="缺少 message 参数")

    async def event_stream():
        now = datetime.now(timezone.utc).isoformat()

        state: ConversationState = {
            "conversation_id": conv_id,
            "repo_url": session.repo_url,
            "repo_owner": session.repo_owner,
            "repo_name": session.repo_name,
            "messages": [{"role": "user", "content": message}],
            "analysis_summary": session.analysis_summary,
            "mcp_tools": session.mcp_tools,
        }

        try:
            graph = await build_conversation_graph(mcp_manager=_mcp_manager)

            # 用 astream_events 实现流式
            async for event in graph.astream_events(state, version="v2"):
                kind = event.get("event", "")
                data = event.get("data", {})

                if kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        delta = str(chunk.content)
                        if delta:
                            yield f"data: {json.dumps({'type': 'token', 'content': delta}, ensure_ascii=False)}\n\n"

                elif kind == "on_tool_start":
                    yield f"data: {json.dumps({'type': 'tool_start', 'name': event.get('name', 'unknown')}, ensure_ascii=False)}\n\n"

                elif kind == "on_tool_end":
                    output_str = str(data.get("output", ""))[:200]
                    yield f"data: {json.dumps({'type': 'tool_end', 'name': event.get('name', 'unknown'), 'output': output_str}, ensure_ascii=False)}\n\n"

            yield "data: {\"type\": \"done\"}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

        # 保存到历史
        store.add_message(conv_id, "user", message)
        # Note: SSE 流没有收集完整的 assistant_response，这里只做占位
        store.add_message(conv_id, "assistant", "(streamed response)")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{conv_id}/history", response_model=ConversationHistoryResponse)
async def get_history(conv_id: str) -> ConversationHistoryResponse:
    """获取对话历史。"""
    store = get_session_store()
    session = store.get(conv_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"会话 {conv_id} 不存在")

    messages = [
        HistoryMessage(
            role=m["role"],
            content=m["content"],
            reasoning_steps=[ReasoningStep(**s) for s in m["reasoning_steps"]] if m.get("reasoning_steps") else None,
            timestamp=m.get("timestamp", ""),
        )
        for m in session.messages
    ]

    # 构建分析摘要（从原始 JSON 重构）
    task_data = task_store.get(session.task_id)
    analysis_summary = task_data.get("result") if task_data else None

    return ConversationHistoryResponse(
        conversation_id=conv_id,
        repo_url=session.repo_url,
        messages=messages,
        analysis_summary=analysis_summary,
    )


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str) -> dict[str, str]:
    """删除对话会话。"""
    store = get_session_store()
    if store.delete(conv_id):
        return {"status": "deleted", "conversation_id": conv_id}
    raise HTTPException(status_code=404, detail=f"会话 {conv_id} 不存在")
