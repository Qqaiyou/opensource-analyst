"""Coordinator Agent — 不自己做分析，只做调度.

CoordinatorAgent 通过 AgentRegistry 管理所有分析 Agent:
    1. 找到当前 state 下所有就绪的 Agent（dependencies 满足 + 尚未产出）
    2. 用 asyncio.gather 并行执行
    3. 合并结果写回 state
    4. 单个 Agent 失败不阻断其他 Agent（独立容错）
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from opensource_analyst.graph.state import GraphState
from opensource_analyst.agents.registry import AgentRegistry, AgentSpec

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """调度引擎 — 管理多 Agent 的并行执行与结果合并.

    使用方式:
        registry = build_analysis_registry()
        coordinator = CoordinatorAgent(registry)

        # 一轮调度：找到就绪 Agent → 并行执行 → 合并结果
        updates = await coordinator.run_round(state)
        state.update(updates)

        # 检查是否全部完成
        if coordinator.all_done(state):
            return updates  # 工作流结束
    """

    def __init__(self, registry: AgentRegistry) -> None:
        self.registry = registry

    async def run_round(self, state: GraphState) -> dict[str, Any]:
        """执行一轮调度：找到所有就绪 Agent → 并行执行 → 合并返回.

        Returns:
            dict: state 的部分更新，可直接用于 LangGraph 节点返回值.
        """
        ready = self.registry.get_ready(state)
        if not ready:
            return {}

        logger.info(
            "Coordinator: dispatching %d agent(s) in parallel — %s",
            len(ready),
            ", ".join(spec.name for spec in ready),
        )

        tasks = [spec.run(state) for spec in ready]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        merged: dict[str, Any] = {}
        failed_count = 0

        for spec, result in zip(ready, results):
            if isinstance(result, Exception):
                logger.warning(
                    "Coordinator: agent '%s' failed: %s", spec.name, result,
                )
                merged[f"{spec.name}_error"] = str(result)
                failed_count += 1
            elif isinstance(result, dict):
                merged.update(result)

        logger.info(
            "Coordinator: round complete — %d succeeded, %d failed",
            len(ready) - failed_count,
            failed_count,
        )
        return merged

    def all_done(self, state: GraphState) -> bool:
        """所有 Agent 都已完成（没有更多可调度的工作）."""
        return self.registry.all_done(state)
