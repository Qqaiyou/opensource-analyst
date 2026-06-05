"""Learning Agent — 学习路线生成专家，综合所有分析结果生成学习路径."""

import json

from opensource_analyst.agents.base import BaseAgent
from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.models.analysis import (
    LearningPath,
    LearningStep,
    InterviewPoint,
    ReadingSuggestion,
    ProjectOverview,
    TechStack,
    Dependency,
    ArchitectureResult,
)
from opensource_analyst.prompts.learning import LEARNING_PATH_PROMPT


class LearningAgent(BaseAgent):
    """学习路线 Agent — 综合全部分析结果，由 LLM 生成结构化学习路线.

    使用方式:
        agent = LearningAgent()
        result = agent.analyze(
            repo_info, overview, tech_stack, dependencies, architecture,
        )
    """

    def analyze(
        self,
        repo_info: RepoInfo,
        overview: ProjectOverview | None = None,
        tech_stack: TechStack | None = None,
        dependencies: list[Dependency] | None = None,
        architecture: ArchitectureResult | None = None,
    ) -> LearningPath:
        """综合所有分析上下文，生成学习路线.

        Args:
            repo_info: M2 仓库信息
            overview: M3 项目概览
            tech_stack: M3 技术栈
            dependencies: M7 依赖分析
            architecture: M8 架构分析

        Returns:
            LearningPath: 包含学习步骤、面试知识点、阅读建议
        """
        # 项目概览
        if overview:
            overview_summary = (
                f"**项目名称**: {overview.name}\n"
                f"**描述**: {overview.description}\n"
                f"**适用场景**: {'、'.join(overview.use_cases)}\n"
            )
        else:
            overview_summary = "（未提供项目概览）"

        # 技术栈
        if tech_stack:
            lang_str = json.dumps(tech_stack.languages, ensure_ascii=False)
            frameworks_str = "、".join(tech_stack.frameworks) if tech_stack.frameworks else "无"
            tech_stack_summary = (
                f"**语言**: {lang_str}\n"
                f"**框架**: {frameworks_str}\n"
            )
        else:
            tech_stack_summary = "（未提供技术栈分析）"

        # 依赖
        if dependencies:
            dep_lines = []
            for d in dependencies:
                ver = f" {d.version}" if d.version else ""
                cat = f" [{d.category}]" if d.category else ""
                dep_lines.append(f"- {d.name}{ver}{cat}: {d.purpose}")
            dependencies_summary = "\n".join(dep_lines)
        else:
            dependencies_summary = "（无依赖分析数据）"

        # 架构
        if architecture:
            mod_lines = []
            for m in architecture.modules:
                mod_lines.append(
                    f"- **{m.name}** ({m.path}): {m.responsibility}\n"
                    f"  关键文件: {', '.join(m.key_files[:5])}"
                )
            modules_detail = "\n".join(mod_lines) if mod_lines else "（无模块信息）"
            architecture_summary = (
                f"**架构模式**: {architecture.architecture_pattern}\n"
                f"**模块信息**:\n{modules_detail}\n"
                f"**架构总结**: {architecture.architecture_summary}\n"
            )
        else:
            architecture_summary = "（未提供架构分析）"

        languages_str = json.dumps(repo_info.languages, ensure_ascii=False)

        prompt = LEARNING_PATH_PROMPT.format(
            owner=repo_info.owner,
            repo=repo_info.repo,
            license="查看 LICENSE 文件",
            overview_summary=overview_summary,
            tech_stack_summary=tech_stack_summary,
            dependencies_summary=dependencies_summary,
            architecture_summary=architecture_summary,
            languages=languages_str,
        )

        data = self._invoke_json(prompt)
        return self._parse_result(data)

    def _parse_result(self, data: dict) -> LearningPath:
        """将 LLM 返回的 dict 转换为 LearningPath."""
        steps_data = data.get("steps", [])
        steps = [
            LearningStep(
                step_number=s.get("step_number", i + 1),
                title=s.get("title", ""),
                description=s.get("description", ""),
                key_files=s.get("key_files", []),
                difficulty=s.get("difficulty", "beginner"),
                estimated_hours=float(s.get("estimated_hours", 1.0)),
            )
            for i, s in enumerate(steps_data)
        ]

        interview_data = data.get("interview_points", [])
        interview_points = [
            InterviewPoint(
                topic=ip.get("topic", ""),
                question=ip.get("question", ""),
                answer_hint=ip.get("answer_hint", ""),
                related_files=ip.get("related_files", []),
            )
            for ip in interview_data
        ]

        reading_data = data.get("reading_suggestions", [])
        reading_suggestions = [
            ReadingSuggestion(
                file_path=rs.get("file_path", ""),
                why_important=rs.get("why_important", ""),
                reading_order=rs.get("reading_order", i + 1),
                focus_points=rs.get("focus_points", []),
            )
            for i, rs in enumerate(reading_data)
        ]

        return LearningPath(
            steps=steps,
            prerequisites=data.get("prerequisites", []),
            estimated_days=data.get("estimated_days", 0),
            interview_points=interview_points,
            reading_suggestions=reading_suggestions,
        )
