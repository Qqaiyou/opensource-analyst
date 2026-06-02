"""分析结果数据模型."""

from pydantic import BaseModel


class Dependency(BaseModel):
    """单个依赖项."""

    name: str
    purpose: str


class ProjectOverview(BaseModel):
    """项目概览."""

    name: str
    description: str
    use_cases: list[str]
    license: str


class TechStack(BaseModel):
    """技术栈分析."""

    languages: dict[str, str]
    frameworks: list[str]
    key_dependencies: list[Dependency]


class AnalysisResult(BaseModel):
    """完整的分析结果 — Agent 输出的顶层模型."""

    overview: ProjectOverview
    tech_stack: TechStack
