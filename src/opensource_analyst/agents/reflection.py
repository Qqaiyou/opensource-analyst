"""Reflection Agent — 分析结果自我反思与质量评估专家.

在所有分析完成后运行，做一个全面的质量检查:
    1. 完整性 (completeness): 是否有遗漏的重要信息
    2. 准确性 (accuracy): 分析结果是否与仓库实际内容一致
    3. 深度 (depth): 分析是否停留在表面
    4. 一致性 (consistency): 不同板块之间是否有矛盾

如果发现问题但不严重，记录到 ReflectionResult.issues 中；
如果发现重大问题，会在 summary 中建议重新分析特定模块。
"""

from __future__ import annotations

from opensource_analyst.agents.base import BaseAgent
from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.models.analysis import (
    ReflectionIssue,
    ReflectionResult,
    ProjectOverview,
    TechStack,
    ArchitectureResult,
    LearningPath,
    MermaidDiagrams,
)
from opensource_analyst.prompts.reflection import REFLECTION_PROMPT


class ReflectionAgent(BaseAgent):
    """反思 Agent — 自检分析质量并给出改进建议.

    纯 LLM 驱动的检查机制。不修改已有分析结果，只产出质量报告。
    下游可根据 ReflectionResult 决定是否补充分析。

    使用方式:
        agent = ReflectionAgent()
        result = agent.check(repo_info, overview, tech_stack, ...)
    """

    def check(
        self,
        repo_info: RepoInfo,
        overview: ProjectOverview | None = None,
        tech_stack: TechStack | None = None,
        architecture: ArchitectureResult | None = None,
        learning_path: LearningPath | None = None,
        mermaid_diagrams: MermaidDiagrams | None = None,
    ) -> ReflectionResult:
        """对所有分析结果做质量检查.

        Args:
            repo_info: M2 仓库原始数据（README + 文件树）
            overview: M3 项目概览
            tech_stack: M3 技术栈
            architecture: M8 架构分析
            learning_path: M9 学习路线
            mermaid_diagrams: M12 Mermaid 图

        Returns:
            ReflectionResult: 反思结果（评分 + 问题列表 + 总结）
        """
        readme_summary = repo_info.readme[:1000] if repo_info.readme else "（无 README）"
        file_tree_sample = "\n".join(repo_info.file_tree[:50])

        overview_json = overview.model_dump_json(indent=2) if overview else "（未提供）"
        tech_stack_json = tech_stack.model_dump_json(indent=2) if tech_stack else "（未提供）"

        arch_json = "（未提供）"
        if architecture:
            arch_json = architecture.model_dump_json(indent=2)

        learning_json = "（未提供）"
        if learning_path:
            learning_json = learning_path.model_dump_json(indent=2)

        mermaid_summary = ""
        if mermaid_diagrams:
            has_fc = bool(mermaid_diagrams.module_flowchart)
            has_dg = bool(mermaid_diagrams.dependency_graph)
            has_ts = bool(mermaid_diagrams.tech_stack_diagram)
            mermaid_summary = f"模块关系图: {'✓' if has_fc else '✗'}, 文件依赖图: {'✓' if has_dg else '✗'}, 技术栈图: {'✓' if has_ts else '✗'}"

        prompt = REFLECTION_PROMPT.format(
            owner=repo_info.owner,
            repo=repo_info.repo,
            readme_summary=readme_summary,
            file_tree=file_tree_sample,
            overview=overview_json,
            tech_stack=tech_stack_json,
            architecture=arch_json,
            learning_path=learning_json,
            mermaid_summary=mermaid_summary,
        )

        data = self._invoke_json(prompt)
        return self._parse_result(data)

    def _parse_result(self, data: dict) -> ReflectionResult:
        """将 LLM 返回的 dict 转换为 ReflectionResult."""
        issues_data = data.get("issues", [])
        issues = [
            ReflectionIssue(
                category=iss.get("category", "completeness"),
                severity=iss.get("severity", "medium"),
                description=iss.get("description", ""),
                suggestion=iss.get("suggestion", ""),
            )
            for iss in issues_data
        ]

        return ReflectionResult(
            completeness_score=data.get("completeness_score", 50),
            issues=issues,
            summary=data.get("summary", ""),
        )
