"""Session Store + Conversation API 单元测试."""

import pytest
from unittest.mock import patch, MagicMock

from opensource_analyst.api.session import (
    ConversationSessionStore,
    get_session_store,
    _build_analysis_summary,
)
from opensource_analyst.models.analysis import (
    AnalysisResult,
    ProjectOverview,
    TechStack,
    Dependency,
    ArchitectureResult,
    ModuleInfo,
    LearningPath,
    LearningStep,
    InterviewPoint,
    ReadingSuggestion,
    InterviewResult,
    InterviewQuestion,
    ReflectionResult,
    ReflectionIssue,
    MermaidDiagrams,
)
from opensource_analyst.models.conversation import ReasoningStep


# ── SessionStore 单元测试 ─────────────────────

def test_create_and_get_session():
    store = ConversationSessionStore()
    conv_id = store.create(
        task_id="task_1",
        repo_url="https://github.com/a/b",
        owner="a",
        repo="b",
    )
    assert len(conv_id) == 12
    session = store.get(conv_id)
    assert session is not None
    assert session.task_id == "task_1"
    assert session.repo_owner == "a"


def test_create_session_with_analysis():
    store = ConversationSessionStore()
    result = AnalysisResult(
        overview=ProjectOverview(
            name="test", description="A test project",
            use_cases=["testing"], license="MIT",
        ),
        tech_stack=TechStack(
            languages={"Python": "100%"}, frameworks=[], key_dependencies=[],
        ),
    )
    conv_id = store.create(
        task_id="task_2",
        repo_url="https://github.com/a/b",
        owner="a",
        repo="b",
        analysis_result=result,
    )
    session = store.get(conv_id)
    assert "test" in session.analysis_summary
    assert "Python" in session.analysis_summary


def test_add_and_get_messages():
    store = ConversationSessionStore()
    conv_id = store.create("t1", "https://github.com/a/b", "a", "b")
    store.add_message(conv_id, "user", "hello")
    store.add_message(conv_id, "assistant", "hi there", [
        ReasoningStep(step_type="tool_call", content="called search_code", timestamp="t1"),
    ])

    history = store.get_history(conv_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert len(history[1]["reasoning_steps"]) == 1


def test_delete_session():
    store = ConversationSessionStore()
    conv_id = store.create("t1", "https://github.com/a/b", "a", "b")
    assert store.exists(conv_id)
    assert store.delete(conv_id)
    assert not store.exists(conv_id)
    assert store.delete("nonexistent") is False


def test_get_nonexistent_session():
    store = ConversationSessionStore()
    assert store.get("nonexistent") is None
    assert store.get_history("nonexistent") == []


def test_add_message_to_nonexistent():
    store = ConversationSessionStore()
    with pytest.raises(ValueError, match="不存在"):
        store.add_message("nonexistent", "user", "hello")


def test_set_mcp_tools():
    store = ConversationSessionStore()
    conv_id = store.create("t1", "https://github.com/a/b", "a", "b")
    tools = [{"name": "mcp_gh_search", "server_name": "github", "description": "search"}]
    store.set_mcp_tools(conv_id, tools)
    session = store.get(conv_id)
    assert len(session.mcp_tools) == 1


def test_global_store_singleton():
    """get_session_store() 返回同一实例。"""
    s1 = get_session_store()
    s2 = get_session_store()
    assert s1 is s2


# ── _build_analysis_summary 测试 ──────────────

def test_build_summary_full():
    """完整的 AnalysisResult → 摘要文本。"""
    result = AnalysisResult(
        overview=ProjectOverview(
            name="TinyDB", description="Lightweight DB",
            use_cases=["embedded"], license="MIT",
        ),
        tech_stack=TechStack(
            languages={"Python": "98%"}, frameworks=["pytest"],
            key_dependencies=[Dependency(name="pytest", category="test", purpose="testing")],
        ),
        architecture=ArchitectureResult(
            architecture_pattern="Layered",
            modules=[ModuleInfo(
                name="core", path="core/", responsibility="core engine",
                key_files=["main.py"], imports=[], exported_symbols=[],
            )],
            entry_file="__init__.py",
            module_relations=[],
            architecture_summary="layered architecture",
        ),
        learning_path=LearningPath(
            steps=[LearningStep(
                step_number=1, title="Overview", description="Learn TinyDB",
                key_files=["README"], difficulty="beginner", estimated_hours=1.0,
            )],
            prerequisites=["Python"],
            estimated_days=3,
            interview_points=[InterviewPoint(
                topic="storage", question="How does it store?",
                answer_hint="JSON", related_files=["storage.py"],
            )],
            reading_suggestions=[ReadingSuggestion(
                file_path="__init__.py", why_important="entry",
                reading_order=1, focus_points=["API"],
            )],
        ),
        interview_result=InterviewResult(
            questions=[InterviewQuestion(
                topic="storage", difficulty="junior",
                question="What is TinyDB?", answer_hint="embedded DB",
                related_files=["README"],
            )],
            total_questions=1,
            difficulty_distribution={"junior": 1},
        ),
        reflection=ReflectionResult(
            completeness_score=85,
            issues=[ReflectionIssue(
                category="completeness", severity="low",
                description="ok", suggestion="none",
            )],
            summary="good",
        ),
    )

    summary = _build_analysis_summary(result)
    assert "TinyDB" in summary
    assert "Python" in summary
    assert "Layered" in summary
    assert "pytest" in summary
    assert "85/100" in summary
    assert "good" in summary


def test_build_summary_none():
    """None → 默认文本。"""
    assert "未加载" in _build_analysis_summary(None)
