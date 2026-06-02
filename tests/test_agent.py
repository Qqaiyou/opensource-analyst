"""Agent 模块测试 — 对 TinyDB 真实调用 DeepSeek API."""

import pytest
from opensource_analyst.agents.base import Analyzer
from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.models.analysis import AnalysisResult, ProjectOverview, TechStack

TINYDB_INFO = RepoInfo(
    owner="msiemens",
    repo="tinydb",
    readme="TinyDB is a lightweight document oriented database optimized for your happiness. "
           "It's written in pure Python and has no external dependencies. "
           "TinyDB is tiny (1800 lines), document oriented, works on Python 3.8+, "
           "100% test coverage, and is powerfully extensible via Middlewares. "
           "License: MIT.",
    file_tree=[
        "tinydb/__init__.py",
        "tinydb/database.py",
        "tinydb/table.py",
        "tinydb/queries.py",
        "tinydb/storages.py",
        "tinydb/middlewares.py",
        "tinydb/operations.py",
        "tinydb/utils.py",
        "tinydb/version.py",
        "tests/test_tinydb.py",
        "tests/test_queries.py",
        "docs/conf.py",
        "setup.py",
        "README.rst",
        "LICENSE",
        "Makefile",
    ],
    languages={"Python": 85642, "Makefile": 1234},
)


@pytest.fixture(scope="module")
def analyzer() -> Analyzer:
    return Analyzer()


# ── 集成测试：真实调用 DeepSeek ─────────────

def test_analyze_returns_correct_types(analyzer: Analyzer) -> None:
    """验证返回类型是 AnalysisResult，所有字段正确。"""
    result = analyzer.analyze(TINYDB_INFO)

    assert isinstance(result, AnalysisResult)
    assert isinstance(result.overview, ProjectOverview)
    assert isinstance(result.tech_stack, TechStack)


def test_analyze_overview_fields(analyzer: Analyzer) -> None:
    """验证概览字段非空且合理。"""
    overview = analyzer.analyze(TINYDB_INFO).overview

    assert len(overview.name) > 0
    assert len(overview.description) > 10
    assert len(overview.use_cases) >= 1
    assert len(overview.license) > 0


def test_analyze_tech_stack_detects_python(analyzer: Analyzer) -> None:
    """验证技术栈正确识别了 Python。"""
    tech_stack = analyzer.analyze(TINYDB_INFO).tech_stack

    assert "Python" in tech_stack.languages or any(
        "python" in k.lower() for k in tech_stack.languages
    )


def test_analyze_key_dependencies(analyzer: Analyzer) -> None:
    """验证 key_dependencies 列表格式正确。"""
    deps = analyzer.analyze(TINYDB_INFO).tech_stack.key_dependencies

    assert isinstance(deps, list)
    if len(deps) > 0:
        dep = deps[0]
        assert isinstance(dep.name, str)
        assert isinstance(dep.purpose, str)
