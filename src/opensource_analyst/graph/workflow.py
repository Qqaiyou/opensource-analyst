"""LangGraph 工作流工厂 — 构建并编译 StateGraph."""

from langgraph.graph import StateGraph, END

from opensource_analyst.graph.state import GraphState
from opensource_analyst.graph.nodes import (
    load_repo_node,
    analyze_node,
    architecture_node,
    learning_node,
)


def build_workflow() -> StateGraph:
    """构建并编译分析工作流。

    返回编译后的 StateGraph（LangGraph Runnable），
    调用 app.ainvoke({"repo_url": ...}) 即可执行全流程。

    工作流结构:
        load_repo → analyze → architecture → learning → END
    """
    graph = StateGraph(GraphState)

    graph.add_node("load_repo", load_repo_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("architecture", architecture_node)
    graph.add_node("learning", learning_node)

    graph.set_entry_point("load_repo")
    graph.add_edge("load_repo", "analyze")
    graph.add_edge("analyze", "architecture")
    graph.add_edge("architecture", "learning")
    graph.add_edge("learning", END)

    return graph.compile()
