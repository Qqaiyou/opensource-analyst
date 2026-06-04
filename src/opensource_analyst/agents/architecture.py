"""Architecture Agent — 架构分析专家，静态分析 + LLM 深度解读."""

import json

from opensource_analyst.agents.base import BaseAgent
from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.models.analysis import (
    ArchitectureResult,
    ModuleInfo,
    Dependency,
)
from opensource_analyst.prompts.architecture import ARCHITECTURE_PROMPT


class ArchitectureAgent(BaseAgent):
    """架构分析 Agent — 基于模块分组 + import 关系 + LLM 生成架构报告.

    使用方式:
        agent = ArchitectureAgent()
        result = agent.analyze(repo_info, modules, entry_file, import_map)
    """

    def analyze(
        self,
        repo_info: RepoInfo,
        modules: dict[str, list[str]],
        entry_file: str | None,
        import_map: dict[str, list[str]],
        dependencies: list[Dependency] | None = None,
    ) -> ArchitectureResult:
        """分析项目架构，返回结构化架构报告.

        Args:
            repo_info: M2 产出的仓库信息
            modules: ArchitectureAnalyzer.group_modules() 的产出
            entry_file: ArchitectureAnalyzer.identify_entry_file() 的产出
            import_map: {file_path: [import_name, ...]}
            dependencies: M7 产出的依赖列表（可选）

        Returns:
            ArchitectureResult: 包含架构模式、模块、关系的完整分析
        """
        languages_str = json.dumps(repo_info.languages, ensure_ascii=False)

        # 模块摘要
        if modules:
            mod_lines = []
            for mod_name, files in modules.items():
                file_count = len(files)
                sample = ", ".join(files[:3]) if len(files) <= 3 else ", ".join(files[:3]) + f" ... (共{file_count}个文件)"
                mod_lines.append(f"- {mod_name}/: {sample}")
            modules_summary = "\n".join(mod_lines)
        else:
            modules_summary = "（扁平结构，无明确子目录分组）"

        # import 关系摘要
        if import_map:
            rel_lines = []
            for file_path, imports in import_map.items():
                if imports:
                    rel_lines.append(f"- {file_path} 导入: {', '.join(imports[:5])}")
            import_relations = "\n".join(rel_lines[:30]) if rel_lines else "（未检测到项目内部 import）"
        else:
            import_relations = "（未下载文件进行 import 分析）"

        # 依赖摘要
        if dependencies:
            dep_lines = []
            for d in dependencies[:10]:
                cat = f" [{d.category}]" if d.category else ""
                dep_lines.append(f"- {d.name}{cat}: {d.purpose}")
            dependencies_summary = "\n".join(dep_lines)
        else:
            dependencies_summary = "（无依赖分析数据）"

        prompt = ARCHITECTURE_PROMPT.format(
            owner=repo_info.owner,
            repo=repo_info.repo,
            languages=languages_str,
            readme_summary=repo_info.readme[:800],
            modules_summary=modules_summary,
            entry_file=entry_file or "（未识别）",
            import_relations=import_relations,
            dependencies_summary=dependencies_summary,
        )

        data = self._invoke_json(prompt)
        return self._parse_result(data)

    def _parse_result(self, data: dict) -> ArchitectureResult:
        """将 LLM 返回的 dict 转换为 ArchitectureResult."""
        modules_data = data.get("modules", [])
        modules = [
            ModuleInfo(
                name=m.get("name", ""),
                path=m.get("path", ""),
                responsibility=m.get("responsibility", ""),
                key_files=m.get("key_files", []),
                imports=m.get("imports", []),
                exported_symbols=m.get("exported_symbols", []),
            )
            for m in modules_data
        ]

        return ArchitectureResult(
            architecture_pattern=data.get("architecture_pattern", ""),
            modules=modules,
            entry_file=data.get("entry_file"),
            module_relations=data.get("module_relations", []),
            architecture_summary=data.get("architecture_summary", ""),
        )
