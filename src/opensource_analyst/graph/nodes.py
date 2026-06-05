"""LangGraph 工作流节点 — 每个节点是一个独立的处理步骤."""

import asyncio
import logging
from typing import Any

from langgraph.types import RunnableConfig

from opensource_analyst.graph.state import GraphState
from opensource_analyst.github.client import GitHubClient
from opensource_analyst.github.readme import ReadmeFetcher
from opensource_analyst.github.parser import RepoParser
from opensource_analyst.github.dependency_parser import DependencyFileParser
from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.agents.base import Analyzer
from opensource_analyst.agents.dependency import DependencyAgent
from opensource_analyst.agents.architecture import ArchitectureAgent
from opensource_analyst.agents.learning import LearningAgent
from opensource_analyst.agents.registry import AgentRegistry, AgentSpec
from opensource_analyst.agents.coordinator import CoordinatorAgent
from opensource_analyst.github.architecture_analyzer import ArchitectureAnalyzer
from opensource_analyst.vectorstore.chroma import VectorStore
from opensource_analyst.rag.indexer import CodeIndexer
from opensource_analyst.rag.retriever import CodeRetriever

logger = logging.getLogger(__name__)


async def load_repo_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """从 GitHub 获取 README + 文件树 + 语言统计，产出 RepoInfo。

    M2 的 GitHubClient → ReadmeFetcher → RepoParser 全链路。
    """
    try:
        owner, repo = GitHubClient.parse_url(state["repo_url"])

        async with GitHubClient() as gh:
            readme_fetcher = ReadmeFetcher(gh)
            parser = RepoParser(gh)

            readme, files, langs = await asyncio.gather(
                readme_fetcher.fetch_readme(owner, repo),
                parser.fetch_file_tree(owner, repo),
                parser.fetch_languages(owner, repo),
            )

        repo_info = RepoInfo(
            owner=owner,
            repo=repo,
            readme=readme,
            file_tree=files,
            languages=langs,
        )
        return {"repo_info": repo_info}
    except Exception as e:
        return {"error": str(e)}


async def index_code_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """下载仓库代码文件并建 ChromaDB 向量索引。

    M4 的 CodeIndexer 全链路：过滤 → 下载 → 分块 → 向量化 → 存储。
    如果 collection 已有数据则跳过，避免重复建索引。
    """
    if state.get("error"):
        return {}

    try:
        repo_info = state["repo_info"]
        if not repo_info:
            return {"error": "index_code_node: repo_info 缺失"}

        collection = f"{repo_info.owner}_{repo_info.repo}"
        store = VectorStore(collection)

        existing = store.count()
        if existing > 0:
            return {"code_indexed": existing}

        indexer = CodeIndexer(store)
        indexed = await indexer.index_repo(
            repo_info.owner, repo_info.repo, repo_info.file_tree,
        )
        return {"code_indexed": indexed}
    except Exception as e:
        return {"error": str(e)}


def retrieve_context_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """基于 README 语义检索最相关的代码片段，作为 LLM 上下文。

    M4 的 CodeRetriever 全链路：embed query → 相似搜索 → 拼接上下文。
    """
    if state.get("error"):
        return {}

    try:
        repo_info = state["repo_info"]
        if not repo_info:
            return {"error": "retrieve_context_node: repo_info 缺失"}

        collection = f"{repo_info.owner}_{repo_info.repo}"
        store = VectorStore(collection)
        retriever = CodeRetriever(store)

        query = repo_info.readme[:500]
        context = retriever.search_as_context(query, k=10)
        return {"rag_context": context}
    except Exception as e:
        return {"error": str(e)}


async def dependency_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """检测依赖文件 → 下载 → 解析 → LLM 分类解读。

    M7 Dependency Agent 全链路：文件检测 → 解析 → LLM 深度分析。
    产出 parsed_dependencies 和 dependencies 写入 state。
    """
    if state.get("error"):
        return {}

    try:
        repo_info = state["repo_info"]
        if not repo_info:
            return {"error": "dependency_node: repo_info 缺失"}

        # 1. 检测依赖文件
        dep_files = DependencyFileParser.detect_dep_files(repo_info.file_tree)

        # 2. 下载并解析
        parser = DependencyFileParser()
        parsed = await parser.fetch_and_parse(
            repo_info.owner, repo_info.repo, dep_files,
        )

        # 3. LLM 深度分析
        agent = DependencyAgent()
        dependencies = agent.analyze(repo_info, parsed)

        parsed_dicts = [p.model_dump() for p in parsed]

        return {
            "parsed_dependencies": parsed_dicts,
            "dependencies": dependencies,
        }
    except Exception as e:
        return {"error": str(e)}


def analyze_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """基于 RepoInfo + RAG 上下文 + 依赖分析结果调用 LLM 生成项目概览和技术栈分析。

    复用 M3 的 Analyzer.analyze()，当 rag_context 或 dependencies 可用时注入上下文。
    """
    if state.get("error"):
        return {}

    repo_info = state.get("repo_info")
    if not repo_info:
        return {"error": "analyze_node: repo_info 缺失，上游节点可能未正常执行"}

    try:
        analyzer = Analyzer()
        rag_context = state.get("rag_context")
        dependencies = state.get("dependencies")

        result = analyzer.analyze(
            repo_info,
            rag_context=rag_context,  # type: ignore[arg-type]
            dependencies=dependencies,  # type: ignore[arg-type]
        )
        return {
            "overview": result.overview,
            "tech_stack": result.tech_stack,
        }
    except Exception as e:
        return {"error": str(e)}


async def architecture_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """静态分析目录结构 → 识别模块+入口 → AST 提取 import → LLM 架构报告。

    M8 ArchitectureAgent 全链路：
    1. ArchitectureAnalyzer 按目录分组模块
    2. 识别入口文件
    3. 下载关键 .py 文件做 AST import 分析
    4. ArchitectureAgent (LLM) 生成架构报告
    """
    if state.get("error"):
        return {}

    try:
        repo_info = state["repo_info"]
        if not repo_info:
            return {"error": "architecture_node: repo_info 缺失"}

        file_tree = repo_info.file_tree

        # 1. 模块分组
        modules = ArchitectureAnalyzer.group_modules(file_tree)

        # 2. 入口文件识别
        entry_file = ArchitectureAnalyzer.identify_entry_file(file_tree)

        # 3. 下载关键文件 + AST import 提取
        analyzer = ArchitectureAnalyzer()
        source_files = await analyzer.download_key_files(
            repo_info.owner, repo_info.repo, file_tree, max_files=30,
        )

        import_map: dict[str, list[str]] = {}
        for path, code in source_files.items():
            imports = ArchitectureAnalyzer.extract_imports(code)
            # 只保留项目内部 import
            project_imports = [
                i for i in imports
                if ArchitectureAnalyzer.is_project_import(i, modules)
            ]
            if project_imports:
                import_map[path] = project_imports

        # 4. 模块间关系推断
        relations = ArchitectureAnalyzer.infer_module_relations(modules, import_map)

        # 5. LLM 深度分析
        agent = ArchitectureAgent()
        dependencies = state.get("dependencies")
        result = agent.analyze(
            repo_info, modules, entry_file, import_map,
            dependencies=dependencies,  # type: ignore[arg-type]
        )

        return {"architecture": result}
    except Exception as e:
        return {"error": str(e)}


def learning_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """综合所有前置分析结果，由 LLM 生成结构化学习路线.

    M9 LearningAgent：注入 overview + tech_stack + dependencies + architecture
    到 LLM prompt，生成 LearningPath（学习步骤 + 面试知识点 + 源码阅读建议）。
    """
    if state.get("error"):
        return {}

    try:
        repo_info = state.get("repo_info")
        if not repo_info:
            return {"error": "learning_node: repo_info 缺失"}

        overview = state.get("overview")
        tech_stack = state.get("tech_stack")
        dependencies = state.get("dependencies")
        architecture = state.get("architecture")

        agent = LearningAgent()
        learning_path = agent.analyze(
            repo_info=repo_info,
            overview=overview,  # type: ignore[arg-type]
            tech_stack=tech_stack,  # type: ignore[arg-type]
            dependencies=dependencies,  # type: ignore[arg-type]
            architecture=architecture,  # type: ignore[arg-type]
        )
        return {"learning_path": learning_path}
    except Exception as e:
        return {"error": str(e)}


# ── M10: Agent Registry 工厂 ──────────────────────────────

# 模块级 registry 缓存，确保 coordinator_node 和 _should_loop_coordinator
# 共享同一实例（避免重复创建 AgentSpec 和闭包 wrapper）
_registry: AgentRegistry | None = None


def _dependency_node_sync(state: GraphState) -> dict[str, Any]:
    """在独立线程中同步执行 dependency_node（含阻塞 LLM 调用）."""
    return asyncio.run(dependency_node(state))


def _architecture_node_sync(state: GraphState) -> dict[str, Any]:
    """在独立线程中同步执行 architecture_node（含阻塞 LLM 调用）."""
    return asyncio.run(architecture_node(state))


def build_analysis_registry() -> AgentRegistry:
    """构建分析 Agent 注册表，定义各 Agent 的依赖关系和产出 key.

    依赖关系决定了并行调度策略:
        Round 1: dependency + architecture + analyze（三者互不依赖，并行）
        Round 2: learning（依赖 overview/tech_stack/architecture）

    所有包含阻塞 LLM 调用的 Agent 都通过 run_in_executor 包装，
    确保 asyncio.gather 真正并行执行。
    """
    global _registry
    if _registry is not None:
        return _registry

    _registry = AgentRegistry()

    # Round 1 Agent: 依赖检测 — repo_info 已就绪，LLM 调用通过 run_in_executor 避免阻塞事件循环
    async def _dependency_node_async(state: GraphState) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _dependency_node_sync, state)

    _registry.register(AgentSpec(
        name="dependency",
        description="依赖文件检测 + 解析 + LLM 分类",
        dependencies=["repo_info"],
        produces=["dependencies"],
        run=_dependency_node_async,
    ))

    # Round 1 Agent: 架构分析 — repo_info 已就绪，LLM 调用通过 run_in_executor 避免阻塞事件循环
    async def _architecture_node_async(state: GraphState) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _architecture_node_sync, state)

    _registry.register(AgentSpec(
        name="architecture",
        description="模块分组 + 入口识别 + AST import + LLM 架构报告",
        dependencies=["repo_info"],
        produces=["architecture"],
        run=_architecture_node_async,
    ))

    # Round 1 Agent: 概览/技术栈分析 — 需要 repo_info + rag_context
    def _analyze_node_sync(state: GraphState) -> dict[str, Any]:
        return analyze_node(state)

    async def _analyze_node_async(state: GraphState) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _analyze_node_sync, state)

    _registry.register(AgentSpec(
        name="analyze",
        description="项目概览 + 技术栈分析（LLM）",
        dependencies=["repo_info", "rag_context"],
        produces=["overview", "tech_stack"],
        run=_analyze_node_async,
    ))

    # Round 2 Agent: 学习路线 — 需要 overview + tech_stack + architecture
    def _learning_node_sync(state: GraphState) -> dict[str, Any]:
        return learning_node(state)

    async def _learning_node_async(state: GraphState) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _learning_node_sync, state)

    _registry.register(AgentSpec(
        name="learning",
        description="学习路线生成 + 面试知识点 + 源码阅读建议（LLM）",
        dependencies=["overview", "tech_stack", "architecture"],
        produces=["learning_path"],
        run=_learning_node_async,
    ))

    return _registry


# ── M10: Coordinator 调度节点 ──────────────────────────────


async def coordinator_node(
    state: GraphState, config: RunnableConfig | None = None
) -> dict[str, Any]:
    """Coordinator Agent — 多 Agent 并行调度 + 结果合并.

    M10 Coordinator：找到所有就绪 Agent → parallel asyncio.gather → 合并结果。
    循环执行直到 all_done（LangGraph condition edge 控制循环）。
    Registry 通过 build_analysis_registry() 缓存，与 _should_loop_coordinator 共享同一实例。
    """
    if state.get("error"):
        return {}

    try:
        repo_info = state.get("repo_info")
        if not repo_info:
            return {"error": "coordinator_node: repo_info 缺失"}

        registry = build_analysis_registry()
        coordinator = CoordinatorAgent(registry)
        updates = await coordinator.run_round(state)
        return updates
    except Exception as e:
        return {"error": str(e)}
