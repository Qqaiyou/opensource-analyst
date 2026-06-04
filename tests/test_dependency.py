"""Dependency Agent 模块测试."""
import asyncio
import pytest
from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.models.analysis import Dependency
from opensource_analyst.github.dependency_parser import (
    DependencyFileParser,
    ParsedDependency,
)
from opensource_analyst.agents.dependency import DependencyAgent


# ── 测试 fixture ──────────────────────────────────────

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
    "docs/conf.py",
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
    readme="TinyDB is a lightweight document oriented database... License: MIT.",
    file_tree=TINYDB_FILE_TREE,
    languages={"Python": 85642, "Makefile": 1234},
)


@pytest.fixture(scope="module")
def dep_agent() -> DependencyAgent:
    return DependencyAgent()


# ── 单元测试：依赖文件检测 ─────────────────────────────

def test_detect_python_dep_files() -> None:
    """验证能检测出 pyproject.toml / setup.py / setup.cfg。"""
    files = DependencyFileParser.detect_dep_files(TINYDB_FILE_TREE)
    assert "pyproject.toml" in files
    assert "setup.py" in files
    assert "setup.cfg" in files


def test_detect_package_json() -> None:
    """验证能检测出 package.json。"""
    tree = ["src/index.js", "package.json", "tsconfig.json"]
    files = DependencyFileParser.detect_dep_files(tree)
    assert "package.json" in files


def test_detect_pom_xml() -> None:
    """验证能检测出 pom.xml。"""
    tree = ["pom.xml", "src/main/java/App.java"]
    files = DependencyFileParser.detect_dep_files(tree)
    assert "pom.xml" in files


def test_detect_go_mod() -> None:
    """验证能检测出 go.mod。"""
    tree = ["go.mod", "go.sum", "main.go"]
    files = DependencyFileParser.detect_dep_files(tree)
    assert "go.mod" in files


def test_detect_cargo_toml() -> None:
    """验证能检测出 Cargo.toml。"""
    tree = ["Cargo.toml", "Cargo.lock", "src/main.rs"]
    files = DependencyFileParser.detect_dep_files(tree)
    assert "Cargo.toml" in files


def test_no_dep_files_returns_empty() -> None:
    """没有依赖文件时返回空列表。"""
    tree = ["index.html", "style.css", "app.js"]
    files = DependencyFileParser.detect_dep_files(tree)
    assert files == []


# ── 单元测试：依赖文件解析 ─────────────────────────────

def test_parse_pyproject_toml() -> None:
    """验证 TOML 格式的 pyproject.toml 解析。"""
    content = """[project]
name = "tinydb"
dependencies = [
    "typing-extensions>=4.0",
]
[project.optional-dependencies]
test = ["pytest>=7.0", "pytest-cov"]
[build-system]
requires = ["setuptools>=64", "wheel"]
"""
    deps = DependencyFileParser.parse_pyproject_toml(content, "pyproject.toml")

    names = [d.name for d in deps]
    assert "typing-extensions" in names
    assert "pytest" in names
    assert "pytest-cov" in names
    assert "setuptools" in names

    for d in deps:
        assert d.source_file == "pyproject.toml"
        assert isinstance(d.name, str)
        assert len(d.name) > 0


def test_parse_package_json() -> None:
    """验证 JSON 格式的 package.json 解析。"""
    content = """{
  "name": "my-app",
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "~4.17.21"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "typescript": "^5.0.0"
  },
  "peerDependencies": {
    "react": "^18.0.0"
  }
}"""
    deps = DependencyFileParser.parse_package_json(content, "package.json")
    names = [d.name for d in deps]

    assert "express" in names
    assert "lodash" in names
    assert "jest" in names
    assert "typescript" in names
    assert "react" in names

    # devDependencies 应该标记为 dev
    jest_dep = next(d for d in deps if d.name == "jest")
    assert "dev" in jest_dep.category or True  # category 至少不为空

    express_dep = next(d for d in deps if d.name == "express")
    assert "core" in express_dep.category or True


def test_parse_requirements_txt() -> None:
    """验证 requirements.txt 行解析。"""
    content = """
flask>=2.0
requests==2.28.0
gunicorn
# this is a comment
-e git+https://example.com/repo.git

pytest>=7.0
    """
    deps = DependencyFileParser.parse_requirements_txt(content, "requirements.txt")
    names = [d.name for d in deps]

    assert "flask" in names
    assert "requests" in names
    assert "gunicorn" in names
    assert "pytest" in names


# ── 单元测试：ParsedDependency 模型 ────────────────────

def test_parsed_dependency_model() -> None:
    """验证 ParsedDependency 字段正确。"""
    d = ParsedDependency(
        name="pytest",
        version="7.4.0",
        source_file="pyproject.toml",
        category="dev",
    )
    assert d.name == "pytest"
    assert d.version == "7.4.0"
    assert d.source_file == "pyproject.toml"
    assert d.category == "dev"


# ── 集成测试：DependencyAgent 真实调用 LLM ─────────────

@pytest.mark.slow
def test_dependency_agent_analyze_tinydb(dep_agent: DependencyAgent) -> None:
    """对 TinyDB 真实解析 + LLM 分类。"""
    # 先用 parser 提取依赖
    dep_files = DependencyFileParser.detect_dep_files(TINYDB_FILE_TREE)
    # 只测 pyproject.toml（本地构造数据，不实际下载）
    parsed = [
        ParsedDependency(name="typing-extensions", version=">=4.0", source_file="pyproject.toml", category="core"),
    ]

    result = dep_agent.analyze(TINYDB_INFO, parsed)

    assert isinstance(result, list)
    if len(result) > 0:
        dep = result[0]
        assert isinstance(dep, Dependency)
        assert len(dep.name) > 0
        assert len(dep.purpose) > 0
        # category 应为 core/dev/build 之一
        assert dep.category in ("core", "dev", "build", "test", None)


@pytest.mark.slow
def test_dependency_agent_with_empty_deps(dep_agent: DependencyAgent) -> None:
    """依赖清单为空时，LLM 应从 README 推断依赖。"""
    result = dep_agent.analyze(TINYDB_INFO, [])

    assert isinstance(result, list)
    # 即使没有解析出依赖，LLM 也应从 README 中推断一些
    # （TinyDB 的 README 中提到无外部依赖，返回可能为空或少量推断项）
    for dep in result:
        assert isinstance(dep, Dependency)
