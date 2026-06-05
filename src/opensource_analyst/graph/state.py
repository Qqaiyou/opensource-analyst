"""LangGraph 工作流共享状态定义."""

from typing_extensions import NotRequired, TypedDict

from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.models.analysis import (
    ProjectOverview, TechStack, Dependency, ArchitectureResult, LearningPath,
)


class GraphState(TypedDict):
    """在 LangGraph 工作流所有节点间传递的共享状态。

    每个节点读取自己需要的字段，返回部分更新 dict。
    """

    repo_url: str
    repo_info: NotRequired[RepoInfo | None]
    code_indexed: NotRequired[int | None]
    rag_context: NotRequired[str | None]
    parsed_dependencies: NotRequired[list[dict] | None]
    dependencies: NotRequired[list[Dependency] | None]
    overview: NotRequired[ProjectOverview | None]
    tech_stack: NotRequired[TechStack | None]
    architecture: NotRequired[ArchitectureResult | None]
    learning_path: NotRequired[LearningPath | None]
    error: NotRequired[str | None]
