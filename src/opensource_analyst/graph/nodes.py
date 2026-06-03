"""LangGraph 工作流节点 — 每个节点是一个独立的处理步骤."""

import asyncio
from typing import Any

from langgraph.types import RunnableConfig

from opensource_analyst.graph.state import GraphState
from opensource_analyst.github.client import GitHubClient
from opensource_analyst.github.readme import ReadmeFetcher
from opensource_analyst.github.parser import RepoParser
from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.agents.base import Analyzer


async def load_repo_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """从 GitHub 获取 README + 文件树 + 语言统计，产出 RepoInfo。

    M2 的 GitHubClient → ReadmeFetcher → RepoParser 全链路。
    """
    try:
        owner, repo = GitHubClient.parse_url(state["repo_url"])

        async with GitHubClient() as gh:
            readme_fetcher = ReadmeFetcher(gh)
            parser = RepoParser(gh)

            readme, files, langs = await asyncio.gather(
                readme_fetcher.fetch_readme(owner, repo),
                parser.fetch_file_tree(owner, repo),
                parser.fetch_languages(owner, repo),
            )

        repo_info = RepoInfo(
            owner=owner,
            repo=repo,
            readme=readme,
            file_tree=files,
            languages=langs,
        )
        return {"repo_info": repo_info}
    except Exception as e:
        return {"error": str(e)}


def analyze_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """基于 RepoInfo 调用 LLM 生成项目概览和技术栈分析。

    复用 M3 的 Analyzer.analyze()。
    """
    if state.get("error"):
        return {}

    try:
        analyzer = Analyzer()
        result = analyzer.analyze(state["repo_info"])  # type: ignore[arg-type]
        return {
            "overview": result.overview,
            "tech_stack": result.tech_stack,
        }
    except Exception as e:
        return {"error": str(e)}


def architecture_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """架构分析节点 — M8 实现，当前为占位。"""
    if state.get("error"):
        return {}
    return {"architecture": None}


def learning_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """学习路线节点 — M9 实现，当前为占位。"""
    if state.get("error"):
        return {}
    return {"learning_path": None}
