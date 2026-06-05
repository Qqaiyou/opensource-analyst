"""LangGraph 工作流工厂 — 构建并编译 StateGraph.

M10: Coordinator Agent 驱动的多 Agent 并行调度。
"""

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from opensource_analyst.graph.state import GraphState
from opensource_analyst.graph.nodes import (
    load_repo_node,
    index_code_node,
    retrieve_context_node,
    coordinator_node,
    build_analysis_registry,
)


def _should_continue(state: GraphState) -> str:
    """条件边路由：有 error 则短路到 END，否则继续。"""
    if state.get("error"):
        return END
    return "continue"


def _should_loop_coordinator(state: GraphState) -> str:
    """Coordinator 循环条件：如果所有 Agent 完成则 END，否则回到 coordinator。"""
    if state.get("error"):
        return END
    registry = build_analysis_registry()
    if registry.all_done(state):
        return END
    return "coordinator"


def build_workflow() -> CompiledStateGraph:
    """构建并编译 M10 分析工作流。

    返回编译后的 StateGraph（LangGraph Runnable），
    调用 app.ainvoke({"repo_url": ...}) 即可执行全流程。

    M10 工作流结构:
        load_repo → index_code → retrieve_context → coordinator ⇄ END
          (pipeline 节点不变，分析 Agent 由 Coordinator 并行调度)
    """
    graph = StateGraph(GraphState)

    graph.add_node("load_repo", load_repo_node)
    graph.add_node("index_code", index_code_node)
    graph.add_node("retrieve_context", retrieve_context_node)
    graph.add_node("coordinator", coordinator_node)

    graph.set_entry_point("load_repo")

    graph.add_edge("load_repo", "index_code")
    graph.add_conditional_edges(
        "index_code", _should_continue, {"continue": "retrieve_context", END: END}
    )
    graph.add_conditional_edges(
        "retrieve_context", _should_continue, {"continue": "coordinator", END: END}
    )
    graph.add_conditional_edges(
        "coordinator", _should_loop_coordinator, {"coordinator": "coordinator", END: END}
    )

    return graph.compile()


def export_workflow_mermaid() -> str:
    """导出工作流图的 Mermaid 标记字符串。

    可用于可视化调试或写入 .md 文档。
    """
    app = build_workflow()
    return app.get_graph().draw_mermaid()
