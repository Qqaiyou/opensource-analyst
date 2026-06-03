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
main.py          — FastAPI app entry (/, /health endpoints)
api/             — REST API route definitions (M5)
agents/          — Expert Agent implementations (one per file)
  ├── base.py    — BaseAgent (LLM wrapper) + Analyzer
graph/           — LangGraph StateGraph definition, nodes, edges (M6)
rag/             — Repository RAG retrieval logic (M4)
github/          — GitHub API client
  ├── client.py  — GitHubClient (auth, requests, URL parsing, exceptions)
  ├── readme.py  — ReadmeFetcher
  └── parser.py  — RepoParser (file tree + language stats)
mcp/             — MCP server integration (M11)
prompts/         — LLM prompt templates
  └── overview.py — Project overview + tech stack analysis prompt
vectorstore/     — ChromaDB wrapper and indexing logic (M4)
models/          — Pydantic models (no raw dict returns)
  ├── repo.py    — RepoInfo (owner, repo, readme, file_tree, languages)
  └── analysis.py — AnalysisResult, ProjectOverview, TechStack, Dependency
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
[Current — M5]
POST /analyze → BackgroundTasks → GitHubClient + Analyzer → AnalysisResult
GET /task/{id} → status polling → GET /task/{id}/result

[Next — M6]
LangGraph StateGraph: LoadRepo → Analyze → Architecture → Learning

[Future — M10+]
[Coordinator Agent]
  ├── RepoAgent        — GitHub data fetching
  ├── DependencyAgent  — tech stack / dependency analysis
  ├── ArchitectureAgent — project structure & module analysis
  └── LearningAgent    — learning path & interview questions
```

### LangGraph Workflow (Milestone 6 ✅)

```
GraphState (repo_url, repo_info, overview, tech_stack, architecture, learning_path, error)

load_repo → analyze → architecture → learning → END
```

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
| M6 | ⏳ | LangGraph workflow (StateGraph) |
| M7 | ⏳ | Dependency Agent |
| M8 | ⏳ | Architecture Agent |
| M9 | ⏳ | Learning Agent |
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
