"""Interview Agent 测试."""
import pytest

from opensource_analyst.models.analysis import (
    InterviewQuestion, InterviewResult, ProjectOverview, TechStack,
    Dependency, ArchitectureResult, ModuleInfo,
)
from opensource_analyst.agents.interview import InterviewAgent
from opensource_analyst.models.repo import RepoInfo


# ── 测试数据 ──────────────────────────────────

TINYDB_INFO = RepoInfo(
    owner="msiemens",
    repo="tinydb",
    readme="TinyDB is a lightweight document oriented database optimized for your happiness...",
    file_tree=[
        "tinydb/__init__.py", "tinydb/database.py", "tinydb/table.py",
        "tinydb/queries.py", "tinydb/storages.py", "tinydb/middlewares.py",
        "tinydb/operations.py", "tinydb/utils.py", "tinydb/version.py",
        "tests/test_tinydb.py", "setup.py", "README.rst",
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
    key_dependencies=[
        Dependency(name="pytest", version=">=7.0", category="test", purpose="测试"),
    ],
)

TINYDB_ARCH = ArchitectureResult(
    architecture_pattern="分层架构",
    modules=[
        ModuleInfo(
            name="tinydb",
            path="tinydb/",
            responsibility="核心数据库引擎",
            key_files=["database.py", "table.py", "queries.py"],
            imports=[], exported_symbols=[],
        ),
    ],
    entry_file="tinydb/__init__.py",
    module_relations=[],
    architecture_summary="简洁的分层架构",
)


# ── 单元测试：模型 ────────────────────────────

def test_interview_question_model() -> None:
    """验证 InterviewQuestion 模型字段。"""
    q = InterviewQuestion(
        topic="TinyDB 存储引擎",
        difficulty="junior",
        question="TinyDB 默认使用什么存储格式？",
        answer_hint="查看 JSONStorage 类",
        related_files=["tinydb/storages.py"],
    )
    assert q.topic == "TinyDB 存储引擎"
    assert q.difficulty == "junior"
    assert q.related_files == ["tinydb/storages.py"]
    assert q.code_context == ""


def test_interview_result_model() -> None:
    """验证 InterviewResult 模型字段。"""
    questions = [
        InterviewQuestion(
            topic="TinyDB 存储引擎",
            difficulty="junior", question="Q1?",
            answer_hint="Hint", related_files=[],
        ),
        InterviewQuestion(
            topic="查询优化",
            difficulty="senior", question="Q2?",
            answer_hint="Hint", related_files=[],
        ),
    ]
    result = InterviewResult(
        questions=questions,
        total_questions=2,
        difficulty_distribution={"junior": 1, "senior": 1},
    )
    assert result.total_questions == 2
    assert result.difficulty_distribution["junior"] == 1


# ── 集成测试：InterviewAgent ──────────────────

@pytest.mark.slow
def test_interview_agent_tinydb() -> None:
    """对 TinyDB 生成面试题（真实 LLM 调用）。"""
    agent = InterviewAgent()
    result = agent.analyze(
        repo_info=TINYDB_INFO,
        overview=TINYDB_OVERVIEW,
        tech_stack=TINYDB_TECH_STACK,
        dependencies=TINYDB_TECH_STACK.key_dependencies,
        architecture=TINYDB_ARCH,
    )

    assert isinstance(result, InterviewResult)
    # 至少 6 道题（允许 LLM 输出略少于 8）
    assert result.total_questions >= 6
    assert len(result.questions) >= 6

    # 验证难度分布
    assert len(result.difficulty_distribution) >= 2  # 至少两个难度级别

    # 每道题必须有内容
    for q in result.questions:
        assert q.topic
        assert q.question
        assert q.answer_hint
        assert q.difficulty in ("junior", "mid", "senior", "staff")


@pytest.mark.slow
def test_interview_agent_minimal() -> None:
    """最小化输入（仅 overview + repo_info）也能生成。"""
    agent = InterviewAgent()
    result = agent.analyze(
        repo_info=RepoInfo(
            owner="test", repo="hello",
            readme="A simple hello world project.",
            file_tree=["main.py"],
            languages={"Python": 500},
        ),
        overview=ProjectOverview(
            name="hello", description="test",
            use_cases=["学习"], license="MIT",
        ),
    )
    assert isinstance(result, InterviewResult)
    assert result.total_questions >= 4
