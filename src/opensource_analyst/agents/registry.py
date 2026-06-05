"""Agent Registry — 轻量级的 Agent 注册与发现机制.

Coordinator Agent 通过 Registry 知道:
    1. 有哪些 Agent 可用
    2. 每个 Agent 需要什么前置条件（state key）
    3. 每个 Agent 产出什么（state key）
    4. 当前 state 下哪些 Agent 可以并行执行
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from opensource_analyst.graph.state import GraphState


@dataclass
class AgentSpec:
    """描述一个可被 Coordinator 调度的分析 Agent."""

    name: str
    description: str
    dependencies: list[str]  # 执行前必须存在于 state 中的 key（值不能为 None）
    produces: list[str]       # 执行后产出的 state key
    run: Callable[[GraphState], Awaitable[dict[str, Any]]]  # 异步执行函数


class AgentRegistry:
    """Agent 注册表 — 管理所有分析 Agent 的元数据.

    使用方式:
        registry = AgentRegistry()
        registry.register(AgentSpec(...))
        ready = registry.get_ready(state)  # 当前可并行执行的 Agent 列表
        if registry.all_done(state):
            print("所有 Agent 已完成")
    """

    def __init__(self) -> None:
        self._agents: list[AgentSpec] = []

    def register(self, spec: AgentSpec) -> None:
        """注册一个 Agent."""
        self._agents.append(spec)

    def get_ready(self, state: GraphState) -> list[AgentSpec]:
        """返回当前 state 下所有就绪可执行的 Agent.

        就绪条件:
            1. dependencies 全部满足（key 存在且值不为 None）
            2. produces 尚未全部产出（至少一个 key 不存在或为 None）
        """
        ready: list[AgentSpec] = []
        for spec in self._agents:
            if not self._deps_satisfied(spec, state):
                continue
            if self._already_produced(spec, state):
                continue
            ready.append(spec)
        return ready

    def all_done(self, state: GraphState) -> bool:
        """所有 Agent 都已产出（没有更多可执行的 Agent）."""
        return len(self.get_ready(state)) == 0

    def _deps_satisfied(self, spec: AgentSpec, state: GraphState) -> bool:
        return all(state.get(dep) is not None for dep in spec.dependencies)

    def _already_produced(self, spec: AgentSpec, state: GraphState) -> bool:
        return all(state.get(prod) is not None for prod in spec.produces)
