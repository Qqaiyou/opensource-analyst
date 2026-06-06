"""Reflection Agent 测试."""
import pytest

from opensource_analyst.models.analysis import (
    ReflectionIssue, ReflectionResult, ProjectOverview, TechStack,
    ArchitectureResult, LearningPath, LearningStep, ModuleInfo,
    InterviewPoint, ReadingSuggestion, MermaidDiagrams,
)
from opensource_analyst.agents.reflection import ReflectionAgent
from opensource_analyst.models.repo import RepoInfo


# ── 测试数据 ──────────────────────────────────

TINYDB_INFO = RepoInfo(
    owner="msiemens",
    repo="tinydb",
    readme="TinyDB is a lightweight document oriented database optimized for your happiness...",
    file_tree=[
        "tinydb/__init__.py", "tinydb/database.py", "tinydb/table.py",
        "tinydb/queries.py", "tinydb/storages.py", "tinydb/middlewares.py",
    ],
    languages={"Python": 85642},
)

TINYDB_OVERVIEW = ProjectOverview(
    name="TinyDB",
    description="轻量级纯 Python 文档数据库，无外部依赖",
    use_cases=["小型应用本地存储", "原型开发"],
    license="MIT",
)

TINYDB_TECH_STACK = TechStack(
    languages={"Python": "约 98.6%"},
    frameworks=[],
    key_dependencies=[],
)

TINYDB_MODULE = ModuleInfo(
    name="tinydb",
    path="tinydb/",
    responsibility="核心数据库引擎",
    key_files=["database.py", "table.py", "queries.py"],
    imports=[], exported_symbols=[],
)

TINYDB_ARCH = ArchitectureResult(
    architecture_pattern="分层架构",
    modules=[TINYDB_MODULE],
    entry_file="tinydb/__init__.py",
    module_relations=[],
    architecture_summary="简洁的分层架构",
)

TINYDB_LEARNING = LearningPath(
    steps=[
        LearningStep(
            step_number=1, title="概览", description="了解 TinyDB",
            key_files=["README.rst"], difficulty="beginner", estimated_hours=0.5,
        ),
    ],
    prerequisites=["Python 基础"],
    estimated_days=3,
    interview_points=[
        InterviewPoint(
            topic="存储引擎",
            question="TinyDB 用什么存储？",
            answer_hint="JSON 文件",
            related_files=["tinydb/storages.py"],
        ),
    ],
    reading_suggestions=[
        ReadingSuggestion(
            file_path="tinydb/__init__.py", why_important="入口",
            reading_order=1, focus_points=["API"],
        ),
    ],
)

TINYDB_MERMAID = MermaidDiagrams(
    module_flowchart="flowchart LR\n    subgraph tinydb[...]\n    end",
    dependency_graph="flowchart LR\n    n0[main.py] --> n1[utils.py]",
    tech_stack_diagram="flowchart LR\n    Python --> FastAPI",
)


# ── 单元测试：模型 ────────────────────────────

def test_reflection_issue_model() -> None:
    """验证 ReflectionIssue 模型字段。"""
    issue = ReflectionIssue(
        category="completeness",
        severity="high",
        description="缺少中间件模块分析",
        suggestion="补充 middlewares.py 的分析",
    )
    assert issue.category == "completeness"
    assert issue.severity == "high"
    assert issue.description


def test_reflection_result_model() -> None:
    """验证 ReflectionResult 模型字段。"""
    issues = [
        ReflectionIssue(
            category="completeness", severity="medium",
            description="测试问题", suggestion="建议",
        ),
    ]
    result = ReflectionResult(
        completeness_score=75,
        issues=issues,
        summary="总体良好",
    )
    assert result.completeness_score == 75
    assert len(result.issues) == 1


# ── 集成测试：ReflectionAgent ─────────────────

@pytest.mark.slow
def test_reflection_agent_tinydb() -> None:
    """对 TinyDB 分析结果做反思（真实 LLM 调用）。"""
    agent = ReflectionAgent()
    result = agent.check(
        repo_info=TINYDB_INFO,
        overview=TINYDB_OVERVIEW,
        tech_stack=TINYDB_TECH_STACK,
        architecture=TINYDB_ARCH,
        learning_path=TINYDB_LEARNING,
        mermaid_diagrams=TINYDB_MERMAID,
    )

    assert isinstance(result, ReflectionResult)
    assert 0 <= result.completeness_score <= 100
    assert len(result.issues) >= 1
    assert result.summary

    # 验证 issue 结构
    for iss in result.issues:
        assert iss.category in ("completeness", "accuracy", "depth", "consistency")
        assert iss.severity in ("high", "medium", "low")
        assert iss.description
        assert iss.suggestion


@pytest.mark.slow
def test_reflection_agent_minimal() -> None:
    """最小化输入也能生成反思结果。"""
    agent = ReflectionAgent()
    result = agent.check(
        repo_info=RepoInfo(
            owner="test", repo="hello",
            readme="A minimal project.",
            file_tree=["main.py"],
            languages={"Python": 100},
        ),
        overview=ProjectOverview(
            name="hello", description="test",
            use_cases=["test"], license="MIT",
        ),
    )

    assert isinstance(result, ReflectionResult)
    assert 0 <= result.completeness_score <= 100
    assert result.summary
