# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenSource Analyst Agent — a LangGraph + Multi-Agent + MCP + Repository RAG + FastAPI platform that analyzes GitHub repositories. Given a repo URL, it produces: project overview, tech stack analysis, architecture analysis, learning path, interview knowledge points, and source code reading suggestions.

Development follows strict milestone sequencing (M0→M13) and a "Design First, Implementation Second" methodology — never skip phases.

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
main.py          — FastAPI app entry (/, /health, /dashboard, routers)
api/             — REST API route definitions (M5+)
  ├── analyze.py      — POST /analyze (start analysis, background task)
  ├── task.py         — GET /task/{id}, GET /task/{id}/result
  ├── chat.py         — POST /chat (RAG Q&A over indexed code)
  ├── conversation.py — POST /conversation/start, /{id}/message, /{id}/stream, /{id}/history (M13: ReAct对话)
  └── session.py      — ConversationSessionStore (M13: 内存会话管理)
agents/          — Expert Agent implementations (one per file)
  ├── base.py           — BaseAgent (LLM wrapper) + Analyzer
  ├── dependency.py     — DependencyAgent (M7: dep file parsing + LLM classification)
  ├── architecture.py   — ArchitectureAgent (M8: module grouping + import analysis + LLM report)
  ├── learning.py       — LearningAgent (M9: synthesis of all analyses + LLM learning path)
  ├── interview.py      — InterviewAgent (M12: 四级面试题生成)
  ├── reflection.py     — ReflectionAgent (M12: 四维度质量自检)
  ├── registry.py       — AgentRegistry + AgentSpec (M10: Agent registration + ready/done detection)
  ├── coordinator.py    — CoordinatorAgent (M10: parallel dispatch via asyncio.gather + fault isolation)
  └── react_agent.py    — ReactAgent (M13: ReAct 对话 Agent, tool calling)
graph/           — LangGraph StateGraph definition, nodes, edges (M6+)
  ├── state.py              — GraphState (15 fields for analysis pipeline)
  ├── nodes.py              — 11 nodes + build_analysis_registry() (7 Agent 注册)
  ├── workflow.py           — build_workflow() + export_workflow_mermaid() + coordinator loop
  ├── conversation.py       — build_conversation_graph() (M13: ReAct call_model ⇄ tool_node)
  └── conversation_state.py — ConversationState (M13: messages + add_messages reducer)
rag/             — Repository RAG retrieval logic (M4)
  ├── indexer.py  — CodeIndexer (file filter → download → chunk → embed → store)
  └── retriever.py — CodeRetriever (semantic search → context assembly)
github/          — GitHub API client
  ├── client.py                 — GitHubClient (auth, requests, URL parsing, exceptions)
  ├── readme.py                 — ReadmeFetcher
  ├── parser.py                 — RepoParser (file tree + language stats)
  ├── dependency_parser.py      — DependencyFileParser (M7: dep file detection + parsing)
  └── architecture_analyzer.py  — ArchitectureAnalyzer (M8: module grouping + AST import + entry file)
mcp/             — MCP server integration (M11+)
  ├── __init__.py    — Public API exports
  ├── config.py      — MCPServerConfig + MCPToolInfo + MCPToolResult
  ├── client.py      — MCPServerConnection + MCPClientManager (stdio transport)
  └── tool_bridge.py — build_mcp_tools() (M13: MCP → LangChain StructuredTool)
analysis/        — Static analysis utilities (M12)
  ├── __init__.py
  └── mermaid.py — build_all_mermaid() — 三种 Mermaid 图生成
prompts/         — LLM prompt templates
  ├── overview.py      — Project overview + tech stack analysis prompt
  ├── dependency.py    — Dependency analysis prompt (M7)
  ├── architecture.py  — Architecture analysis prompt (M8)
  ├── learning.py      — Learning path prompt (M9)
  ├── interview.py     — Interview question prompt (M12)
  ├── reflection.py    — Self-reflection prompt (M12)
  ├── conversation.py  — ReAct conversation system prompt (M13)
  └── chat.py          — RAG Q&A prompt template
frontend/        — Static web UI (M13)
  └── index.html — Interactive chat frontend (analysis report cards + reasoning timeline + SSE + Mermaid)
vectorstore/     — ChromaDB wrapper and indexing logic (M4)
  └── chroma.py  — DashScopeEmbeddings + VectorStore (CRUD + count)
models/          — Pydantic models (no raw dict returns)
  ├── repo.py         — RepoInfo (owner, repo, readme, file_tree, languages)
  ├── analysis.py     — AnalysisResult + 15 analysis models
  ├── task.py         — AnalyzeRequest, TaskStatus, TaskResult
  ├── chat.py         — ChatRequest, ChatResponse, SourceInfo
  └── conversation.py — Conversation models (M13)
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

### Agent Pipeline (M13)

```
POST /analyze → BackgroundTasks → LangGraph Workflow → AnalysisResult
  Pipeline: load_repo → index_code → retrieve_context → coordinator ⇄ END
  Coordinator: asyncio.gather(dependency, architecture, analyze) → learning → mermaid → interview → reflection
GET /task/{id} → status polling → GET /task/{id}/result
POST /chat → RAG 检索 + DeepSeek → 答案 + 代码引用来源

M13: Interactive Conversation
POST /conversation/start → 基于已完成的 task_id 加载分析结果 → 创建会话
POST /conversation/{id}/message → ReAct Agent (search_code + MCP tools) → 回答 + 推理步骤
GET /conversation/{id}/stream → SSE 流式输出 (token + tool events)

MCP 能力层: MCPServerConnection + MCPClientManager → stdio transport 连接外部 MCP Server
MCP → LangChain Tool Bridge: build_mcp_tools() 将 MCP 工具动态注入 ReAct Agent 的可用工具集
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
| M10 | ✅ | Coordinator Agent (multi-agent orchestration) |
| M11 | ✅ | MCP integration (GitHub, Filesystem, Browser) |
| M12 | ✅ | Advanced features (Mermaid, Interview Agent, Reflection) |
| M13 | ✅ | Interactive Conversation (ReAct Agent + RAG + MCP + Chat UI) |

## Key Design Docs

- `docs/PRD.md` — product requirements (user personas, features, I/O spec)
- `docs/ARCHITECTURE.md` — system architecture (5-layer design, Agent system, data flow)
- `docs/ROADMAP.md` — development roadmap (dependencies, risks, milestones)
- `opensource_analyst_mentor.md` — development methodology and coding rules
- `PROJECT_STATUS.md` — current progress tracking (updated each milestone)

## Test Targets

| Project | URL | Used In |
|---------|-----|---------|
| TinyDB | https://github.com/msiemens/tinydb | M2-M13 integration tests |

## Git History

```
18c6f0c feat: 前端重写 — 格式化分析报告卡片 + 推理时间线可视化
586a824 fix: add_messages reducer (Annotated) + 跳过失败回复防止 tool message 顺序错误
ee251e1 fix: M13 — 日志级别 DEBUG + session 调试输出 + 前端重写
c778d10 fix: 重写前端 chat UI — 分析报告显示 + 错误处理增强
4c3d6a4 fix: ReactAgent.react() 添加消息数 + 工具数日志
e4c5178 fix: send_message 添加历史消息日志 + 调试多轮对话
ff676d4 feat: 完成 Milestone 13 — 交互式对话 (ReAct Agent + 前端)
dc6beaf feat: 完成 Milestone 12 — Mermaid图/Interview Agent/Reflection Agent
a240477 feat: 完成 Milestone 11 — MCP 集成能力层
ecb4876 feat: 完成 Milestone 10 — Coordinator Agent
f834a1b feat: 完成 Milestone 9 — Learning Agent
4f21132 feat: 完成 Milestone 8 — Architecture Agent
5a76611 feat: 完成 Milestone 7 — Dependency Agent
3b58389 feat: 完成 Milestone 6 — LangGraph 工作流
ed36db1 feat: 完成 Milestone 5 — FastAPI 接口完善
35f7edc feat: 完成 Milestone 4 — Repository RAG
b77202c feat: 完成 Milestone 3 — 单 Agent 分析
aa6bcdf feat: 完成 Milestone 2 — GitHub 仓库读取
```
