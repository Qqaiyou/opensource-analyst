# OpenSource Analyst - 项目进度跟踪

> 最后更新：2026-06-02
> 当前阶段：Milestone 3 ✅ 已完成 | 下一阶段：Milestone 4

---

## 一、项目概述

**项目名称**：OpenSource Analyst Agent

**技术栈**：LangGraph + Multi-Agent + MCP + Repository RAG + FastAPI

**目标**：输入 GitHub 仓库 URL，输出项目概览、技术栈分析、架构分析、学习路线、面试知识点

---

## 二、Milestone 进度

| 阶段 | 名称 | 状态 | 完成日期 | 提交哈希 |
|------|------|------|----------|----------|
| M0 | 环境搭建 | ✅ 已完成 | 2026-06-01 | `45539df` |
| M1 | 项目设计 | ✅ 已完成 | 2026-06-02 | - |
| M2 | GitHub 仓库读取 | ✅ 已完成 | 2026-06-02 | - |
| M3 | 单 Agent 分析 | ✅ 已完成 | 2026-06-02 | - |
| M4 | Repository RAG | ⏳ 待开始 | - | - |
| M5 | FastAPI 接口 | ⏳ 待开始 | - | - |
| M6 | LangGraph 工作流 | ⏳ 待开始 | - | - |
| M7 | Dependency Agent | ⏳ 待开始 | - | - |
| M8 | Architecture Agent | ⏳ 待开始 | - | - |
| M9 | Learning Agent | ⏳ 待开始 | - | - |
| M10 | Coordinator Agent | ⏳ 待开始 | - | - |
| M11 | MCP 集成 | ⏳ 待开始 | - | - |
| M12 | 高级功能 | ⏳ 待开始 | - | - |

---

## 三、Milestone 0 完成详情

### 3.1 环境信息

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | 3.14.0 | 运行环境 |
| uv | 0.11.17 | 包管理器 |
| Git | 2.53.0 | 版本控制 |
| FastAPI | 0.136.3 | Web 框架 |
| Uvicorn | 0.48.0 | ASGI 服务器 |
| Pydantic | 2.13.4 | 数据验证 |
| LangGraph | 1.2.2 | Agent 工作流 |
| LangChain | 1.3.2 | LLM 框架 |
| LangChain-OpenAI | 1.2.2 | OpenAI 集成 |
| ChromaDB | 1.5.9 | 向量数据库 |
| HTTPX | 0.28.1 | HTTP 客户端 |

### 3.2 目录结构

```
opensource-analyst/
├── .venv/                          # uv 虚拟环境
├── .python-version                 # Python 3.14
├── pyproject.toml                  # 项目配置 + 依赖
├── uv.lock                         # 依赖锁定
├── README.md
├── Milestone.md                    # 路线图（原始规划）
├── opensource_analyst_mentor.md    # 开发规范
├── PROJECT_STATUS.md               # 本文件：进度跟踪
├── docs/                           # 设计文档（M1 产出目录）
├── src/opensource_analyst/
│   ├── __init__.py                 # 版本 0.1.0
│   ├── main.py                     # FastAPI 入口
│   ├── api/                        # REST API 路由
│   ├── agents/                     # Agent 实现
│   ├── graph/                      # LangGraph 工作流
│   ├── rag/                        # RAG 检索
│   ├── github/                     # GitHub 读取
│   ├── mcp/                        # MCP 集成
│   ├── prompts/                    # 提示词模板
│   ├── vectorstore/                # 向量存储
│   └── models/                     # Pydantic 模型
└── tests/                          # 测试用例
```

### 3.3 已验证功能

```bash
# 启动命令
uv run uvicorn src.opensource_analyst.main:app --host 127.0.0.1 --port 8000

# 验证端点
GET /     → {"message": "OpenSource Analyst is running!"}
GET /health → {"status": "ok"}
GET /docs → Swagger UI 自动生成
```

### 3.4 Git 提交历史

```
45539df chore: setup project structure and dependencies
40e9325 init project
```

---

## 四、Milestone 1 完成详情

### 4.1 产出文档

| 文档 | 路径 | 内容 |
|------|------|------|
| PRD.md | `docs/PRD.md` | 产品需求文档 — 5 种用户画像、功能边界、输入输出定义、验收标准 |
| ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 架构设计文档 — 5 层架构图、Agent 关系、LangGraph 工作流、RAG 流水线、MCP 集成、API 设计、数据流全链路 |
| ROADMAP.md | `docs/ROADMAP.md` | 开发路线图 — 13 个里程碑总览、依赖关系图、分阶段计划、技术选型、风险矩阵、验收标准 |

### 4.2 关键设计决策

- **LLM 提供商**：OpenAI Compatible API，通过 `base_url` 切换（ChatOpenAI）
- **向量数据库**：ChromaDB（MVP），后续可升级 PostgreSQL + pgvector
- **Agent 架构**：Coordinator + 4 Expert Agent（Repo / Dependency / Architecture / Learning）
- **工作流引擎**：LangGraph StateGraph，M6 顺序执行，M10 升级为动态并行路由
- **异步方案**：MVP 用 asyncio + 内存队列，后续可升级 Celery/Redis

### 4.3 已确认事项（M2 就绪）

- [x] **LLM API Key**：DeepSeek API Key，环境变量 `DEEPSEEK_API_KEY`，通过 `ChatOpenAI(base_url="https://api.deepseek.com/v1")` 兼容接入
- [x] **GitHub Token**：用 `gh` CLI 获取（`gh auth token`），或去 GitHub Settings → Developer settings → Personal access tokens 查看
- [x] **M2 测试目标**：[TinyDB](https://github.com/msiemens/tinydb)（Python 轻量数据库）

---

## 五、Milestone 2 完成详情

### 5.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| GitHubClient | `src/opensource_analyst/github/client.py` | 异步 HTTP 客户端 + URL 解析 + 3 种异常类 + `.env` 自动加载 |
| ReadmeFetcher | `src/opensource_analyst/github/readme.py` | README 获取 + base64 解码 |
| RepoParser | `src/opensource_analyst/github/parser.py` | 文件树获取（自适应默认分支） + 语言统计 |
| RepoInfo | `src/opensource_analyst/models/repo.py` | Pydantic 数据模型 |
| 测试 | `tests/test_github.py` | 9 个测试用例（4 单元 + 5 集成）|
| 环境变量模板 | `.env.example` | DEEPSEEK_API_KEY + GITHUB_TOKEN |
| 环境变量 | `.env` | 真实 Key（已 gitignore）|

### 5.2 测试结果

```
9 passed in 9.90s
  - 4 单元测试：URL 解析（含边界情况：尾部斜杠、非 GitHub 域名、缺少 repo）
  - 5 集成测试：对 TinyDB 真实请求（README / 文件树 / 语言 / 404 异常 / 全链路）
```

### 5.3 技术要点

- GitHub API 自适应默认分支（TinyDB 用 `master`，LangGraph 用 `main`）
- `.env` 自动加载 + `.gitignore` 防护
- 异步全链路：httpx.AsyncClient + async with 上下文管理器
- 异常分层：`GitHubAPIError` → `RepoNotFoundError` / `RateLimitError`

---

## 六、Milestone 3 完成详情

### 6.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| BaseAgent | `src/opensource_analyst/agents/base.py` | LLM 调用基类 + ChatOpenAI 封装 + JSON 解析 + Analyzer |
| OverviewPrompt | `src/opensource_analyst/prompts/overview.py` | 项目概览 + 技术栈分析 prompt 模板 |
| AnalysisResult | `src/opensource_analyst/models/analysis.py` | 输出模型（AnalysisResult / ProjectOverview / TechStack / Dependency）|
| 测试 | `tests/test_agent.py` | 4 个集成测试（类型 / 概览 / 技术栈 / 依赖）|

### 6.2 测试结果

```
13 passed in 22.92s
  M2: 9 tests (4 unit + 5 integration)
  M3: 4 tests (4 integration — 真实调用 DeepSeek API)
```

### 6.3 真实分析输出（TinyDB）

```json
{
  "overview": {
    "name": "TinyDB",
    "description": "轻量级纯 Python 文档数据库，无外部依赖...",
    "use_cases": ["小型应用本地存储", "原型开发", "嵌入式数据管理"],
    "license": "MIT"
  },
  "tech_stack": {
    "languages": {"Python": "约 98.6%", "Makefile": "约 1.4%"},
    "frameworks": [],
    "key_dependencies": []
  }
}
```

### 6.4 技术要点

- DeepSeek API 通过 `ChatOpenAI(base_url="https://api.deepseek.com/v1")` 兼容接入
- `DEEPSEEK_API_KEY` 从 `.env` 自动加载（`python-dotenv`）
- `_invoke_json()` 内置容错：自动去掉 markdown 代码块、提取 JSON 边界
- Prompt 中 JSON 示例花括号用 `{{ }}` 转义，避免与 `str.format()` 冲突
- 低温度（0.3）保证输出稳定

---

## 七、快速启动命令

```bash
# 进入项目目录
cd c:\Users\Administrator\Desktop\myproject

# 确保 uv 在 PATH
$env:Path = "C:\Users\Administrator\.local\bin;$env:Path"

# 启动开发服务器
uv run uvicorn src.opensource_analyst.main:app --reload

# 运行测试
uv run pytest

# 添加新依赖
uv add <package-name>
```

---

## 八、开发规范速查

- **设计优先**：每个功能先输出设计文档，确认后再编码
- **类型完整**：所有函数使用类型注解
- **Pydantic**：禁止返回裸字典，使用 Pydantic 模型
- **依赖注入**：禁止大量全局变量
- **单一职责**：一个 Agent 一个文件
- **编写测试**：每个核心模块必须有测试

---

*本文件由 AI 维护，每次里程碑完成后更新。*
