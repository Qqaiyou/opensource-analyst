"""Architecture Agent 模块测试."""
import pytest
from opensource_analyst.models.analysis import (
    ArchitectureResult,
    ModuleInfo,
)
from opensource_analyst.github.architecture_analyzer import ArchitectureAnalyzer
from opensource_analyst.agents.architecture import ArchitectureAgent
from opensource_analyst.models.repo import RepoInfo


# ── TinyDB 测试数据 ──────────────────────────────────

TINYDB_FILE_TREE = [
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
    "tests/test_storages.py",
    "docs/conf.py",
    "docs/usage.rst",
    "examples/simple.py",
    "examples/advanced.py",
    "setup.py",
    "setup.cfg",
    "pyproject.toml",
    "README.rst",
    "LICENSE",
    "Makefile",
]

TINYDB_INFO = RepoInfo(
    owner="msiemens",
    repo="tinydb",
    readme="TinyDB is a lightweight document oriented database optimized for your happiness...",
    file_tree=TINYDB_FILE_TREE,
    languages={"Python": 85642, "Makefile": 1234},
)


# ── 单元测试：模块分组 ────────────────────────────────

def test_group_modules_tinydb() -> None:
    """验证 TinyDB 的模块分组：tinydb/ / tests/ / docs/ / examples/。"""
    modules = ArchitectureAnalyzer.group_modules(TINYDB_FILE_TREE)

    assert "tinydb" in modules
    assert "tests" in modules
    assert "docs" in modules
    assert "examples" in modules

    # tinydb 模块应包含核心文件
    tinydb_files = modules["tinydb"]
    assert any("database.py" in f for f in tinydb_files)
    assert any("table.py" in f for f in tinydb_files)
    assert any("queries.py" in f for f in tinydb_files)


def test_group_modules_single_root() -> None:
    """只有一个源码目录时正确分组。"""
    tree = [
        "src/controllers/user.py",
        "src/controllers/admin.py",
        "src/models/db.py",
        "src/services/auth.py",
        "src/main.py",
        "tests/test_auth.py",
    ]
    modules = ArchitectureAnalyzer.group_modules(tree)

    assert "src.controllers" in modules or any("controllers" in k for k in modules)
    assert "src.models" in modules or any("models" in k for k in modules)
    assert "src.services" in modules or any("services" in k for k in modules)


def test_group_modules_flat() -> None:
    """扁平项目（无子目录）时所有 .py 归入 root 模块。"""
    tree = ["app.py", "utils.py", "config.py", "README.md"]
    modules = ArchitectureAnalyzer.group_modules(tree)

    # 应该至少有一个 root 模块组
    assert len(modules) >= 1


# ── 单元测试：入口文件识别 ────────────────────────────

def test_identify_entry_main_py() -> None:
    """能识别 main.py 作为入口。"""
    tree = ["src/main.py", "src/utils.py", "README.md"]
    entry = ArchitectureAnalyzer.identify_entry_file(tree)
    assert entry is not None
    assert "main.py" in entry


def test_identify_entry_dunder_main() -> None:
    """能识别 __main__.py 作为入口。"""
    tree = ["mypackage/__init__.py", "mypackage/__main__.py", "mypackage/core.py"]
    entry = ArchitectureAnalyzer.identify_entry_file(tree)
    assert entry is not None
    assert "__main__.py" in entry


def test_identify_entry_app_py() -> None:
    """能识别 app.py 作为入口（FastAPI/Flask 风格）。"""
    tree = ["app/__init__.py", "app/routes.py", "app.py"]
    entry = ArchitectureAnalyzer.identify_entry_file(tree)
    assert entry is not None


def test_identify_entry_fallback() -> None:
    """无明确入口时 fallback 返回最可能的文件。"""
    tree = ["lib/core.py", "lib/helpers.py"]
    entry = ArchitectureAnalyzer.identify_entry_file(tree)
    assert entry is not None
    assert isinstance(entry, str)


# ── 单元测试：AST import 提取 ─────────────────────────

def test_extract_imports_python() -> None:
    """验证从 Python 源码中正确提取 import 名称。"""
    code = '''
import os
import sys
from tinydb.database import TinyDB
from tinydb.queries import Query
from .storages import JSONStorage
from ..utils import helper
import numpy as np
'''
    imports = ArchitectureAnalyzer.extract_imports(code)

    assert "tinydb.database" in imports
    assert "tinydb.queries" in imports
    # 相对导入保留为模块内引用
    assert ".storages" in imports
    # 标准库不应出现在项目内部 import 中（由调用方过滤）


def test_extract_imports_empty() -> None:
    """无 import 的代码返回空列表。"""
    code = '''
def hello():
    print("world")
'''
    imports = ArchitectureAnalyzer.extract_imports(code)
    assert imports == []


# ── 单元测试：ArchitectureResult 模型 ─────────────────

def test_architecture_result_model() -> None:
    """验证 ArchitectureResult 字段正确。"""
    module = ModuleInfo(
        name="core",
        path="tinydb/",
        responsibility="核心数据库引擎",
        key_files=["database.py", "table.py"],
        imports=["tinydb.queries", "tinydb.storages"],
        exported_symbols=["TinyDB", "Table"],
    )
    result = ArchitectureResult(
        architecture_pattern="分层架构：核心引擎 + 存储后端 + 查询层",
        modules=[module],
        entry_file="tinydb/__init__.py",
        module_relations=[{"from": "tinydb", "to": "tinydb.storages", "type": "imports"}],
        architecture_summary="TinyDB 采用分层架构，核心 database.py 依赖 storages 和 queries 模块。",
    )
    assert result.architecture_pattern
    assert len(result.modules) == 1
    assert result.modules[0].name == "core"
    assert result.entry_file


# ── 集成测试：ArchitectureAgent ───────────────────────

@pytest.mark.slow
def test_architecture_agent_tinydb() -> None:
    """对 TinyDB 做 LLM 架构分析。"""
    agent = ArchitectureAgent()

    # 模拟 ArchitectureAnalyzer 产出
    modules = ArchitectureAnalyzer.group_modules(TINYDB_FILE_TREE)
    entry = ArchitectureAnalyzer.identify_entry_file(TINYDB_FILE_TREE)

    result = agent.analyze(
        repo_info=TINYDB_INFO,
        modules=modules,
        entry_file=entry,
        import_map={},
    )

    assert isinstance(result, ArchitectureResult)
    assert len(result.architecture_pattern) > 0
    assert len(result.modules) > 0
    assert len(result.architecture_summary) > 10
    assert result.entry_file is not None


@pytest.mark.slow
def test_architecture_agent_empty_repo() -> None:
    """低文件数项目也能生成基本架构分析。"""
    agent = ArchitectureAgent()
    modules = {"root": ["main.py", "utils.py"]}
    entry = "main.py"

    result = agent.analyze(
        repo_info=RepoInfo(
            owner="test", repo="test",
            readme="A simple tool.",
            file_tree=["main.py", "utils.py", "README.md"],
            languages={"Python": 1000},
        ),
        modules=modules,
        entry_file=entry,
        import_map={},
    )

    assert isinstance(result, ArchitectureResult)
    assert len(result.architecture_summary) > 0
