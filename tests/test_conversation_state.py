"""ConversationState + Models 单元测试."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage

from opensource_analyst.graph.conversation_state import ConversationState
from opensource_analyst.models.conversation import (
    ConversationStartRequest,
    ConversationStartResponse,
    ConversationMessageRequest,
    ConversationMessageResponse,
    ConversationHistoryResponse,
    HistoryMessage,
    ReasoningStep,
)
from opensource_analyst.prompts.conversation import CONVERSATION_SYSTEM_PROMPT


# ── 模型测试 ──────────────────────────────────

def test_conversation_start_request():
    req = ConversationStartRequest(task_id="abc123")
    assert req.task_id == "abc123"


def test_conversation_message_request():
    req = ConversationMessageRequest(message="hello world")
    assert req.message == "hello world"

    with pytest.raises(Exception):
        ConversationMessageRequest(message="")  # min_length=1

    with pytest.raises(Exception):
        ConversationMessageRequest(message="x" * 4001)  # max_length=4000


def test_reasoning_step_model():
    step = ReasoningStep(
        step_type="tool_call",
        content="调用 search_code",
        tool_name="search_code",
        tool_args={"query": "database"},
        timestamp="2026-01-01T00:00:00",
    )
    assert step.step_type == "tool_call"
    assert step.tool_name == "search_code"
    assert step.tool_args == {"query": "database"}


def test_conversation_message_response():
    step = ReasoningStep(
        step_type="observation",
        content="找到 3 个相关片段",
        timestamp="2026-01-01T00:00:00",
    )
    resp = ConversationMessageResponse(
        conversation_id="conv_1",
        user_message="hi",
        assistant_response="hello!",
        reasoning_steps=[step],
        timestamp="2026-01-01T00:00:00",
    )
    assert resp.conversation_id == "conv_1"
    assert len(resp.reasoning_steps) == 1


def test_history_message_model():
    msg = HistoryMessage(role="user", content="hello", timestamp="2026-01-01T00:00:00")
    assert msg.role == "user"
    assert msg.reasoning_steps is None


def test_history_response_model():
    resp = ConversationHistoryResponse(
        conversation_id="c1",
        repo_url="https://github.com/a/b",
        messages=[
            HistoryMessage(role="user", content="hi", timestamp="t1"),
            HistoryMessage(role="assistant", content="hello!", timestamp="t2"),
        ],
        analysis_summary={"overview": {"name": "test"}},
    )
    assert len(resp.messages) == 2


# ── State 测试 ──────────────────────────────

def test_conversation_state_construction():
    """ConversationState 最小构造。"""
    state: ConversationState = {
        "conversation_id": "c1",
        "repo_url": "https://github.com/a/b",
        "repo_owner": "a",
        "repo_name": "b",
        "messages": [HumanMessage(content="hi")],
    }
    assert state["conversation_id"] == "c1"
    assert len(state["messages"]) == 1
    assert isinstance(state["messages"][0], HumanMessage)


def test_conversation_state_with_analysis():
    """ConversationState 含分析摘要。"""
    state: ConversationState = {
        "conversation_id": "c1",
        "repo_url": "https://github.com/a/b",
        "repo_owner": "a",
        "repo_name": "b",
        "messages": [],
        "analysis_summary": "## 项目概览\n- 名称: test",
        "mcp_tools": [{"name": "mcp_github_search", "server_name": "github", "description": "search issues"}],
    }
    assert state["analysis_summary"]
    assert len(state["mcp_tools"]) == 1


# ── Prompt 测试 ──────────────────────────────

def test_conversation_prompt_renders():
    """系统提示词可以正确渲染。"""
    rendered = CONVERSATION_SYSTEM_PROMPT.format(
        repo_url="https://github.com/a/b",
        analysis_summary="## 项目概览\n- 名称: test",
    )
    assert "https://github.com/a/b" in rendered
    assert "test" in rendered
    assert "search_code" in rendered
    assert "MCP" in rendered


def test_conversation_prompt_with_empty_analysis():
    """空分析摘要也能渲染。"""
    rendered = CONVERSATION_SYSTEM_PROMPT.format(
        repo_url="https://github.com/a/b",
        analysis_summary="（无分析报告）",
    )
    assert "https://github.com/a/b" in rendered
    assert "（无分析报告）" in rendered
