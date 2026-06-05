# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenSource Analyst Agent — a LangGraph + Multi-Agent + MCP + Repository RAG + FastAPI platform that analyzes GitHub repositories. Given a repo URL, it produces: project overview, tech stack analysis, architecture analysis, learning path, interview knowledge points, and source code reading suggestions.

Development follows strict milestone sequencing (M0→M12) and a "Design First, Implementation Second" methodology — never skip phases.

## Essential Commands

```bash
# Start dev server (hot-reload)
uv run uvicorn src.opensource_analyst.main:app --reload

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_github.py -v

# Run a single test function
uv run pytest tests/test_github.py::test_fetch_readme -v

# Add a dependency
uv add <package-name>

# Activate uv path (if needed)
$env:Path = "C:\Users\Administrator\.local\bin;$env:Path"
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.14, uv |
| Web | FastAPI, Uvicorn, Pydantic |
| LLM/Agent | LangChain, LangChain-OpenAI, LangGraph 1.2+, DeepSeek API |
| Embedding | DashScope text-embedding-v3 (1024 dim, OpenAI Compatible) |
| Vector DB | ChromaDB 1.5+ (M4) |
| HTTP | HTTPX 0.28+ |
| Testing | pytest 9.0+, pytest-asyncio |
| Env | python-dotenv (.env auto-load) |

## Architecture

Package root: `src/opensource_analyst/`

```
main.py          — FastAPI app entry (/, /health, routers)
api/             — REST API route definitions (M5+)
  ├── analyze.py — POST /analyze (start analysis, background task)
  ├── task.py    — GET /task/{id}, GET /task/{id}/result
  └── chat.py    — POST /chat (RAG Q&A over indexed code)
agents/          — Expert Agent implementations (one per file)
  ├── base.py           — BaseAgent (LLM wrapper) + Analyzer
  ├── dependency.py     — DependencyAgent (M7: dep file parsing + LLM classification)
  ├── architecture.py   — ArchitectureAgent (M8: module grouping + import analysis + LLM report)
  ├── learning.py       — LearningAgent (M9: synthesis of all analyses + LLM learning path)
  ├── registry.py       — AgentRegistry + AgentSpec (M10: Agent registration + ready/done detection)
  └── coordinator.py    — CoordinatorAgent (M10: parallel dispatch via asyncio.gather + fault isolation)
graph/           — LangGraph StateGraph definition, nodes, edges (M6, M10 refactored)
  ├── state.py   — GraphState (11 fields: repo_url, repo_info, code_indexed, rag_context, parsed_dependencies, dependencies, overview, tech_stack, architecture, learning_path, error)
  ├── nodes.py   — 8 nodes (load_repo / index_code / retrieve_context / dependency / analyze / architecture / learning / coordinator) + build_analysis_registry()
  └── workflow.py — build_workflow() + export_workflow_mermaid() + coordinator conditional loop
rag/             — Repository RAG retrieval logic (M4)
  ├── indexer.py  — CodeIndexer (file filter → download → chunk → embed → store)
  └── retriever.py — CodeRetriever (semantic search → context assembly)
github/          — GitHub API client
  ├── client.py                 — GitHubClient (auth, requests, URL parsing, exceptions)
  ├── readme.py                 — ReadmeFetcher
  ├── parser.py                 — RepoParser (file tree + language stats)
  ├── dependency_parser.py      — DependencyFileParser (M7: dep file detection + parsing)
  └── architecture_analyzer.py  — ArchitectureAnalyzer (M8: module grouping + AST import + entry file)
mcp/             — MCP server integration (M11)
prompts/         — LLM prompt templates
  ├── overview.py      — Project overview + tech stack analysis prompt
  ├── dependency.py    — Dependency analysis prompt (M7)
  ├── architecture.py  — Architecture analysis prompt (M8)
  ├── learning.py      — Learning path prompt (M9)
  └── chat.py          — RAG Q&A prompt template
vectorstore/     — ChromaDB wrapper and indexing logic (M4)
  └── chroma.py  — DashScopeEmbeddings + VectorStore (CRUD + count)
models/          — Pydantic models (no raw dict returns)
  ├── repo.py    — RepoInfo (owner, repo, readme, file_tree, languages)
  ├── analysis.py — AnalysisResult, ProjectOverview, TechStack, Dependency, ArchitectureResult, ModuleInfo, LearningStep, InterviewPoint, ReadingSuggestion, LearningPath
  ├── task.py     — AnalyzeRequest, TaskStatus, TaskResult
  └── chat.py     — ChatRequest, ChatResponse, SourceInfo
```

### Environment Variables (.env)

```
DEEPSEEK_API_KEY   — DeepSeek API key (loaded via python-dotenv)
GITHUB_TOKEN       — GitHub Personal Access Token (higher API rate limit)
DASH_SCOPE_API_KEY — Alibaba DashScope API key (embedding model)
```

### LLM Configuration

```
Provider: DeepSeek API (OpenAI Compatible)
Model: deepseek-chat
Base URL: https://api.deepseek.com/v1
SDK: ChatOpenAI (LangChain-OpenAI)
Temperature: 0.3
```

### Agent Pipeline (current → future)

```
[Current — M10]
POST /analyze → BackgroundTasks → LangGraph Workflow → AnalysisResult
  Pipeline: load_repo → index_code → retrieve_context → coordinator ⇄ END
  Coordinator: asyncio.gather(dependency, architecture, analyze) → learning
GET /task/{id} → status polling → GET /task/{id}/result
POST /chat → RAG 检索 + DeepSeek → 答案 + 代码引用来源

[Future — M10+]
[Coordinator Agent]
  ├── RepoAgent        — GitHub data fetching
  ├── DependencyAgent  — tech stack / dependency analysis ✅ (M7)
  ├── ArchitectureAgent — project structure & module analysis ✅ (M8)
  └── LearningAgent    — learning path & interview questions ✅ (M9)
```

### LangGraph Workflow (Milestone 9 ✅)

```
GraphState (11 fields: repo_url, repo_info, code_indexed, rag_context, parsed_dependencies, dependencies, overview, tech_stack, architecture, learning_path, error)

load_repo → index_code → retrieve_context → coordinator ⇄ END
              ↓ error?        ↓ error?       ↓ error?
              END             END            END

coordinator 内部并行调度:
  Round 1: asyncio.gather(dependency, architecture, analyze)
  Round 2: learning
  Round 3: all_done → END
- AgentRegistry 声明式注册 dependencies/produces → 自动发现就绪 Agent 并行执行
- 单 Agent 失败不阻断其他 Agent（独立容错）
```

- index_code: ChromaDB 已有数据则跳过，避免重复索引
- retrieve_context: 用 README 前 500 字符做语义检索，返回 top-10 代码片段
- coordinator: AgentRegistry.get_ready(state) → asyncio.gather 并行调度 → 合并结果

## Development Rules

- **Design First**: every feature begins with a design doc (PRD.md, ARCHITECTURE.md, ROADMAP.md)
- **Type annotations**: all functions must have type hints
- **Pydantic over dicts**: never return bare dictionaries, use Pydantic models
- **Dependency injection**: no large global variables
- **Single responsibility**: one Agent class per file
- **Tests required**: every core module must have tests
- **No cross-phase jumps**: follow the milestone order strictly
- **Git commits in Chinese**: all commit messages must be written in Chinese
- **Environment variables**: secrets in .env (gitignored), template in .env.example

## Milestone Roadmap

| Phase | Status | What |
|-------|--------|------|
| M0 | ✅ | Environment setup (Python, uv, FastAPI, LangGraph, ChromaDB) |
| M1 | ✅ | Design docs (PRD, Architecture, Roadmap) |
| M2 | ✅ | GitHub repository reader (client, readme fetcher, file tree parser) |
| M3 | ✅ | Single-agent analysis (DeepSeek API, Analyzer, overview + tech stack) |
| M4 | ✅ | Repository RAG (ChromaDB indexing + semantic search) |
| M5 | ✅ | FastAPI API refinement (async tasks, /analyze endpoint) |
| M6 | ✅ | LangGraph workflow (StateGraph, 6 nodes, RAG integration, error routing, Mermaid export, /chat API) |
| M7 | ✅ | Dependency Agent |
| M8 | ✅ | Architecture Agent |
| M9 | ✅ | Learning Agent |
| M10 | ⏳ | Coordinator Agent (multi-agent orchestration) |
| M11 | ⏳ | MCP integration (GitHub, Filesystem, Browser) |
| M12 | ⏳ | Advanced features (Mermaid, Interview Agent, Reflection) |

## Key Design Docs

- `docs/PRD.md` — product requirements (user personas, features, I/O spec)
- `docs/ARCHITECTURE.md` — system architecture (5-layer design, Agent system, data flow)
- `docs/ROADMAP.md` — development roadmap (dependencies, risks, milestones)
- `opensource_analyst_mentor.md` — development methodology and coding rules
- `PROJECT_STATUS.md` — current progress tracking (updated each milestone)

## Test Targets

| Project | URL | Used In |
|---------|-----|---------|
| TinyDB | https://github.com/msiemens/tinydb | M2-M5 integration tests |

## Git History

```
f8f41a0 fix: 修复 M5 遗留问题并更新项目状态 — 修复代理连接失败、统一导入路径
ed36db1 feat: 完成 Milestone 5 — FastAPI 接口完善
35f7edc feat: 完成 Milestone 4 — Repository RAG
b77202c feat: 完成 Milestone 3 — 单 Agent 分析
aa6bcdf feat: 完成 Milestone 2 — GitHub 仓库读取
1b90124 chore: 完成 Milestone 1 — 项目设计文档
45539df chore: 初始化项目结构和依赖
40e9325 init project
```
