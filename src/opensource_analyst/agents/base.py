"""Agent 基类 + Analyzer — LLM 调用封装."""

import json
import os
from typing import Any

from langchain_openai import ChatOpenAI

from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.models.analysis import AnalysisResult
from opensource_analyst.prompts.overview import OVERVIEW_PROMPT


class BaseAgent:
    """LLM Agent 基类 — 封装 ChatOpenAI 调用和 JSON 解析."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "deepseek-chat",
        temperature: float = 0.3,
    ) -> None:
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY 未设置。请在 .env 文件中配置。")

        base_url = base_url or "https://api.deepseek.com/v1"

        self._llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
        )

    def _invoke(self, prompt: str) -> str:
        """发送 prompt 到 LLM，返回原始文本。"""
        response = self._llm.invoke(prompt)
        return response.content.strip()  # type: ignore[no-any-return]

    def _invoke_json(self, prompt: str) -> dict[str, Any]:
        """发送 prompt 到 LLM，解析返回的 JSON。

        包含自动修复：去掉 markdown 代码块标记、尝试提取第一个 JSON 对象。
        """
        raw = self._invoke(prompt)

        # 去掉可能的 markdown 代码块标记
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            raw = "\n".join(lines)

        # 尝试找到 JSON 对象的起止位置
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            raw = raw[start:end]

        return json.loads(raw)  # type: ignore[no-any-return]


class Analyzer(BaseAgent):
    """单 Agent 分析器 — 基于 RepoInfo 生成项目概览和技术栈分析."""

    def analyze(self, repo_info: RepoInfo) -> AnalysisResult:
        """分析仓库，返回结构化结果。

        Args:
            repo_info: M2 产出的仓库数据（README + 文件树 + 语言统计）

        Returns:
            AnalysisResult: 包含概览和技术栈的完整分析
        """
        file_tree_str = "\n".join(repo_info.file_tree[:200])
        languages_str = json.dumps(repo_info.languages, ensure_ascii=False)

        prompt = OVERVIEW_PROMPT.format(
            readme=repo_info.readme,
            file_tree=file_tree_str,
            languages=languages_str,
        )

        data = self._invoke_json(prompt)
        return AnalysisResult(**data)
