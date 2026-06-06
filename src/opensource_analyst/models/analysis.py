"""分析结果数据模型."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class Dependency(BaseModel):
    name: str
    version: str | None = None
    category: str | None = None
    purpose: str


class ProjectOverview(BaseModel):
    name: str
    description: str
    use_cases: list[str]
    license: str


class TechStack(BaseModel):
    languages: dict[str, str]
    frameworks: list[str]
    key_dependencies: list[Dependency]


class MermaidDiagrams(BaseModel):
    module_flowchart: str
    dependency_graph: str
    tech_stack_diagram: str


class InterviewQuestion(BaseModel):
    topic: str
    difficulty: str
    question: str
    answer_hint: str
    related_files: list[str]
    code_context: str = ""


class InterviewResult(BaseModel):
    questions: list[InterviewQuestion]
    total_questions: int
    difficulty_distribution: dict[str, int]


class ReflectionIssue(BaseModel):
    category: str
    severity: str
    description: str
    suggestion: str


class ReflectionResult(BaseModel):
    completeness_score: int
    issues: list[ReflectionIssue]
    summary: str


class ModuleInfo(BaseModel):
    name: str
    path: str
    responsibility: str
    key_files: list[str]
    imports: list[str]
    exported_symbols: list[str]


class ArchitectureResult(BaseModel):
    architecture_pattern: str
    modules: list[ModuleInfo]
    entry_file: str | None = None
    module_relations: list[dict]
    architecture_summary: str


class LearningStep(BaseModel):
    step_number: int
    title: str
    description: str
    key_files: list[str]
    difficulty: str
    estimated_hours: float


class InterviewPoint(BaseModel):
    topic: str
    question: str
    answer_hint: str
    related_files: list[str]


class ReadingSuggestion(BaseModel):
    file_path: str
    why_important: str
    reading_order: int
    focus_points: list[str]


class LearningPath(BaseModel):
    steps: list[LearningStep]
    prerequisites: list[str]
    estimated_days: int
    interview_points: list[InterviewPoint]
    reading_suggestions: list[ReadingSuggestion]


class AnalysisResult(BaseModel):
    overview: ProjectOverview
    tech_stack: TechStack
    learning_path: LearningPath | None = None
    architecture: ArchitectureResult | None = None
    mermaid_diagrams: MermaidDiagrams | None = None
    interview_result: InterviewResult | None = None
    reflection: ReflectionResult | None = None
