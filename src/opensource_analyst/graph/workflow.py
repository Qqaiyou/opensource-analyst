"""LangGraph 工作流工厂 — 构建并编译 StateGraph."""

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from opensource_analyst.graph.state import GraphState
from opensource_analyst.graph.nodes import (
    load_repo_node,
    index_code_node,
    retrieve_context_node,
    analyze_node,
    architecture_node,
    learning_node,
)


def _should_continue(state: GraphState) -> str:
    """条件边路由：有 error 则短路到 END，否则继续。"""
    if state.get("error"):
        return END
    return "continue"


def build_workflow() -> CompiledStateGraph:
    """构建并编译分析工作流。

    返回编译后的 StateGraph（LangGraph Runnable），
    调用 app.ainvoke({"repo_url": ...}) 即可执行全流程。

    工作流结构:
        load_repo → index_code → retrieve_context → analyze → architecture → learning → END
        每个节点后检查 error，有 error 则直接跳转到 END。
    """
    graph = StateGraph(GraphState)

    graph.add_node("load_repo", load_repo_node)
    graph.add_node("index_code", index_code_node)
    graph.add_node("retrieve_context", retrieve_context_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("architecture", architecture_node)
    graph.add_node("learning", learning_node)

    graph.set_entry_point("load_repo")

    graph.add_edge("load_repo", "index_code")
    graph.add_conditional_edges(
        "index_code", _should_continue, {"continue": "retrieve_context", END: END}
    )
    graph.add_conditional_edges(
        "retrieve_context", _should_continue, {"continue": "analyze", END: END}
    )
    graph.add_conditional_edges(
        "analyze", _should_continue, {"continue": "architecture", END: END}
    )
    graph.add_edge("architecture", "learning")
    graph.add_edge("learning", END)

    return graph.compile()


def export_workflow_mermaid() -> str:
    """导出工作流图的 Mermaid 标记字符串。

    可用于可视化调试或写入 .md 文档。
    """
    app = build_workflow()
    return app.get_graph().draw_mermaid()
