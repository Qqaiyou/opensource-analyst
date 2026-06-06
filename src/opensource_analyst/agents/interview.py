"""Interview Agent — 深度面试题生成专家.

专注于从项目源码和技术实现细节中提取面试知识点，
覆盖 junior / mid / senior / staff 四个难度级别。
"""

from __future__ import annotations

from opensource_analyst.agents.base import BaseAgent
from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.models.analysis import (
    InterviewQuestion,
    InterviewResult,
    ProjectOverview,
    TechStack,
    Dependency,
    ArchitectureResult,
)
from opensource_analyst.prompts.interview import INTERVIEW_PROMPT


class InterviewAgent(BaseAgent):
    """面试题 Agent — 聚焦生成深度、全面的面试问答.

    InterviewAgent 与 LearningAgent 不同：
        - 不生成学习路线，只聚焦面试题
        - 输出 8-12 个问题，覆盖 junior/mid/senior/staff 四级
        - 每个问题附带相关代码片段，便于追问

    使用方式:
        agent = InterviewAgent()
        result = agent.analyze(repo_info, overview, tech_stack, ...)
    """

    def analyze(
        self,
        repo_info: RepoInfo,
        overview: ProjectOverview | None = None,
        tech_stack: TechStack | None = None,
        dependencies: list[Dependency] | None = None,
        architecture: ArchitectureResult | None = None,
        rag_context: str | None = None,
    ) -> InterviewResult:
        """生成面试题集.

        Args:
            repo_info: M2 仓库信息
            overview: M3 项目概览
            tech_stack: M3 技术栈
            dependencies: M7 依赖分析
            architecture: M8 架构分析
            rag_context: M4 RAG 检索的代码上下文

        Returns:
            InterviewResult: 面试题集
        """
        # 注入信息拼接
        overview_summary = (
            f"**名称**: {overview.name}\n"
            f"**描述**: {overview.description}\n"
            f"**场景**: {'、'.join(overview.use_cases)}\n"
            if overview else "（未提供）"
        )

        lang_str = str(tech_stack.languages) if tech_stack else "（未提供）"
        fw_str = "、".join(tech_stack.frameworks) if tech_stack and tech_stack.frameworks else "无"

        dep_str = "\n".join(
            f"- {d.name} ({d.category}): {d.purpose}"
            for d in (dependencies or [])
        ) if dependencies else "（未提供）"

        arch_str = str(architecture.architecture_summary) if architecture and architecture.architecture_summary else "（未提供）"
        module_str = "\n".join(
            f"- {m.name} ({m.path}): {m.responsibility}"
            for m in (architecture.modules if architecture else [])
        ) if architecture and architecture.modules else "（未提供）"

        rag_context_str = rag_context or "（未提供）"

        prompt = INTERVIEW_PROMPT.format(
            owner=repo_info.owner,
            repo=repo_info.repo,
            readme_summary=repo_info.readme[:800],
            overview_summary=overview_summary,
            languages=lang_str,
            frameworks=fw_str,
            dependencies_summary=dep_str,
            architecture_summary=arch_str,
            modules_summary=module_str,
            rag_context=rag_context_str,
        )

        data = self._invoke_json(prompt)
        return self._parse_result(data)

    def _parse_result(self, data: dict) -> InterviewResult:
        """将 LLM 返回的 dict 转换为 InterviewResult."""
        questions_data = data.get("questions", [])
        questions = [
            InterviewQuestion(
                topic=q.get("topic", ""),
                difficulty=q.get("difficulty", "mid"),
                question=q.get("question", ""),
                answer_hint=q.get("answer_hint", ""),
                related_files=q.get("related_files", []),
                code_context=q.get("code_context", ""),
            )
            for q in questions_data
        ]

        dist: dict[str, int] = {}
        for q in questions:
            diff = q.difficulty
            dist[diff] = dist.get(diff, 0) + 1

        return InterviewResult(
            questions=questions,
            total_questions=len(questions),
            difficulty_distribution=dist,
        )
