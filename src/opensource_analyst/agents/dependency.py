"""Dependency Agent — 依赖分析专家，结合解析结果 + LLM 做深度解读."""

import json
from typing import Optional

from opensource_analyst.agents.base import BaseAgent
from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.models.analysis import Dependency
from opensource_analyst.github.dependency_parser import ParsedDependency
from opensource_analyst.prompts.dependency import DEPENDENCY_ANALYSIS_PROMPT


class DependencyAgent(BaseAgent):
    """依赖分析 Agent — 基于解析出的依赖清单 + README 用 LLM 做分类和用途解释.

    使用方式:
        agent = DependencyAgent()
        deps = agent.analyze(repo_info, parsed_deps)
    """

    def analyze(
        self,
        repo_info: RepoInfo,
        parsed_deps: list[ParsedDependency],
    ) -> list[Dependency]:
        """分析依赖项，返回增强的依赖列表.

        Args:
            repo_info: M2 产出的仓库信息
            parsed_deps: DependencyFileParser 解析出的原始依赖清单

        Returns:
            增强后的 Dependency 列表，含分类和用途说明
        """
        languages_str = json.dumps(repo_info.languages, ensure_ascii=False)
        readme_summary = repo_info.readme[:800]

        dep_files = sorted({d.source_file for d in parsed_deps})
        dep_files_summary = "、".join(dep_files) if dep_files else "无（未检测到标准依赖文件）"

        if parsed_deps:
            dep_lines = []
            for d in parsed_deps:
                cat = d.category or "unknown"
                ver = f" {d.version}" if d.version else ""
                dep_lines.append(f"- {d.name}{ver} [{cat}] ({d.source_file})")
            parsed_deps_str = "\n".join(dep_lines)
        else:
            parsed_deps_str = "（未解析到任何依赖项）"

        prompt = DEPENDENCY_ANALYSIS_PROMPT.format(
            name=f"{repo_info.owner}/{repo_info.repo}",
            languages=languages_str,
            readme_summary=readme_summary,
            dep_files_summary=dep_files_summary,
            parsed_deps=parsed_deps_str,
        )

        raw = self.invoke(prompt)

        data = self._parse_json_array(raw)
        return [
            Dependency(
                name=d.get("name", ""),
                version=d.get("version"),
                category=d.get("category"),
                purpose=d.get("purpose", ""),
            )
            for d in data
        ]

    @staticmethod
    def _parse_json_array(raw: str) -> list[dict]:
        """解析 LLM 返回的 JSON 数组，含自动修复."""
        # 去掉 markdown 代码块
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            raw = "\n".join(lines)

        # 找到 JSON 数组的起止位置
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start != -1 and end > start:
            raw = raw[start:end]

        return json.loads(raw)  # type: ignore[no-any-return]
