"""LangGraph 工作流测试 — 节点 + 工作流 + 端到端."""

import pytest

from opensource_analyst.graph.state import GraphState
from opensource_analyst.graph.nodes import (
    load_repo_node,
    analyze_node,
    architecture_node,
    learning_node,
)
from opensource_analyst.graph.workflow import build_workflow
from opensource_analyst.models.repo import RepoInfo


# ── 单元测试：GraphState ──────────────────────────────────────

def test_graph_state_minimal() -> None:
    """GraphState 最小字段构造。"""
    state: GraphState = {"repo_url": "https://github.com/a/b"}
    assert state["repo_url"] == "https://github.com/a/b"


def test_graph_state_full() -> None:
    """GraphState 包含分析结果。"""
    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "repo_info": None,
        "overview": None,
        "tech_stack": None,
        "architecture": None,
        "learning_path": None,
        "error": None,
    }
    assert state["error"] is None


# ── 单元测试：占位节点 ──────────────────────────────────────

def test_architecture_node_is_placeholder() -> None:
    """architecture_node 返回 None 占位。"""
    state: GraphState = {"repo_url": "https://github.com/a/b"}
    result = architecture_node(state, {})
    assert result == {"architecture": None}


def test_learning_node_is_placeholder() -> None:
    """learning_node 返回 None 占位。"""
    state: GraphState = {"repo_url": "https://github.com/a/b"}
    result = learning_node(state, {})
    assert result == {"learning_path": None}


def test_placeholder_nodes_skip_on_error() -> None:
    """占位节点在有 error 时返回空 dict。"""
    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "error": "something failed",
    }
    assert architecture_node(state, {}) == {}
    assert learning_node(state, {}) == {}


# ── 单元测试：workflow 构建 ──────────────────────────────────

def test_build_workflow_compiles() -> None:
    """build_workflow() 返回编译后的 Runnable。"""
    app = build_workflow()
    assert app is not None
    # 验证 app 有 invoke 和 ainvoke 方法
    assert hasattr(app, "invoke")
    assert hasattr(app, "ainvoke")


# ── 集成测试：真实工作流 ──────────────────────────────────

@pytest.mark.asyncio
async def test_workflow_full_tinydb() -> None:
    """对 TinyDB 执行完整 LangGraph 工作流。"""
    app = build_workflow()
    state = await app.ainvoke(
        {"repo_url": "https://github.com/msiemens/tinydb"}
    )

    assert state.get("error") is None, f"工作流出错: {state.get('error')}"

    repo_info = state.get("repo_info")
    assert repo_info is not None
    assert isinstance(repo_info, RepoInfo)
    assert repo_info.owner == "msiemens"
    assert repo_info.repo == "tinydb"
    assert len(repo_info.readme) > 0
    assert len(repo_info.file_tree) > 0

    overview = state.get("overview")
    assert overview is not None
    assert overview.name is not None
    assert overview.description is not None

    tech_stack = state.get("tech_stack")
    assert tech_stack is not None
    assert "Python" in tech_stack.languages or len(tech_stack.languages) > 0
