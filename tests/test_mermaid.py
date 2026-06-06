"""Mermaid 图生成器测试."""
import pytest

from opensource_analyst.analysis.mermaid import (
    build_module_flowchart,
    build_dependency_graph,
    build_tech_stack_diagram,
    build_all_mermaid,
)
from opensource_analyst.models.analysis import (
    ArchitectureResult, ModuleInfo, TechStack, Dependency, MermaidDiagrams,
)


# ── 测试数据 ──────────────────────────────────

SAMPLE_MODULES = [
    ModuleInfo(
        name="core",
        path="core/",
        responsibility="核心引擎",
        key_files=["core/main.py", "core/utils.py", "core/types.py"],
        imports=[], exported_symbols=[],
    ),
    ModuleInfo(
        name="api",
        path="api/",
        responsibility="REST API 层",
        key_files=["api/routes.py", "api/middleware.py"],
        imports=[], exported_symbols=[],
    ),
]

SAMPLE_ARCHITECTURE = ArchitectureResult(
    architecture_pattern="分层架构",
    modules=SAMPLE_MODULES,
    entry_file="core/main.py",
    module_relations=[
        {"from": "api", "to": "core", "type": "imports"},
    ],
    architecture_summary="test",
)

SAMPLE_TECH_STACK = TechStack(
    languages={"Python": "100%"},
    frameworks=["FastAPI", "Pydantic"],
    key_dependencies=[
        Dependency(name="fastapi", version="0.136", category="core", purpose="Web 框架"),
    ],
)

SAMPLE_IMPORT_MAP = {
    "core/main.py": ["api.routes", "core.utils"],
    "core/utils.py": ["core.types"],
    "api/routes.py": ["core.main"],
}


# ── 单元测试 ──────────────────────────────────

class TestBuildModuleFlowchart:
    """build_module_flowchart 测试."""

    def test_with_valid_architecture(self) -> None:
        """有模块和关系 → 输出有效 Mermaid."""
        result = build_module_flowchart(SAMPLE_ARCHITECTURE)
        assert result.startswith("flowchart LR")
        assert "subgraph" in result
        assert "core" in result or "api" in result
        # 应包含边
        assert "-->" in result

    def test_with_none(self) -> None:
        """architecture=None → 返回空字符串."""
        assert build_module_flowchart(None) == ""

    def test_with_empty_modules(self) -> None:
        """modules 为空列表 → 返回空字符串."""
        empty_arch = ArchitectureResult(
            architecture_pattern="",
            modules=[],
            entry_file=None,
            module_relations=[],
            architecture_summary="",
        )
        assert build_module_flowchart(empty_arch) == ""

    def test_with_no_relations(self) -> None:
        """有模块但无 module_relations → 能生成不含边的图."""
        arch = ArchitectureResult(
            architecture_pattern="单体",
            modules=SAMPLE_MODULES,
            entry_file="main.py",
            module_relations=[],
            architecture_summary="test",
        )
        result = build_module_flowchart(arch)
        assert result.startswith("flowchart LR")
        assert "-->" not in result

    def test_sanitize_special_chars(self) -> None:
        """模块名含特殊字符 → 被正确转义为安全 ID."""
        mods = [
            ModuleInfo(
                name="my-module/v2",
                path="src/",
                responsibility="test",
                key_files=["test.py"],
                imports=[], exported_symbols=[],
            ),
        ]
        arch = ArchitectureResult(
            architecture_pattern="test",
            modules=mods,
            entry_file="test.py",
            module_relations=[],
            architecture_summary="test",
        )
        result = build_module_flowchart(arch)
        assert "my_module_v2" in result  # 特殊字符被替换
        assert result.startswith("flowchart LR")


class TestBuildDependencyGraph:
    """build_dependency_graph 测试."""

    def test_with_valid_import_map(self) -> None:
        """有 import_map → 输出有效 Mermaid."""
        result = build_dependency_graph(SAMPLE_IMPORT_MAP, SAMPLE_MODULES)
        assert result.startswith("flowchart LR")
        assert "-->" in result

    def test_with_none(self) -> None:
        """import_map=None → 返回空字符串."""
        assert build_dependency_graph(None, None) == ""

    def test_with_empty_map(self) -> None:
        """import_map 为空 dict → 返回空字符串."""
        assert build_dependency_graph({}, []) == ""

    def test_without_modules(self) -> None:
        """有 import_map 但无 modules → 能生成，所有文件在 Others 子图中."""
        result = build_dependency_graph(SAMPLE_IMPORT_MAP, None)
        assert "Others" in result
        assert "-->" in result


class TestBuildTechStackDiagram:
    """build_tech_stack_diagram 测试."""

    def test_with_tech_stack_only(self) -> None:
        """只有 tech_stack → 生成语言和框架层."""
        result = build_tech_stack_diagram(SAMPLE_TECH_STACK)
        assert result.startswith("flowchart LR")
        assert "Python" in result

    def test_with_dependencies(self) -> None:
        """tech_stack + dependencies → 包含依赖层."""
        result = build_tech_stack_diagram(SAMPLE_TECH_STACK, SAMPLE_TECH_STACK.key_dependencies)
        assert result.startswith("flowchart LR")

    def test_with_none(self) -> None:
        """全部为 None → 返回空字符串."""
        assert build_tech_stack_diagram(None) == ""


class TestBuildAllMermaid:
    """build_all_mermaid 集成测试."""

    def test_returns_all_three_diagrams(self) -> None:
        """返回 MermaidDiagrams 包含三个图."""
        result = build_all_mermaid(
            architecture=SAMPLE_ARCHITECTURE,
            import_map=SAMPLE_IMPORT_MAP,
            tech_stack=SAMPLE_TECH_STACK,
            dependencies=SAMPLE_TECH_STACK.key_dependencies,
        )
        assert isinstance(result, MermaidDiagrams)
        assert result.module_flowchart.startswith("flowchart LR")
        assert result.dependency_graph.startswith("flowchart LR")
        assert result.tech_stack_diagram.startswith("flowchart LR")


def test_valid_mermaid_syntax() -> None:
    """生成的 Mermaid 字符串可被基础解析器理解."""
    result = build_all_mermaid(
        architecture=SAMPLE_ARCHITECTURE,
        import_map=SAMPLE_IMPORT_MAP,
        tech_stack=SAMPLE_TECH_STACK,
        dependencies=SAMPLE_TECH_STACK.key_dependencies,
    )
    for name, diagram in [
        ("module_flowchart", result.module_flowchart),
        ("dependency_graph", result.dependency_graph),
        ("tech_stack_diagram", result.tech_stack_diagram),
    ]:
        # 基本 Mermaid 格式检查：以 flowchart LR 开头，无空行在头部
        lines = diagram.strip().split("\n")
        assert lines[0].strip() == "flowchart LR", f"{name} 格式错误"
        # 有内容
        assert len(lines) > 1, f"{name} 内容为空"
