"""LangGraph 工作流测试 — 节点 + 工作流 + 端到端."""

import pytest

from opensource_analyst.graph.state import GraphState
from opensource_analyst.graph.nodes import (
    load_repo_node,
    index_code_node,
    retrieve_context_node,
    analyze_node,
    architecture_node,
    learning_node,
)
from opensource_analyst.graph.workflow import build_workflow, export_workflow_mermaid
from opensource_analyst.models.repo import RepoInfo


# ── 单元测试：GraphState ──────────────────────────────────────

def test_graph_state_minimal() -> None:
    """GraphState 最小字段构造。"""
    state: GraphState = {"repo_url": "https://github.com/a/b"}
    assert state["repo_url"] == "https://github.com/a/b"


def test_graph_state_full() -> None:
    """GraphState 包含 RAG 和分析结果等全部字段。"""
    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "repo_info": None,
        "code_indexed": None,
        "rag_context": None,
        "overview": None,
        "tech_stack": None,
        "architecture": None,
        "learning_path": None,
        "error": None,
    }
    assert state["error"] is None
    assert state["code_indexed"] is None
    assert state["rag_context"] is None


def test_graph_state_partial() -> None:
    """GraphState 只填部分可选字段也合法。"""
    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "code_indexed": 42,
    }
    assert state["code_indexed"] == 42


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


# ── 单元测试：analyze_node 防 御 ──────────────────────────

def test_analyze_node_skips_on_error() -> None:
    """analyze_node 在 state 有 error 时跳过。"""
    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "error": "upstream failure",
    }
    result = analyze_node(state, {})
    assert result == {}


def test_analyze_node_missing_repo_info() -> None:
    """analyze_node 在 repo_info 缺失时返回 error。"""
    state: GraphState = {"repo_url": "https://github.com/a/b"}
    result = analyze_node(state, {})
    assert "error" in result
    assert "repo_info" in result["error"]


# ── 单元测试：RAG 节点错误传播 ───────────────────────────

@pytest.mark.asyncio
async def test_index_code_node_skips_on_error() -> None:
    """index_code_node 在 state 有 error 时跳过。"""
    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "error": "previous failure",
    }
    result = await index_code_node(state, {})
    assert result == {}


@pytest.mark.asyncio
async def test_index_code_node_missing_repo_info() -> None:
    """index_code_node 在 repo_info 缺失时返回 error。"""
    state: GraphState = {"repo_url": "https://github.com/a/b"}
    result = await index_code_node(state, {})
    assert "error" in result
    assert "repo_info" in result["error"]


def test_retrieve_context_node_skips_on_error() -> None:
    """retrieve_context_node 在 state 有 error 时跳过。"""
    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "error": "previous failure",
    }
    result = retrieve_context_node(state, {})
    assert result == {}


def test_retrieve_context_node_missing_repo_info() -> None:
    """retrieve_context_node 在 repo_info 缺失时返回 error。"""
    state: GraphState = {"repo_url": "https://github.com/a/b"}
    result = retrieve_context_node(state, {})
    assert "error" in result
    assert "repo_info" in result["error"]


# ── 单元测试：workflow 构建 ──────────────────────────────────

def test_build_workflow_compiles() -> None:
    """build_workflow() 返回编译后的 Runnable。"""
    app = build_workflow()
    assert app is not None
    assert hasattr(app, "invoke")
    assert hasattr(app, "ainvoke")


def test_export_workflow_mermaid() -> None:
    """export_workflow_mermaid() 返回有效 Mermaid 字符串。"""
    mermaid = export_workflow_mermaid()
    assert isinstance(mermaid, str)
    assert len(mermaid) > 0
    assert "graph TD" in mermaid or "---" in mermaid


@pytest.mark.asyncio
async def test_workflow_error_short_circuit() -> None:
    """工作流在 load_repo 失败后短路到 END，不执行下游节点。"""
    app = build_workflow()
    state = await app.ainvoke({"repo_url": "https://github.com/nonexistent-owner-xyz/nonexistent-repo-xyz"})

    # load_repo 应该报错
    assert state.get("error") is not None
    # 短路后下游节点不得产出分析结果
    assert state.get("overview") is None
    assert state.get("tech_stack") is None
    assert state.get("code_indexed") is None
    assert state.get("rag_context") is None


# ── 集成测试：真实工作流 ──────────────────────────────────

@pytest.mark.asyncio
async def test_workflow_full_tinydb() -> None:
    """对 TinyDB 执行完整 LangGraph 工作流（含 RAG 索引+检索）。"""
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
