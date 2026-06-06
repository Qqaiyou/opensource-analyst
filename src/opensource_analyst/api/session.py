"""ConversationSessionStore — 内存对话会话管理.

MVP 用 in-memory dict，与 api/analyze.py 的 _store 模式一致。

每个 ConversationSession:
    - conversation_id: 唯一标识
    - task_id: 关联的分析任务
    - repo_url / repo_owner / repo_name: 仓库信息
    - analysis_summary: 分析结果摘要文本（注入系统提示词）
    - messages: 对话历史 [{role, content, reasoning_steps, timestamp}]
    - mcp_tools: 序列化的 MCP 工具列表
    - created_at: 创建时间
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from opensource_analyst.models.analysis import AnalysisResult
from opensource_analyst.models.conversation import ReasoningStep

logger = logging.getLogger(__name__)


@dataclass
class ConversationSession:
    conversation_id: str
    task_id: str
    repo_url: str
    repo_owner: str
    repo_name: str
    analysis_summary: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    mcp_tools: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""


class ConversationSessionStore:
    """内存对话会话存储 — 支持 CRUD + 消息追加."""

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSession] = {}

    def create(
        self,
        task_id: str,
        repo_url: str,
        owner: str,
        repo: str,
        analysis_result: AnalysisResult | None = None,
        mcp_tools: list[dict[str, Any]] | None = None,
    ) -> str:
        """创建新会话。返回 conversation_id。"""
        import uuid
        conv_id = uuid.uuid4().hex[:12]

        summary = _build_analysis_summary(analysis_result) if analysis_result else ""

        self._sessions[conv_id] = ConversationSession(
            conversation_id=conv_id,
            task_id=task_id,
            repo_url=repo_url,
            repo_owner=owner,
            repo_name=repo,
            analysis_summary=summary,
            mcp_tools=mcp_tools or [],
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        logger.info("创建会话 %s (task=%s, repo=%s)", conv_id, task_id, repo_url)
        return conv_id

    def get(self, conv_id: str) -> ConversationSession | None:
        return self._sessions.get(conv_id)

    def add_message(
        self,
        conv_id: str,
        role: str,
        content: str,
        reasoning_steps: list[ReasoningStep] | None = None,
    ) -> None:
        """追加一条消息到会话历史。"""
        session = self._sessions.get(conv_id)
        if session is None:
            raise ValueError(f"会话 {conv_id} 不存在")

        session.messages.append({
            "role": role,
            "content": content,
            "reasoning_steps": [s.model_dump() for s in reasoning_steps] if reasoning_steps else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_history(self, conv_id: str) -> list[dict]:
        session = self._sessions.get(conv_id)
        if session is None:
            return []
        return list(session.messages)

    def delete(self, conv_id: str) -> bool:
        return self._sessions.pop(conv_id, None) is not None

    def set_mcp_tools(self, conv_id: str, tools: list[dict[str, Any]]) -> None:
        session = self._sessions.get(conv_id)
        if session:
            session.mcp_tools = tools

    def exists(self, conv_id: str) -> bool:
        return conv_id in self._sessions


# ── 模块级单例 ──────────────────────────

_store = ConversationSessionStore()


def get_session_store() -> ConversationSessionStore:
    return _store


# ── 辅助 ────────────────────────────────


def _build_analysis_summary(result: AnalysisResult | None) -> str:
    """将 AnalysisResult 压缩为上下文文本。"""
    if result is None:
        return "（分析结果未加载）"

    parts: list[str] = []

    overview = result.overview
    if overview:
        parts.append(f"## 项目概览\n- 名称: {overview.name}\n- 描述: {overview.description}\n- 适用场景: {'、'.join(overview.use_cases)}\n- 许可证: {overview.license}")

    tech = result.tech_stack
    if tech:
        langs = ", ".join(f"{k}({v})" for k, v in tech.languages.items())
        fw = ", ".join(tech.frameworks) if tech.frameworks else "无"
        deps_lines = "\n".join(f"  - {d.name} ({d.category or 'core'}): {d.purpose}" for d in tech.key_dependencies[:10])
        parts.append(f"## 技术栈\n- 语言: {langs}\n- 框架: {fw}\n- 核心依赖:\n{deps_lines}")

    arch = result.architecture
    if arch:
        mods = "\n".join(f"  - {m.name} ({m.path}): {m.responsibility}" for m in arch.modules)
        parts.append(f"## 架构\n- 模式: {arch.architecture_pattern}\n- 入口: {arch.entry_file or '未识别'}\n- 模块:\n{mods}\n- 总结: {arch.architecture_summary}")

    learning = result.learning_path
    if learning:
        steps = "\n".join(f"  Step {s.step_number}: {s.title} [{s.difficulty}] — {s.description}" for s in learning.steps)
        parts.append(f"## 学习路线\n- 预估天数: {learning.estimated_days}\n- 前置知识: {'、'.join(learning.prerequisites)}\n{steps}")

    interview = result.interview_result
    if interview:
        parts.append(f"## 面试题\n- 共 {interview.total_questions} 题\n- 难度分布: {interview.difficulty_distribution}")

    reflection = result.reflection
    if reflection:
        parts.append(f"## 质量自检\n- 评分: {reflection.completeness_score}/100\n- 总结: {reflection.summary}")

    return "\n\n".join(parts)
