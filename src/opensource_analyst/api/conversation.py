"""对话 API — 交互式 ReAct 对话端点.

端点:
    POST /conversation/start          — 基于已完成的 task_id 创建对话会话
    POST /conversation/{id}/message    — 发送消息，返回完整响应 + 推理步骤
    GET  /conversation/{id}/stream     — SSE 流式输出
    GET  /conversation/{id}/history    — 对话历史
    DELETE /conversation/{id}           — 结束对话
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

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
from opensource_analyst.api.session import get_session_store
from opensource_analyst.api.analyze import _store as task_store
from opensource_analyst.github.client import GitHubClient
from opensource_analyst.graph.conversation import build_conversation_graph, set_mcp_manager
from opensource_analyst.mcp.client import MCPClientManager
from opensource_analyst.mcp.tool_bridge import build_mcp_tools
from opensource_analyst.graph.conversation_state import ConversationState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversation", tags=["conversation"])

_mcp_manager: MCPClientManager | None = None


def init_conversation_mcp(manager: MCPClientManager | None) -> None:
    global _mcp_manager
    _mcp_manager = manager
    if manager:
        set_mcp_manager(manager)


@router.post("/start", response_model=ConversationStartResponse)
async def start_conversation(req: ConversationStartRequest) -> ConversationStartResponse:
    store = get_session_store()

    task_data = task_store.get(req.task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail=f"任务 {req.task_id} 不存在")
    if task_data.get("status") != "completed":
        raise HTTPException(status_code=409, detail=f"任务 {req.task_id} 尚未完成（状态: {task_data.get('status')}）")

    repo_url = task_data["repo_url"]
    result_data = task_data.get("result")

    analysis_result = None
    if result_data and isinstance(result_data, dict) and "overview" in result_data:
        try:
            analysis_result = AnalysisResult(**result_data)
        except Exception as e:
            logger.warning("AnalysisResult 解析失败: %s", e)

    try:
        owner, repo = GitHubClient.parse_url(repo_url)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的仓库 URL: {repo_url}")

    mcp_tools: list[dict[str, Any]] = []
    if _mcp_manager:
        try:
            tools = await build_mcp_tools(_mcp_manager)
            for t in tools:
                mcp_tools.append({"name": t.name, "description": t.description or ""})
        except Exception:
            logger.warning("获取 MCP 工具列表失败", exc_info=True)

    conv_id = store.create(
        task_id=req.task_id, repo_url=repo_url, owner=owner, repo=repo,
        analysis_result=analysis_result, mcp_tools=mcp_tools,
    )

    logger.info("会话已创建: %s (task=%s)", conv_id, req.task_id)
    return ConversationStartResponse(conversation_id=conv_id, repo_url=repo_url, task_id=req.task_id)


@router.post("/{conv_id}/message", response_model=ConversationMessageResponse)
async def send_message(conv_id: str, req: ConversationMessageRequest) -> ConversationMessageResponse:
    store = get_session_store()
    session = store.get(conv_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"会话 {conv_id} 不存在")

    now = datetime.now(timezone.utc).isoformat()

    # 打印当前 session 状态用于调试
    logger.info("[DEBUG] session.messages count: %d", len(session.messages))
    for i, m in enumerate(session.messages):
        logger.info("[DEBUG]   msg[%d] role=%s content[:60]=%s", i, m["role"], m["content"][:60])

    # 从 session 恢复历史消息
    history_messages: list = []
    for m in session.messages:
        if m["role"] == "user":
            history_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            history_messages.append(AIMessage(content=m["content"]))

    logger.info("[DEBUG] history_messages count: %d", len(history_messages))

    # 追加当前用户消息
    history_messages.append(HumanMessage(content=req.message))

    state: ConversationState = {
        "conversation_id": conv_id,
        "repo_url": session.repo_url,
        "repo_owner": session.repo_owner,
        "repo_name": session.repo_name,
        "messages": history_messages,
        "analysis_summary": session.analysis_summary,
        "mcp_tools": session.mcp_tools,
    }

    reasoning_steps: list[ReasoningStep] = []
    assistant_response = ""

    try:
        graph = await build_conversation_graph(mcp_manager=_mcp_manager)
        final_state = await graph.ainvoke(state)

        messages = final_state.get("messages", [])

        if final_state.get("error"):
            assistant_response = f"对话处理失败: {final_state['error']}"
        elif messages:
            # 收集 ToolMessage 作为推理步骤
            for msg in messages:
                if isinstance(msg, ToolMessage):
                    reasoning_steps.append(ReasoningStep(
                        step_type="observation",
                        content=str(msg.content)[:500],
                        tool_name=getattr(msg, "name", None),
                        timestamp=now,
                    ))

            # 取最后一条 AIMessage 的 content
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            reasoning_steps.append(ReasoningStep(
                                step_type="tool_call",
                                content=f"调用工具: {tc.get('name', 'unknown')}",
                                tool_name=tc.get("name", "unknown"),
                                tool_args=tc.get("args", {}),
                                timestamp=now,
                            ))
                    if msg.content:
                        assistant_response = str(msg.content)
                        break

        if not assistant_response:
            assistant_response = "（AI 未生成回复）"

    except Exception as e:
        logger.exception("ReAct 循环失败")
        assistant_response = f"对话处理失败: {e}"

    # 保存到会话历史
    store.add_message(conv_id, "user", req.message)
    store.add_message(conv_id, "assistant", assistant_response, reasoning_steps)

    logger.info("[DEBUG] after save: session.messages count: %d", len(session.messages))

    return ConversationMessageResponse(
        conversation_id=conv_id,
        user_message=req.message,
        assistant_response=assistant_response,
        reasoning_steps=reasoning_steps,
        timestamp=now,
    )


@router.get("/{conv_id}/stream")
async def stream_conversation(conv_id: str, message: str = "") -> StreamingResponse:
    store = get_session_store()
    session = store.get(conv_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"会话 {conv_id} 不存在")
    if not message:
        raise HTTPException(status_code=400, detail="缺少 message 参数")

    async def event_stream():
        state: ConversationState = {
            "conversation_id": conv_id,
            "repo_url": session.repo_url,
            "repo_owner": session.repo_owner,
            "repo_name": session.repo_name,
            "messages": [HumanMessage(content=message)],
            "analysis_summary": session.analysis_summary,
            "mcp_tools": session.mcp_tools,
        }
        try:
            graph = await build_conversation_graph(mcp_manager=_mcp_manager)
            async for event in graph.astream_events(state, version="v2"):
                kind = event.get("event", "")
                data = event.get("data", {})
                if kind == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield f"data: {json.dumps({'type': 'token', 'content': str(chunk.content)}, ensure_ascii=False)}\n\n"
                elif kind == "on_tool_start":
                    yield f"data: {json.dumps({'type': 'tool_start', 'name': event.get('name', 'unknown')}, ensure_ascii=False)}\n\n"
                elif kind == "on_tool_end":
                    yield f"data: {json.dumps({'type': 'tool_end', 'name': event.get('name', 'unknown'), 'output': str(data.get('output', ''))[:200]}, ensure_ascii=False)}\n\n"
            yield "data: {\"type\": \"done\"}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
        store.add_message(conv_id, "user", message)
        store.add_message(conv_id, "assistant", "(streamed response)")

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/{conv_id}/history", response_model=ConversationHistoryResponse)
async def get_history(conv_id: str) -> ConversationHistoryResponse:
    store = get_session_store()
    session = store.get(conv_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"会话 {conv_id} 不存在")

    messages = [
        HistoryMessage(
            role=m["role"], content=m["content"],
            reasoning_steps=[ReasoningStep(**s) for s in m["reasoning_steps"]] if m.get("reasoning_steps") else None,
            timestamp=m.get("timestamp", ""),
        )
        for m in session.messages
    ]

    task_data = task_store.get(session.task_id)
    analysis_summary = task_data.get("result") if task_data else None

    return ConversationHistoryResponse(
        conversation_id=conv_id, repo_url=session.repo_url,
        messages=messages, analysis_summary=analysis_summary,
    )


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str) -> dict[str, str]:
    store = get_session_store()
    if store.delete(conv_id):
        return {"status": "deleted", "conversation_id": conv_id}
    raise HTTPException(status_code=404, detail=f"会话 {conv_id} 不存在")
