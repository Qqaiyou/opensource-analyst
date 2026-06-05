"""Learning Agent 模块测试."""
import pytest
from opensource_analyst.models.analysis import (
    LearningStep,
    LearningPath,
    InterviewPoint,
    ReadingSuggestion,
    ProjectOverview,
    TechStack,
    Dependency,
    ArchitectureResult,
    ModuleInfo,
)
from opensource_analyst.agents.learning import LearningAgent
from opensource_analyst.models.repo import RepoInfo


# ── TinyDB 测试数据 ──────────────────────────────────

TINYDB_INFO = RepoInfo(
    owner="msiemens",
    repo="tinydb",
    readme="TinyDB is a lightweight document oriented database optimized for your happiness...",
    file_tree=[
        "tinydb/__init__.py", "tinydb/database.py", "tinydb/table.py",
        "tinydb/queries.py", "tinydb/storages.py", "tinydb/middlewares.py",
        "tinydb/operations.py", "tinydb/utils.py", "tinydb/version.py",
        "tests/test_tinydb.py", "docs/conf.py", "setup.py", "README.rst",
    ],
    languages={"Python": 85642, "Makefile": 1234},
)

TINYDB_OVERVIEW = ProjectOverview(
    name="TinyDB",
    description="轻量级纯 Python 文档数据库，无外部依赖",
    use_cases=["小型应用本地存储", "原型开发", "嵌入式数据管理"],
    license="MIT",
)

TINYDB_TECH_STACK = TechStack(
    languages={"Python": "约 98.6%"},
    frameworks=[],
    key_dependencies=[],
)

TINYDB_DEPS = [
    Dependency(name="pytest", version=">=7.0", category="test", purpose="单元测试框架"),
    Dependency(name="tox", version=None, category="dev", purpose="多版本测试"),
]

TINYDB_MODULE = ModuleInfo(
    name="tinydb",
    path="tinydb/",
    responsibility="核心数据库引擎，包含 JSON 存储、查询、中间件",
    key_files=["database.py", "table.py", "queries.py"],
    imports=[],
    exported_symbols=["TinyDB", "Table", "Query"],
)

TINYDB_ARCH = ArchitectureResult(
    architecture_pattern="分层架构：核心引擎 + 存储后端 + 查询层 + 中间件",
    modules=[TINYDB_MODULE],
    entry_file="tinydb/__init__.py",
    module_relations=[],
    architecture_summary="TinyDB 采用简洁的分层架构，database.py 作为核心协调 storage/queries/middlewares 各层。",
)


# ── 单元测试：模型 ────────────────────────────────────

def test_learning_step_model() -> None:
    """验证 LearningStep 模型字段正确。"""
    step = LearningStep(
        step_number=1,
        title="项目概览与 README 阅读",
        description="了解 TinyDB 是什么、能做什么、基本概念",
        key_files=["README.rst", "tinydb/__init__.py"],
        difficulty="beginner",
        estimated_hours=0.5,
    )
    assert step.step_number == 1
    assert step.title
    assert step.difficulty == "beginner"
    assert len(step.key_files) == 2


def test_learning_path_model() -> None:
    """验证 LearningPath 完整嵌套模型。"""
    steps = [
        LearningStep(
            step_number=1, title="概览", description="了解项目",
            key_files=["README.md"], difficulty="beginner", estimated_hours=0.5,
        ),
        LearningStep(
            step_number=2, title="核心模块", description="阅读核心代码",
            key_files=["main.py"], difficulty="intermediate", estimated_hours=2.0,
        ),
    ]
    interview = [
        InterviewPoint(
            topic="存储引擎设计",
            question="TinyDB 如何实现可插拔的存储后端？",
            answer_hint="查看 storages.py 中的 JSONStorage 类和 Storage 抽象",
            related_files=["tinydb/storages.py"],
        ),
    ]
    reading = [
        ReadingSuggestion(
            file_path="tinydb/__init__.py",
            why_important="项目入口，暴露所有公共 API",
            reading_order=1,
            focus_points=["公开导出的类和函数", "版本信息"],
        ),
    ]

    path = LearningPath(
        steps=steps,
        prerequisites=["Python 基础", "了解 NoSQL 基本概念"],
        estimated_days=3,
        interview_points=interview,
        reading_suggestions=reading,
    )
    assert len(path.steps) == 2
    assert len(path.prerequisites) == 2
    assert path.estimated_days == 3
    assert len(path.interview_points) == 1
    assert len(path.reading_suggestions) == 1
    assert path.steps[0].difficulty == "beginner"
    assert path.steps[1].difficulty == "intermediate"


# ── 集成测试：LearningAgent ───────────────────────────

@pytest.mark.slow
def test_learning_agent_tinydb() -> None:
    """对 TinyDB 做完整学习路线生成（真实 LLM 调用）。"""
    agent = LearningAgent()
    result = agent.analyze(
        repo_info=TINYDB_INFO,
        overview=TINYDB_OVERVIEW,
        tech_stack=TINYDB_TECH_STACK,
        dependencies=TINYDB_DEPS,
        architecture=TINYDB_ARCH,
    )

    assert isinstance(result, LearningPath)
    assert len(result.steps) >= 4  # 至少 4 步学习步骤
    assert result.steps[0].step_number == 1
    assert result.steps[0].difficulty in ("beginner", "intermediate", "advanced")
    assert isinstance(result.prerequisites, list)
    assert result.estimated_days > 0
    assert len(result.interview_points) >= 2
    assert len(result.reading_suggestions) >= 3

    # 验证面试知识点结构
    for ip in result.interview_points:
        assert ip.topic
        assert ip.question
        assert ip.answer_hint
        assert isinstance(ip.related_files, list)

    # 验证阅读建议结构
    for rs in result.reading_suggestions:
        assert rs.file_path
        assert rs.why_important
        assert rs.reading_order > 0
        assert isinstance(rs.focus_points, list)


@pytest.mark.slow
def test_learning_agent_minimal() -> None:
    """最小化输入（仅 overview + repo_info）也能生成路线。"""
    agent = LearningAgent()
    result = agent.analyze(
        repo_info=RepoInfo(
            owner="test", repo="hello",
            readme="A simple hello world project.",
            file_tree=["main.py", "utils.py", "README.md"],
            languages={"Python": 500},
        ),
        overview=ProjectOverview(
            name="hello",
            description="A simple hello world project.",
            use_cases=["学习 Python"],
            license="MIT",
        ),
        tech_stack=None,
        dependencies=None,
        architecture=None,
    )

    assert isinstance(result, LearningPath)
    assert len(result.steps) >= 3
    assert result.estimated_days > 0
