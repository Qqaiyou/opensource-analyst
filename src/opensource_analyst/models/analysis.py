"""分析结果数据模型."""

from pydantic import BaseModel


class Dependency(BaseModel):
    """单个依赖项."""

    name: str
    version: str | None = None
    category: str | None = None  # core / dev / build / test
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
    learning_path: LearningPath | None = None


class ModuleInfo(BaseModel):
    """单个模块信息 — M8 架构分析产出."""

    name: str
    path: str
    responsibility: str
    key_files: list[str]
    imports: list[str]
    exported_symbols: list[str]


class ArchitectureResult(BaseModel):
    """架构分析结果 — M8 ArchitectureAgent 产出."""

    architecture_pattern: str
    modules: list[ModuleInfo]
    entry_file: str | None = None
    module_relations: list[dict]
    architecture_summary: str


class LearningStep(BaseModel):
    """单个学习步骤."""

    step_number: int
    title: str
    description: str
    key_files: list[str]
    difficulty: str  # beginner / intermediate / advanced
    estimated_hours: float


class InterviewPoint(BaseModel):
    """面试知识点."""

    topic: str
    question: str
    answer_hint: str
    related_files: list[str]


class ReadingSuggestion(BaseModel):
    """源码阅读建议."""

    file_path: str
    why_important: str
    reading_order: int
    focus_points: list[str]


class LearningPath(BaseModel):
    """学习路线完整输出 — M9 LearningAgent 产出."""

    steps: list[LearningStep]
    prerequisites: list[str]
    estimated_days: int
    interview_points: list[InterviewPoint]
    reading_suggestions: list[ReadingSuggestion]
