"""M10 Coordinator Agent + Agent Registry 测试."""
import asyncio
import pytest
from typing import Any
from unittest.mock import AsyncMock, patch

from opensource_analyst.graph.state import GraphState
from opensource_analyst.agents.registry import AgentRegistry, AgentSpec
from opensource_analyst.agents.coordinator import CoordinatorAgent
from opensource_analyst.graph.nodes import (
    coordinator_node,
    build_analysis_registry,
)
from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.models.analysis import (
    ProjectOverview,
    TechStack,
    ArchitectureResult,
    Dependency,
    ModuleInfo,
    LearningPath,
    LearningStep,
)


# ── 单元测试：AgentRegistry ────────────────────────────────

async def _fake_agent(state: GraphState) -> dict[str, Any]:
    return {"result": "ok"}


async def _fake_dep_agent(state: GraphState) -> dict[str, Any]:
    return {"dependencies": []}


def test_registry_register_and_list() -> None:
    """注册 AgentSpec 后可被 get_ready 发现。"""
    registry = AgentRegistry()
    registry.register(AgentSpec(
        name="test_agent",
        description="A test agent",
        dependencies=["repo_info"],
        produces=["result"],
        run=_fake_agent,
    ))

    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "repo_info": RepoInfo(
            owner="a", repo="b", readme="hi",
            file_tree=["main.py"], languages={"Python": 100},
        ),
    }
    ready = registry.get_ready(state)
    assert len(ready) == 1
    assert ready[0].name == "test_agent"


def test_registry_get_ready_empty_state() -> None:
    """repo_url only → get_ready 返回空（缺 repo_info 依赖）。"""
    registry = AgentRegistry()
    registry.register(AgentSpec(
        name="dep_agent",
        description="Needs repo_info",
        dependencies=["repo_info"],
        produces=["result"],
        run=_fake_agent,
    ))
    state: GraphState = {"repo_url": "https://github.com/a/b"}
    ready = registry.get_ready(state)
    assert len(ready) == 0


def test_registry_get_ready_with_repo_info() -> None:
    """有 repo_info → 返回依赖 repo_info 但不依赖 rag_context 的 Agent。"""
    registry = AgentRegistry()
    registry.register(AgentSpec(
        name="dep_agent",
        description="Dependency analysis",
        dependencies=["repo_info"],
        produces=["dependencies"],
        run=_fake_agent,
    ))
    registry.register(AgentSpec(
        name="arch_agent",
        description="Architecture analysis",
        dependencies=["repo_info"],
        produces=["architecture"],
        run=_fake_agent,
    ))
    registry.register(AgentSpec(
        name="learning_agent",
        description="Learning path",
        dependencies=["overview", "tech_stack", "architecture"],
        produces=["learning_path"],
        run=_fake_agent,
    ))

    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "repo_info": RepoInfo(
            owner="a", repo="b", readme="hi",
            file_tree=["main.py"], languages={"Python": 100},
        ),
    }
    ready = registry.get_ready(state)
    names = {s.name for s in ready}
    # dep_agent 和 arch_agent 的依赖都满足（repo_info）；learning_agent 不行
    assert "dep_agent" in names
    assert "arch_agent" in names
    assert "learning_agent" not in names


def test_registry_get_ready_partial_results() -> None:
    """有 overview + architecture → 只返回 learning（依赖已满足）。"""
    registry = AgentRegistry()
    registry.register(AgentSpec(
        name="dep_agent",
        description="Dependency analysis",
        dependencies=["repo_info"],
        produces=["dependencies"],
        run=_fake_agent,
    ))
    registry.register(AgentSpec(
        name="learning_agent",
        description="Learning path generation",
        dependencies=["overview", "tech_stack", "architecture"],
        produces=["learning_path"],
        run=_fake_agent,
    ))

    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "repo_info": RepoInfo(
            owner="a", repo="b", readme="hi",
            file_tree=["main.py"], languages={"Python": 100},
        ),
        "overview": ProjectOverview(
            name="test", description="test",
            use_cases=["test"], license="MIT",
        ),
        "tech_stack": TechStack(
            languages={"Python": "100%"}, frameworks=[], key_dependencies=[],
        ),
        "architecture": ArchitectureResult(
            architecture_pattern="layered",
            modules=[], module_relations=[],
            architecture_summary="test",
        ),
        # dep_agent 还没跑：state 中没有 "dependencies"
    }
    ready = registry.get_ready(state)
    names = {s.name for s in ready}
    # dep_agent: repo_info ✓, dependencies NOT produced yet → should be ready
    # learning_agent: overview ✓, tech_stack ✓, architecture ✓ → should be ready
    assert "dep_agent" in names
    assert "learning_agent" in names


def test_registry_all_done() -> None:
    """全部分析完成 → all_done = True。"""
    registry = AgentRegistry()
    registry.register(AgentSpec(
        name="dep_agent",
        description="Dependency analysis",
        dependencies=["repo_info"],
        produces=["dependencies"],
        run=_fake_agent,
    ))
    registry.register(AgentSpec(
        name="learning_agent",
        description="Learning path generation",
        dependencies=["overview", "tech_stack", "architecture"],
        produces=["learning_path"],
        run=_fake_agent,
    ))

    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "repo_info": RepoInfo(
            owner="a", repo="b", readme="hi",
            file_tree=["main.py"], languages={},
        ),
        "overview": ProjectOverview(
            name="t", description="t", use_cases=[], license="MIT",
        ),
        "tech_stack": TechStack(
            languages={}, frameworks=[], key_dependencies=[],
        ),
        "architecture": ArchitectureResult(
            architecture_pattern="mvc", modules=[], module_relations=[],
            architecture_summary="t",
        ),
        "dependencies": [Dependency(name="pytest", purpose="testing")],
        "learning_path": LearningPath(
            steps=[], prerequisites=[], estimated_days=1,
            interview_points=[], reading_suggestions=[],
        ),
    }
    assert registry.all_done(state) is True


def test_registry_all_done_false() -> None:
    """只有 repo_info → all_done = False。"""
    registry = AgentRegistry()
    registry.register(AgentSpec(
        name="dep_agent",
        description="Dependency analysis",
        dependencies=["repo_info"],
        produces=["dependencies"],
        run=_fake_agent,
    ))
    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "repo_info": RepoInfo(
            owner="a", repo="b", readme="hi",
            file_tree=["main.py"], languages={},
        ),
    }
    assert registry.all_done(state) is False


# ── 单元测试：CoordinatorAgent ─────────────────────────────

@pytest.mark.asyncio
async def test_coordinator_skips_on_error() -> None:
    """state 有 error → coordinator_node 返回空 dict。"""
    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "error": "upstream failure",
    }
    result = await coordinator_node(state, {})
    assert result == {}


@pytest.mark.asyncio
async def test_coordinator_missing_repo_info() -> None:
    """repo_info 缺失 → coordinator_node 返回 error。"""
    state: GraphState = {"repo_url": "https://github.com/a/b"}
    result = await coordinator_node(state, {})
    assert "error" in result
    assert "repo_info" in result["error"]


@pytest.mark.asyncio
async def test_coordinator_agent_failure_isolation() -> None:
    """单 Agent 失败不阻断其他 Agent。"""
    registry = AgentRegistry()

    async def _failing_agent(state: GraphState) -> dict[str, Any]:
        raise ValueError("injected failure")

    async def _ok_agent(state: GraphState) -> dict[str, Any]:
        return {"ok_result": "success"}

    registry.register(AgentSpec(
        name="failing",
        description="Always fails",
        dependencies=["repo_info"],
        produces=["bad_result"],
        run=_failing_agent,
    ))
    registry.register(AgentSpec(
        name="ok",
        description="Always works",
        dependencies=["repo_info"],
        produces=["ok_result"],
        run=_ok_agent,
    ))

    coordinator = CoordinatorAgent(registry)
    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "repo_info": RepoInfo(
            owner="a", repo="b", readme="hi",
            file_tree=["main.py"], languages={},
        ),
    }
    updates = await coordinator.run_round(state)

    # ok_agent 应该成功
    assert updates.get("ok_result") == "success"
    # failing_agent 记录错误，不抛异常
    assert "failing_error" in updates
    assert "injected failure" in updates["failing_error"]


@pytest.mark.asyncio
async def test_coordinator_run_empty_round() -> None:
    """无就绪 Agent 时 run_round 返回空 dict。"""
    registry = AgentRegistry()
    coordinator = CoordinatorAgent(registry)
    state: GraphState = {"repo_url": "https://github.com/a/b"}
    result = await coordinator.run_round(state)
    assert result == {}


# ── 单元测试：build_analysis_registry ──────────────────────

def test_build_analysis_registry_structure() -> None:
    """验证 Registry factory 注册了正确的 Agent。"""
    registry = build_analysis_registry()
    # 4 个 Agent
    assert len(registry._agents) == 4

    names = {s.name for s in registry._agents}
    assert names == {"dependency", "architecture", "analyze", "learning"}

    # learning 依赖 overview + tech_stack + architecture
    learning = next(s for s in registry._agents if s.name == "learning")
    assert "overview" in learning.dependencies
    assert "tech_stack" in learning.dependencies
    assert "architecture" in learning.dependencies

    # dependency 只依赖 repo_info
    dep = next(s for s in registry._agents if s.name == "dependency")
    assert dep.dependencies == ["repo_info"]


def test_build_analysis_registry_parallel_agents() -> None:
    """dependency + architecture + analyze 在有 repo_info 时均为就绪。"""
    registry = build_analysis_registry()
    state: GraphState = {
        "repo_url": "https://github.com/a/b",
        "repo_info": RepoInfo(
            owner="a", repo="b", readme="hi",
            file_tree=["src/main.py"], languages={"Python": 100},
        ),
        "rag_context": "some code context for LLM",
    }
    ready = registry.get_ready(state)
    names = {s.name for s in ready}
    # Round 1: dependency + architecture + analyze 并行
    # learning 不在（缺少 overview + tech_stack）
    assert "dependency" in names
    assert "architecture" in names
    assert "analyze" in names
    assert "learning" not in names


# ── 集成测试：Coordinator 全链路 ──────────────────────────

@pytest.mark.slow
@pytest.mark.asyncio
async def test_coordinator_runs_all_agents() -> None:
    """对 TinyDB 实际调度：Round 1 并行 dependency+architecture+analyze → Round 2 learning。"""
    print("\n" + "=" * 60)
    print("  M10 Coordinator — TinyDB 全链路调度")
    print("=" * 60)

    registry = build_analysis_registry()
    coordinator = CoordinatorAgent(registry)

    print(f"\n[已注册 Agent] {[s.name for s in registry._agents]}")

    repo_info = RepoInfo(
        owner="msiemens", repo="tinydb",
        readme="TinyDB is a lightweight document oriented database...",
        file_tree=[
            "tinydb/__init__.py", "tinydb/database.py", "tinydb/table.py",
            "tinydb/queries.py", "tinydb/storages.py", "tinydb/middlewares.py",
            "tinydb/operations.py", "tinydb/utils.py", "tinydb/version.py",
            "tests/test_tinydb.py", "setup.py", "README.rst",
        ],
        languages={"Python": 85642},
    )

    state: GraphState = {
        "repo_url": "https://github.com/msiemens/tinydb",
        "repo_info": repo_info,
        "rag_context": "TinyDB is a lightweight document oriented database...",
    }

    print("[state 初始状态]")
    for k, v in state.items():
        if v is not None:
            val = str(v)[:80]
            print(f"  {k}: {val}...")

    # ── Round 1 ──
    print("\n── Round 1: 并行执行 dependency + architecture + analyze ──")
    ready1 = registry.get_ready(state)
    print(f"就绪 Agent ({len(ready1)}): {[(s.name, s.dependencies) for s in ready1]}")

    round1 = await coordinator.run_round(state)
    state = {**state, **round1}  # type: ignore[dict-item]

    print(f"\nRound 1 产出 keys: {list(round1.keys())}")

    if "dependencies" in round1:
        deps = round1["dependencies"]
        print(f"\n[dependencies] 共 {len(deps)} 项:")
        for d in deps[:5]:
            print(f"  - {d.name} [{d.category}] {d.purpose[:60] if d.purpose else ''}")
        if len(deps) > 5:
            print(f"  ... 共 {len(deps)} 项")

    if "architecture" in round1:
        arch = round1["architecture"]
        print(f"\n[architecture]")
        print(f"  模式: {arch.architecture_pattern[:100]}")
        print(f"  模块数: {len(arch.modules)}")
        for m in arch.modules[:3]:
            print(f"    - {m.name} ({m.responsibility[:60] if m.responsibility else ''})")
        print(f"  总结: {arch.architecture_summary[:120]}")

    if "overview" in round1:
        ov = round1["overview"]
        print(f"\n[overview] {ov.name}: {ov.description[:80]}")

    if "tech_stack" in round1:
        ts = round1["tech_stack"]
        print(f"[tech_stack] 语言: {ts.languages}, 框架: {ts.frameworks}")

    # ── Round 2 ──
    print("\n── Round 2: learning ──")
    ready2 = registry.get_ready(state)
    print(f"就绪 Agent ({len(ready2)}): {[(s.name, s.dependencies) for s in ready2]}")

    round2 = await coordinator.run_round(state)
    state = {**state, **round2}  # type: ignore[dict-item]

    print(f"Round 2 产出 keys: {list(round2.keys())}")

    learning_path = state.get("learning_path")
    if learning_path:
        print(f"\n[learning_path]")
        print(f"  步骤数: {len(learning_path.steps)}")
        print(f"  预估天数: {learning_path.estimated_days}")
        print(f"  前置知识: {learning_path.prerequisites}")
        for step in learning_path.steps[:3]:
            print(f"  Step {step.step_number}: {step.title} [{step.difficulty}] ({step.estimated_hours}h)")
        if len(learning_path.steps) > 3:
            print(f"  ... 共 {len(learning_path.steps)} 步")
        print(f"  面试知识点: {len(learning_path.interview_points)} 个")
        for ip in learning_path.interview_points[:2]:
            print(f"    - Q: {ip.question[:80]}")
        print(f"  阅读建议: {len(learning_path.reading_suggestions)} 个")

    # ── Round 3 ──
    print("\n── Round 3: 全部完成? ──")
    ready3 = registry.get_ready(state)
    print(f"就绪 Agent: {[s.name for s in ready3]}")
    round3 = await coordinator.run_round(state)

    print(f"\n{'完成! all_done = ' + str(coordinator.all_done(state))}")
    print("=" * 60)

    # Assertions
    assert "dependencies" in round1
    assert "architecture" in round1
    assert "overview" in round1
    assert "tech_stack" in round1
    assert "learning_path" in round2
    assert learning_path is not None
    assert len(learning_path.steps) >= 3
    assert learning_path.estimated_days > 0
    assert len(learning_path.interview_points) >= 2
    assert len(learning_path.reading_suggestions) >= 3
    assert round3 == {}
    assert coordinator.all_done(state) is True
