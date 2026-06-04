# OpenSource Analyst — 开发笔记

> 记录每个里程碑的 Step 1-5 内容，便于复盘。

---

## Milestone 0 — 环境搭建

### Step 1: 概念讲解

- **Python 虚拟环境**：用 `uv` 创建隔离的 Python 运行环境（`.venv/`），避免全局依赖污染
- **uv**：Rust 写的极速 Python 包管理器，替代 pip + venv，支持 `uv add`、`uv run`、`uv lock`
- **FastAPI**：Python 异步 Web 框架，自动生成 Swagger 文档，性能接近 Node.js
- **Uvicorn**：ASGI 服务器，运行 FastAPI 应用（类似 Tomcat 之于 Java）
- **pyproject.toml**：Python 项目的标准配置文件（替代 requirements.txt + setup.py）

### Step 2: 在项目中的作用

整个项目的基石。后续所有模块（GitHub、Agent、RAG、API）都运行在这个环境之上。

### Step 3: 设计方案

目录结构：
```
opensource-analyst/
├── .venv/              # 虚拟环境
├── .python-version      # 锁定 Python 3.14
├── pyproject.toml       # 项目配置 + 依赖
├── uv.lock             # 依赖锁定文件
├── README.md
├── src/opensource_analyst/
│   ├── __init__.py     # 版本 0.1.0
│   └── main.py         # FastAPI 入口
└── tests/
```

依赖清单：fastapi, uvicorn, pydantic, langgraph, langchain, langchain-openai, chromadb, httpx

### Step 4: 代码产出

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `pyproject.toml` | 新建 | 项目元数据 + 全部依赖声明 |
| `.python-version` | 新建 | 锁定 Python 3.14 |
| `src/opensource_analyst/__init__.py` | 新建 | 版本号 0.1.0 |
| `src/opensource_analyst/main.py` | 新建 | FastAPI 应用入口，注册 `/` 和 `/health` 路由 |
| `.gitignore` | 新建 | 忽略 .venv、.env、__pycache__ |

### Step 5: 验收标准

```bash
# 启动服务
uv run uvicorn src.opensource_analyst.main:app --host 127.0.0.1 --port 8000

# 验证端点
curl http://localhost:8000/       # → {"message":"OpenSource Analyst is running!"}
curl http://localhost:8000/health  # → {"status":"ok"}
# 浏览器访问 http://localhost:8000/docs → Swagger UI
```

---

## Milestone 1 — 项目设计

### Step 1: 概念讲解

- **PRD（产品需求文档）**：定义"做什么"——用户是谁、解决什么问题、输入输出是什么
- **ARCHITECTURE（架构文档）**：定义"怎么做"——系统分层、模块关系、数据流
- **ROADMAP（路线图）**：定义"分几步走"——里程碑拆解、依赖关系、风险矩阵
- **设计优先原则**：先写清楚再编码，避免"边写边想"导致的返工

### Step 2: 在项目中的作用

M1 是"图纸"。13 个里程碑的复杂项目如果没有设计文档，后面会频繁推倒重来。架构文档中的分层图、Agent 关系图、工作流图是整个开发的"北极星"。

### Step 3: 设计方案

三份文档的定位：
- **PRD.md**：5 种用户画像、功能边界、输入输出 JSON Schema、验收标准
- **ARCHITECTURE.md**：5 层架构（API → 编排 → Agent → 能力 → 数据）、Agent 通信机制、LangGraph 工作流设计、RAG 流水线、MCP 集成方案
- **ROADMAP.md**：13 个里程碑总览、依赖关系图、4 个开发阶段、技术选型、风险矩阵

### Step 4: 代码产出

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `docs/PRD.md` | 新建 | ~210 行，5 种用户画像 + 功能列表 + I/O JSON Schema |
| `docs/ARCHITECTURE.md` | 新建 | ~380 行，5 层架构 + Agent 系统 + LangGraph 工作流 + RAG + MCP |
| `docs/ROADMAP.md` | 新建 | ~230 行，13 里程碑 + 依赖树 + 技术选型 + 风险矩阵 |

### Step 5: 验收标准

- 三份文档完整可读
- 架构图能解释"整个系统怎么工作"
- 确认了 LLM 方案（DeepSeek API）、GitHub Token、M2 测试目标（TinyDB）

---

## Milestone 2 — GitHub 仓库读取

### Step 1: 概念讲解

- **GitHub REST API**：`GET /repos/{owner}/{repo}` 获取仓库信息，`/readme` 获取 README（base64 编码），`/git/trees/{branch}?recursive=1` 获取文件树，`/languages` 获取语言统计
- **httpx**：Python 异步 HTTP 客户端（类似 requests 但支持 async/await）
- **async/await**：Python 异步编程核心语法，`async with` 用于需要异步初始化和清理的资源
- **python-dotenv**：从 `.env` 文件自动加载环境变量到 `os.getenv()`
- **自定义异常层级**：`GitHubAPIError` → `RepoNotFoundError` (404) / `RateLimitError` (403 rate limit)

### Step 2: 在项目中的作用

M2 是数据获取层。所有后续 Agent 分析都依赖它提供原始数据（README + 文件树 + 语言统计）。

### Step 3: 设计方案

4 个类：
- **GitHubClient**：异步 HTTP 客户端，认证头、URL 解析、错误处理
- **ReadmeFetcher**：获取 README API → base64 解码 → Markdown 字符串
- **RepoParser**：获取文件树（自适应默认分支 master/main）+ 语言统计
- **RepoInfo**：Pydantic 数据模型，组合所有仓库信息

```
用户 URL → GitHubClient.parse_url() → (owner, repo)
  → ReadmeFetcher.fetch_readme()    → Markdown
  → RepoParser.fetch_file_tree()    → list[str]
  → RepoParser.fetch_languages()    → dict[str, int]
  → RepoInfo(owner, repo, readme, file_tree, languages)
```

### Step 4: 代码产出

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/opensource_analyst/github/client.py` | 新建 | GitHubClient 类：异步 httpx 客户端 + parse_url() + _request() + 3 种异常类 |
| `src/opensource_analyst/github/readme.py` | 新建 | ReadmeFetcher 类：fetch_readme() → base64 解码 |
| `src/opensource_analyst/github/parser.py` | 新建 | RepoParser 类：fetch_file_tree() + fetch_languages()，自适应默认分支 |
| `src/opensource_analyst/models/repo.py` | 新建 | RepoInfo Pydantic 模型 |
| `tests/test_github.py` | 新建 | 9 个测试（4 单元 + 5 集成），测试目标 TinyDB |
| `.env.example` | 新建 | DEEPSEEK_API_KEY + GITHUB_TOKEN 模板 |
| `.env` | 新建 | 真实 Key（gitignored） |

**关键技术点：**
- `parse_url()` 处理尾部斜杠、`.git` 后缀、非 GitHub 域名校验
- `fetch_file_tree()` 先查 `/repos/{owner}/{repo}` 取 `default_branch`，避免硬编码 `main`
- `_request()` 中 404 → RepoNotFoundError，403+rate limit → RateLimitError
- `load_dotenv()` 模块级调用，自动加载 .env

### Step 5: 验收标准

```bash
uv run pytest tests/test_github.py -v
# 预期：9 passed
#   - 4 单元：URL 解析（有效/尾部斜杠/非GitHub域名/路径过短）
#   - 5 集成：README/文件树/语言统计/404异常/全链路
```

---

## Milestone 3 — 单 Agent 分析

### Step 1: 概念讲解

- **LLM（大语言模型）**：接收文本输入（Prompt），生成文本输出（Completion）。本项目的"大脑"
- **LangChain**：LLM 应用框架，统一了不同模型的调用接口（`ChatOpenAI` 可以调用 OpenAI、DeepSeek 等任何兼容 API）
- **Prompt Engineering**：编写结构化的提示词指示 LLM 输出特定格式（如 JSON）
- **Pydantic 模型**：Python 数据校验库，定义字段类型，自动校验和序列化。禁止返回裸字典
- **temperature**：LLM 创造性参数，0.0=确定性, 1.0=高随机性。分析任务用 0.3 保证输出稳定
- **JSON 容错**：LLM 返回的 JSON 可能带有 markdown 代码块（```json），需要 `_invoke_json()` 做清洗

### Step 2: 在项目中的作用

M3 是项目的"第一次价值交付"——输入 GitHub URL，输出有意义的分析结果。后续 M7-M10 的专家 Agent 都基于 M3 的 BaseAgent 扩展。

### Step 3: 设计方案

```
用户 → Analyzer.analyze(RepoInfo)
  → OVERVIEW_PROMPT.format(readme, file_tree, languages)
  → BaseAgent._invoke_json(prompt)
  → ChatOpenAI(base_url="https://api.deepseek.com/v1", model="deepseek-chat")
  → DeepSeek API
  → JSON 清洗（去 markdown 代码块、提取 { } 边界）
  → AnalysisResult(**dict)
```

3 个 Pydantic 模型：
- `Dependency`：name + purpose
- `ProjectOverview`：name + description + use_cases + license
- `TechStack`：languages + frameworks + key_dependencies
- `AnalysisResult`：overview + tech_stack

### Step 4: 代码产出

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/opensource_analyst/agents/base.py` | 新建 | BaseAgent 类（ChatOpenAI 封装 + _invoke + _invoke_json）+ Analyzer 类（analyze 方法） |
| `src/opensource_analyst/prompts/overview.py` | 新建 | OVERVIEW_PROMPT 模板，包含系统角色、输出格式、JSON 示例 |
| `src/opensource_analyst/models/analysis.py` | 新建 | Dependency + ProjectOverview + TechStack + AnalysisResult 四个 Pydantic 模型 |
| `tests/test_agent.py` | 新建 | 4 个集成测试（类型校验/概览字段/技术栈检测/依赖格式） |

**关键技术点：**
- DeepSeek API 通过 `ChatOpenAI(base_url="https://api.deepseek.com/v1")` 兼容接入
- `_invoke_json()` 内置容错：`re.sub` 去 markdown 代码块 + 找第一个 `{` 到最后一个 `}` 边界
- Prompt 中 JSON 示例花括号用 `{{ }}` 转义，避免与 `str.format()` 冲突
- temperature=0.3 保证分析输出稳定

### Step 5: 验收标准

```bash
uv run pytest tests/test_agent.py -v
# 预期：4 passed（真实调用 DeepSeek API）
# 验证点：AnalysisResult 结构完整、overview 字段非空、Python 被检出、dependencies 格式正确
```

---

## Milestone 4 — Repository RAG

### Step 1: 概念讲解

- **RAG（检索增强生成）**：先检索相关代码，再让 LLM 基于检索结果回答。解决"LLM 没见过这个项目代码"的问题
- **Embedding（向量嵌入）**：将文本转化为固定维度的数值向量（如 1024 维），语义相近的文本向量距离也近
- **ChromaDB**：轻量级嵌入式向量数据库，支持本地持久化，Python 原生
- **Text Chunking（文本分块）**：代码文件太长不能直接嵌入，需要切成小块（chunk_size=1000, overlap=200），overlap 保证块边界不丢失上下文
- **Semantic Search（语义搜索）**：用"自然语言"搜索代码，不是关键词匹配

### Step 2: 在项目中的作用

M4 让系统不再只读 README，而是能理解仓库所有代码。后续 Architecture Agent、Learning Agent 都需要搜索代码来回答具体问题。

### Step 3: 设计方案

RAG 流水线：
```
索引阶段：GitHub 下载文件 → RecursiveCharacterTextSplitter 分块 → DashScopeEmbeddings 向量化 → ChromaDB 存储
检索阶段：用户查询 → DashScopeEmbeddings 向量化 → ChromaDB.similarity_search(k=5) → LLM 上下文拼接
```

5 个组件：
- **DashScopeEmbeddings**：LangChain Embeddings 接口适配器，接入百炼 text-embedding-v3
- **VectorStore**：ChromaDB 封装（add_texts / similarity_search / delete_collection）
- **CodeIndexer**：文件过滤 + GitHub raw 下载 + 分块 + 批量索引
- **CodeRetriever**：语义搜索 + LLM 上下文拼接

文件过滤规则：
- 保留：`.py, .js, .ts, .java, .go, .rs, .c, .cpp, .h, .toml, .yaml, .json, .xml, .sql, .css, .html`
- 排除目录：`tests/, docs/, node_modules/, .git/, __pycache__/`
- 排除文件：`.lock, .md, .rst, .txt, Makefile, LICENSE, .gitignore, 图片/图标`
- 限制：单文件 ≤500KB，总数 ≤200 个

### Step 4: 代码产出

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/opensource_analyst/vectorstore/chroma.py` | 新建 | DashScopeEmbeddings（逐条请求 + 3 次重试）+ VectorStore（ChromaDB 封装） |
| `src/opensource_analyst/rag/indexer.py` | 新建 | CodeIndexer：文件过滤 + 异步批量下载 + RecursiveCharacterTextSplitter 分块 + 索引 |
| `src/opensource_analyst/rag/retriever.py` | 新建 | CodeRetriever：similarity_search + search_as_context（格式化拼接） |
| `tests/test_rag.py` | 新建 | 6 个测试（3 单元文件过滤 + 1 单元嵌入维度 + 2 集成索引检索） |

**关键技术点：**
- 自建 `DashScopeEmbeddings` 适配 LangChain Embeddings 接口（base_url: `https://dashscope.aliyuncs.com/compatible-mode/v1`，model: `text-embedding-v3`，1024 维）
- 嵌入请求逐条发送 + 3 次重试解决网络波动
- 分块策略：chunk_size=1000, chunk_overlap=200
- GitHub raw 下载：async 并发，自适应 master/main 分支
- `search_as_context()` 输出格式：🔹 文件路径 + ```code``` 代码块，可直接嵌入 LLM prompt

### Step 5: 验收标准

```bash
uv run pytest tests/test_rag.py -v
# 预期：6 passed
#   - 3 单元：.py 保留 / docs 排除 / .rst 排除
#   - 1 单元：embedding 返回 1024 维向量
#   - 2 集成：TinyDB 索引→搜索→上下文拼接
```

---

## Milestone 5 — FastAPI 接口

### Step 1: 概念讲解

- **REST API**：基于 HTTP 方法的 API 风格。POST=创建资源，GET=查询，资源路径=/analyze、/task/{id}
- **异步任务模式**：用户请求不能等太久（分析一个仓库可能要 30s+），所以先返回 task_id，后台异步执行，用户轮询状态
- **FastAPI BackgroundTasks**：轻量级后台任务执行器，适合 MVP。不需要 Redis/Celery 等独立服务
- **内存存储**：MVP 用 `dict[str, dict]` 存任务状态，进程重启丢失。后续可替换为 Redis
- **HTTP 状态码语义**：202 Accepted（请求已接受但未完成）、404 Not Found（资源不存在）、409 Conflict（资源存在但状态不允许操作）

### Step 2: 在项目中的作用

M5 把 M2-M4 的能力打包成 HTTP API，让外部系统（前端、CLI、其他服务）可以调用。这是从"函数库"到"服务"的关键跃迁。

### Step 3: 设计方案

3 个端点：
```
POST /analyze              请求体：{repo_url: "..."}
  ↓ 校验 URL → 生成 task_id → 202 + task_id → BackgroundTasks 启动后台
  ↓ 后台：status=running → GitHubClient 获取数据 → Analyzer 分析 → status=completed

GET /task/{task_id}         → 200 {task_id, status, repo_url, created_at}
  ↓ status in (pending, running, completed, error)

GET /task/{task_id}/result  → 200 {task_id, status, result}  (completed/error 时)
  ↓ 未完成 → 409, 不存在 → 404
```

3 个 Pydantic 模型：
- `AnalyzeRequest`：repo_url
- `TaskStatus`：task_id + status + repo_url + created_at
- `TaskResult`：task_id + status + result + error

### Step 4: 代码产出

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/opensource_analyst/models/task.py` | 新建 | AnalyzeRequest + TaskStatus + TaskResult 三个模型 |
| `src/opensource_analyst/api/analyze.py` | 新建 | POST /analyze 路由 + _run_analysis 后台协程（M2+M3 全链路） + 内存 _store |
| `src/opensource_analyst/api/task.py` | 新建 | GET /task/{id} + GET /task/{id}/result 两个路由，404/409 异常处理 |
| `src/opensource_analyst/main.py` | 修改 | 注册 analyze_router + task_router |
| `tests/test_api.py` | 新建 | 5 个测试（根路径/健康检查/无效URL 400/全链路端到端/任务不存在 404） |

**后续修复（commit f8f41a0）：**
- `GitHubClient` 添加 `httpx.AsyncHTTPTransport(trust_env=False)` 解决 Windows 系统代理导致连接失败
- `parser.py` / `readme.py` / `test_github.py` 导入路径从 `from src.opensource_analyst.*` 统一为 `from opensource_analyst.*`

### Step 5: 验收标准

```bash
# 启动服务
uv run uvicorn src.opensource_analyst.main:app --reload

# API 端点验证
http://localhost:8000/docs                        # Swagger UI 可见 3 组端点
curl -X POST localhost:8000/analyze               # 无效 URL → 400
  -H "Content-Type: application/json"             #
  -d '{"repo_url":"https://github.com/msiemens/tinydb"}'  # → 202 + task_id
curl localhost:8000/task/{task_id}                # → 200 {status: "completed"}
curl localhost:8000/task/{task_id}/result         # → 200 {overview + tech_stack}

# 全量测试
uv run pytest -v
# 预期：24/24 passed
#   M2: 9 (GitHub 客户端)
#   M3: 4 (Agent 分析)
#   M4: 6 (RAG 索引检索)
#   M5: 5 (API 接口)
```

## Milestone 6 — LangGraph 工作流

### Step 1: 概念讲解

- **LangGraph StateGraph**：LangChain 团队出的 Agent 编排框架。把 AI 应用执行流程建模成**有向图**——每个节点是可执行函数，每条边定义流转方向，State 是节点间共享的字典
- **State（状态）**：贯穿工作流的共享数据对象（TypedDict），每个节点读取自己需要的字段，返回部分更新。LangGraph 用 reducer 合并策略（默认覆盖，可选追加）
- **Node（节点）**：普通 Python 函数，签名 `(state: GraphState, config: RunnableConfig | None = None) -> dict`，返回的 dict 自动合并回 State
- **Edge（边）**：定义执行顺序。`add_edge("A", "B")` 表示 A 完成后执行 B。还有条件边（Conditional Edge）可根据 State 值动态路由
- **编译（Compile）**：`StateGraph.compile()` 返回 Runnable 对象，调用 `app.invoke(initial_state)` 执行全流程
- **RunnableConfig**：LangGraph 传递给每个节点的运行时配置对象，从 `langgraph.types` 导入，设为 `| None = None` 保证节点可独立测试

### Step 2: 在项目中的作用

M6 将 M5 的"线性代码调用"升级为**显式编排图**：

| 问题 | LangGraph 解法 |
|------|---------------|
| 流程藏在调用链里 | StateGraph 显式声明节点和边 |
| 加新步骤需改主流程 | 加 Node + Edge，不碰旧代码 |
| 出错后无法恢复 | State 持久化，可从失败节点重试 |
| 看不到中间状态 | 每个 Node 输出留在 State 里 |

为 M7-M10 的 Multi-Agent 协作打基础——后续只需替换节点内部逻辑，不碰工作流结构。

### Step 3: 设计方案

4 节点顺序流水线：

```
START → load_repo → analyze → architecture → learning → END
          │            │           │             │
     GitHub API     LLM 调用    占位 (M8)    占位 (M9)
```

GraphState 定义（7 字段，repo_url 必填，其余 NotRequired）：

```python
class GraphState(TypedDict):
    repo_url: str                       # 输入
    repo_info: NotRequired[RepoInfo | None]
    overview: NotRequired[ProjectOverview | None]
    tech_stack: NotRequired[TechStack | None]
    architecture: NotRequired[Any]
    learning_path: NotRequired[Any]
    error: NotRequired[str | None]
```

目录结构：

```
src/opensource_analyst/graph/
├── __init__.py     # 模块标记
├── state.py        # NEW — GraphState TypedDict
├── nodes.py        # NEW — 4 个节点函数
└── workflow.py     # NEW — build_workflow() 工厂函数
```

API 集成改造：`_run_analysis()` 从直接调用 GitHubClient + Analyzer 改为 `build_workflow().ainvoke({"repo_url": ...})`。

### Step 4: 代码产出

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/opensource_analyst/graph/state.py` | 新建 | GraphState TypedDict，7 字段，repo_url 必填外全部 NotRequired |
| `src/opensource_analyst/graph/nodes.py` | 新建 | load_repo_node（async，GitHub API）+ analyze_node（LLM）+ architecture_node（占位）+ learning_node（占位） |
| `src/opensource_analyst/graph/workflow.py` | 新建 | build_workflow()：创建 StateGraph → add_node × 4 → add_edge × 4 → set_entry_point → compile() |
| `src/opensource_analyst/api/analyze.py` | 修改 | _run_analysis 改为 LangGraph 调用：`app.ainvoke({"repo_url": ...})` → 从 state 提取 overview + tech_stack |
| `tests/test_graph.py` | 新建 | 7 个测试（2 单元 state 构造 + 3 单元占位节点 + 1 单元编译 + 1 集成全链路） |

**关键技术点：**

- 节点 config 参数类型为 `RunnableConfig | None = None`（从 `langgraph.types` 导入），满足 LangGraph 1.2.x 的类型检查
- 每个节点 `try/except`，异常写入 `state["error"]`，下游节点检查 `state.get("error")` 后跳过（容错设计）
- 占位节点（architecture_node、learning_node）返回 `None`，M8/M9 替换内部逻辑即可
- `asyncio.gather()` 并发请求 README + 文件树 + 语言统计，减少 GitHub API 等待时间
- `GraphState` 使用 `NotRequired`（`from typing_extensions`）而非 `total=False`，允许初始 state 只传 `repo_url`

### Step 5: 验收标准

```bash
# 仅跑 M6 测试
uv run pytest tests/test_graph.py -v
# 预期：7 passed
#   - 2 单元：GraphState 最小/完整字段构造
#   - 3 单元：占位节点行为 + error 跳过
#   - 1 单元：build_workflow 编译验证
#   - 1 集成：TinyDB 全链路 LangGraph 工作流

# 全量测试（确认零回归）
uv run pytest -v
# 预期：31/31 passed
#   M2: 9 + M3: 4 + M4: 6 + M5: 5 + M6: 7

# API 端到端
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/msiemens/tinydb"}'
# → 202 + task_id → 轮询 → completed → result 含 overview + tech_stack
```

### MVP 差距分析（M6 结束时）

M6 完成了 LangGraph 编排骨架，但 6 个分析板块尚未齐备：

| 板块 | 状态 | 负责阶段 |
|------|------|----------|
| overview | ✅ 可用 | M3 |
| tech_stack | ✅ 可用 | M3 |
| dependencies | ❌ 占位 | **M7** |
| architecture | ❌ 占位 | M8 |
| learning_path | ❌ 占位 | M9 |
| interview_points | ❌ 未规划 | M10/M12 |

MVP 完成需继续 M7（Dependency Agent）→ M8（Architecture Agent）→ M9（Learning Agent）。

---

---

## Milestone 7 — Dependency Agent

### Step 1: 概念讲解

- **Dependency Agent（依赖分析 Agent）**：专门解析项目依赖文件的 Agent，从代码仓库的构建文件中提取依赖信息，再用 LLM 做深度解读
- **多语言依赖解析**：不同语言用不同的依赖文件格式。Python 用 `pyproject.toml`（TOML 格式）/ `requirements.txt`（行格式）/ `setup.py`（Python 代码），Node.js 用 `package.json`（JSON），Java 用 `pom.xml`（XML）/ `build.gradle`（Groovy），Go 用 `go.mod`（自定义格式），Rust 用 `Cargo.toml`（TOML）。每种格式需要专门的解析逻辑
- **依赖分类体系**：将依赖分为 5 个类别——`core`（运行时必需）、`dev`（开发工具）、`build`（构建系统）、`test`（测试框架）、`peer`（对等依赖，宿主项目提供）
- **PEP 508**：Python 依赖声明标准格式，如 `requests>=2.28,<3`。需要拆分为 name + version specifier
- **LLM 增强解析**：解析器提取硬数据（name、version），LLM 补充软信息（分类确认、用途说明、生态定位），两者互补

### Step 2: 在项目中的作用

**为什么需要 M7**：M3 的 Analyze 只基于 README 文本猜测技术栈，存在三个问题：
1. README 可能不提某些依赖
2. 无法知道精确的版本约束
3. LLM 凭空推测用途，缺乏证据

M7 从实际依赖文件提取硬数据，再交给 LLM 做语义解读，实现"数据驱动 + 智能增强"。

**输入**：`RepoInfo.file_tree`（文件路径列表）
**输出**：`list[Dependency]`，每条含 name / version / category / purpose

**在工作流中的位置**：
```
retrieve_context → dependency（← M7 新增） → analyze
                                ↓
                  dependency_node 产出写入 GraphState
                  analyze_node 读取并注入 prompt
```

### Step 3: 设计方案

#### 模块结构

```
新增 4 文件 + 修改 8 文件 = 12 个文件变更
```

| 文件 | 类型 | 说明 |
|------|------|------|
| `github/dependency_parser.py` | 新增 | DependencyFileParser：检测 + 下载 + 解析（8种格式） |
| `agents/dependency.py` | 新增 | DependencyAgent：LLM 分类 + 用途解读 |
| `prompts/dependency.py` | 新增 | DEPENDENCY_ANALYSIS_PROMPT 模板 |
| `tests/test_dependency.py` | 新增 | 12 个测试（9 单元 + 2 集成 + 1 模型） |
| `models/analysis.py` | 修改 | Dependency 新增 version、category 字段 |
| `graph/state.py` | 修改 | 新增 parsed_dependencies、dependencies 字段（7→11） |
| `graph/nodes.py` | 修改 | 新增 dependency_node |
| `graph/workflow.py` | 修改 | 插入 dependency 节点 + 条件边 |
| `prompts/overview.py` | 修改 | 新增 {dependencies} 占位符 |
| `agents/base.py` | 修改 | Analyzer.analyze() 新增 dependencies 参数 |
| `CLAUDE.md` | 修改 | 更新架构图 |
| `PROJECT_STATUS.md` | 修改 | M7 完成记录 |

#### DependencyFileParser 类设计

```python
class DependencyFileParser:
    # 类方法：文件检测
    detect_dep_files(file_tree: list[str]) -> list[str]  # 静态方法，匹配根目录下的已知文件名

    # 实例方法：下载 + 解析
    fetch_and_parse(owner, repo, dep_files, token?) -> list[ParsedDependency]  # async
    _fetch_file(client, owner, repo, path, headers) -> str | None              # 从 GitHub raw 下载

    # 静态方法：各类解析器
    parse_pyproject_toml(content, filename) -> list[ParsedDependency]   # TOML: [project.dependencies] + [project.optional-dependencies] + [build-system]
    parse_setup_cfg(content, filename) -> list[ParsedDependency]         # configparser: install_requires
    parse_setup_py(content, filename) -> list[ParsedDependency]          # 正则: install_requires = [...]
    parse_requirements_txt(content, filename, category) -> list[...]     # 行解析: name==version
    parse_package_json(content, filename) -> list[ParsedDependency]      # JSON: dependencies / devDependencies / peerDependencies
    parse_pom_xml(content, filename) -> list[ParsedDependency]           # XML regex: groupId:artifactId:version + test scope 识别
    parse_gradle(content, filename) -> list[ParsedDependency]            # 正则: implementation / testImplementation / compileOnly
    parse_go_mod(content, filename) -> list[ParsedDependency]            # 行解析: require 块
    parse_cargo_toml(content, filename) -> list[ParsedDependency]        # TOML: [dependencies] / [dev-dependencies] / [build-dependencies]

    # 工具方法
    _split_pep508(dep_str: str) -> tuple[str, str | None]               # PEP 508 拆分: "requests>=2.28" → ("requests", ">=2.28")
```

#### DependencyAgent 类设计

```python
class DependencyAgent(BaseAgent):  # 继承 M3 的 BaseAgent
    def analyze(
        self,
        repo_info: RepoInfo,
        parsed_deps: list[ParsedDependency],
    ) -> list[Dependency]:
        # 1. 构造 prompt：项目名 + README 摘要 + 依赖清单
        # 2. invoke LLM
        # 3. _parse_json_array() 解析 JSON 数组
        # 4. 返回 list[Dependency]
```

#### 数据流

```
file_tree
  → DependencyFileParser.detect_dep_files()
  → [pyproject.toml, ...]
  → fetch_and_parse()
  → [ParsedDependency(name, version, source_file, category)]
  → DependencyAgent.analyze()
  → [Dependency(name, version, category: core/dev/build, purpose)]
  → GraphState.dependencies
  → Analyzer.analyze(dependencies=...)
  → OVERVIEW_PROMPT 注入依赖数据
  → AnalysisResult.tech_stack.key_dependencies（增强版）
```

#### GraphState 扩展

```python
class GraphState(TypedDict):
    repo_url: str
    repo_info: NotRequired[RepoInfo | None]
    code_indexed: NotRequired[int | None]          # M6
    rag_context: NotRequired[str | None]            # M6
    parsed_dependencies: NotRequired[list[dict] | None]  # M7 NEW — parser 原始数据
    dependencies: NotRequired[list[Dependency] | None]   # M7 NEW — LLM 增强结果
    overview: NotRequired[ProjectOverview | None]
    tech_stack: NotRequired[TechStack | None]
    architecture: NotRequired[Any]
    learning_path: NotRequired[Any]
    error: NotRequired[str | None]                  # M6
```

### Step 4: 代码产出

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/opensource_analyst/github/dependency_parser.py` | 新建 | ~400 行：DependencyFileParser（8 种格式检测+解析）+ ParsedDependency 模型 + PEP 508 拆分工具 |
| `src/opensource_analyst/agents/dependency.py` | 新建 | ~85 行：DependencyAgent（LLM 分类+用途解读） |
| `src/opensource_analyst/prompts/dependency.py` | 新建 | ~35 行：DEPENDENCY_ANALYSIS_PROMPT 模板 |
| `tests/test_dependency.py` | 新建 | ~225 行：12 个测试（6 检测 + 3 解析 + 1 模型 + 2 集成 LLM） |
| `src/opensource_analyst/models/analysis.py` | 修改 | Dependency 新增 `version: str | None` + `category: str | None` |
| `src/opensource_analyst/graph/state.py` | 修改 | 新增 `parsed_dependencies` + `dependencies` 字段 |
| `src/opensource_analyst/graph/nodes.py` | 修改 | 新增 `dependency_node`（异步），retrieve_context → analyze 之间 |
| `src/opensource_analyst/graph/workflow.py` | 修改 | 注册 dependency 节点 + 条件边（error→END） |
| `src/opensource_analyst/prompts/overview.py` | 修改 | 新增 `## 依赖分析结果\n{dependencies}` 段落 + JSON 示例更新 |
| `src/opensource_analyst/agents/base.py` | 修改 | Analyzer.analyze() 新增 `dependencies: list[Dependency] | None` 参数 |

**关键技术点：**

- **多语言解析器统一入口**：`_parse_file()` 按文件名分发到 9 个静态解析方法，新增语言只需加一个静态方法
- **PEP 508 拆分**：`_split_pep508()` 用正则 `([a-zA-Z0-9][\w\-.]*)\s*(.*)` 统一处理 Python 依赖字符串，同时支持 `>=`、`==`、`~=`、`^` 等版本约束
- **分类粒度**：Python → 按 TOML section 自动分类（dependencies→core, optional-dev→dev, build-system→build）；Node.js → 按 JSON key（dependencies→core, devDependencies→dev, peerDependencies→peer）；Java → 按 scope（test scope→test）；Rust/Cargo → 按 section key
- **LLM JSON 数组解析**：`_parse_json_array()` 针对数组格式做了专用清洗（去 markdown 代码块 + 提取 `[` `]` 边界）
- **错误短路继承**：dependency_node 完全遵循 M6 的 error→END 模式，上游出错直接跳过
- **向后兼容**：`Analyzer.analyze(dependencies=None)` 默认值保证 M3 的旧测试不破坏；`OVERVIEW_PROMPT` 的 `{dependencies}` 占位符在无数据时填入"（未提供依赖分析数据）"

### Step 5: 验收标准

```bash
# 运行 M7 专项测试
uv run pytest tests/test_dependency.py -v
# 预期：12 passed
#   - 6 检测：pyproject.toml / package.json / pom.xml / go.mod / Cargo.toml / 空列表
#   - 3 解析：pyproject.toml / package.json / requirements.txt
#   - 1 模型：ParsedDependency 字段校验
#   - 2 集成：DependencyAgent 真实 LLM 调用 / 空依赖推断

# 全量回归测试
uv run pytest -v
# 预期：58/58 passed
#   M2: 9 + M3: 4 + M4: 6 + M5: 5 + M6: 16 + chat: 6 + M7: 12

# 验证工作流已包含 dependency 节点
uv run python -c "from opensource_analyst.graph.workflow import export_workflow_mermaid; print(export_workflow_mermaid())"
# 预期：Mermaid 图中出现 "dependency" 节点，位于 retrieve_context 和 analyze 之间
```

---

## Milestone 8 — Architecture Agent

### Step 1: 概念讲解

- **ArchitectureAgent（架构分析 Agent）**：从目录结构、import 关系、入口文件三个维度分析项目架构，用 LLM 生成结构化架构报告
- **静态代码分析**：不运行代码，直接解析源文件提取信息（AST 解析 import 语句、类/函数定义等）。M8 用 Python 标准库 `ast` 模块做轻量级分析
- **模块分组**：将扁平的文件树按目录前缀聚合为逻辑模块。核心算法：跳过已知非源码目录（tests/、docs/、examples/ 等），取前两级目录名作为模块标识
- **AST（抽象语法树）**：Python 源码的树状结构表示，`ast.parse()` 解析代码，`ast.walk()` 遍历所有节点，遇到 `ast.Import` 提取 `import X`，遇到 `ast.ImportFrom` 提取 `from .X import Y`
- **入口文件识别**：按优先级匹配命名模式（`__main__.py` > `main.py` > `app.py` > `server.py` > ...），找不到匹配项则 fallback 到项目内第一个 `.py` 文件
- **架构模式**：常见开源项目架构模式——分层架构（Controller→Service→Repository）、MVC、插件式/中间件架构、管道-过滤器、微内核等
- **模块依赖图**：项目内部模块间的 import 关系构成有向图，图中每个节点是一个模块，边表示依赖方向（如 `tinydb → tinydb.storages`）

### Step 2: 在项目中的作用

**为什么需要 M8**：Milestone.md 将 M8 定义为"项目核心"。因为用户面对陌生项目的第一问题是："我应该从哪里开始读代码？这个项目是怎么组织的？"M8 直接回答这个问题。

M7 告诉你"用了什么技术"，M8 告诉你"这些技术是怎么组织在一起的"。

**输入**：`file_tree` + `RepoInfo` + M7 的依赖分析结果（可选）
**输出**：`ArchitectureResult`，含 architecture_pattern / modules / entry_file / module_relations / architecture_summary

**在工作流中的位置**：
```
dependency → architecture（← M8 占位升级） → analyze → learning
                        ↓
          ArchitectureAnalyzer（静态分析） → ArchitectureAgent（LLM 解读）
          产出 ArchitectureResult 写入 GraphState
```

**影响下游**：
- M9 Learning Agent 需要 architecture 数据来知道"先学哪个模块"
- M12 可用 architecture 数据生成 Mermaid 图

### Step 3: 设计方案

#### 两个新类 + 一个新 Prompt + 一个模型

```
ArchitectureAnalyzer（纯静态，不涉及 LLM）
  ├── group_modules()       — 按目录前缀分组，识别模块边界
  ├── identify_entry_file() — 按命名模式优先级识别入口
  ├── extract_imports()     — AST 解析 import 语句
  ├── is_project_import()   — 过滤标准库/第三方库
  ├── infer_module_relations() — 从 import_map 构建模块依赖图
  └── download_key_files()  — 从 GitHub raw 下载 .py 文件（最多30个）

ArchitectureAgent(BaseAgent)（LLM 解读）
  └── analyze(repo_info, modules, entry_file, import_map, dependencies?)
      → ArchitectureResult

新增模型:
  ModuleInfo          — name / path / responsibility / key_files / imports / exported_symbols
  ArchitectureResult  — architecture_pattern / modules / entry_file / module_relations / architecture_summary
```

#### 架构分析数据流

```
file_tree（扁平列表）
  │
  ├── 1. group_modules() — 按目录聚合 → {module_name: [files]}
  ├── 2. identify_entry_file() — 命名匹配 → "tinydb/__init__.py"
  ├── 3. download_key_files() — GitHub raw 下载 .py (max 30) → {path: source_code}
  ├── 4. extract_imports() × N — AST 解析 → {path: [import_name]}
  ├── 5. is_project_import() — 过滤外部库 → 仅保留项目内引用
  ├── 6. infer_module_relations() — 构建依赖图 → [{from, to, type}]
  │
  └── 7. ArchitectureAgent.analyze() — LLM: 模式识别 + 职责推断 + 报告生成
        → ArchitectureResult
```

### Step 4: 代码产出

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/opensource_analyst/github/architecture_analyzer.py` | 新建 | ~222 行：ArchitectureAnalyzer 类（group_modules / identify_entry_file / extract_imports / is_project_import / infer_module_relations / download_key_files） |
| `src/opensource_analyst/agents/architecture.py` | 新建 | ~111 行：ArchitectureAgent 类（analyze → LLM 架构报告） |
| `src/opensource_analyst/prompts/architecture.py` | 新建 | ~56 行：ARCHITECTURE_PROMPT 模板 |
| `tests/test_architecture.py` | 新建 | ~227 行：12 个测试（3 分组 + 4 入口 + 2 AST + 1 模型 + 2 集成 LLM） |
| `src/opensource_analyst/models/analysis.py` | 修改 | 新增 `ModuleInfo` + `ArchitectureResult` 两个 Pydantic 模型 |
| `src/opensource_analyst/graph/state.py` | 修改 | `architecture` 字段类型从 `Any` 改为 `ArchitectureResult \| None` |
| `src/opensource_analyst/graph/nodes.py` | 修改 | `architecture_node` 从 `def → return {"architecture": None}` 占位 → `async def → 5步实际分析链路` |
| `src/opensource_analyst/graph/workflow.py` | 修改 | 节点顺序重排：dependency → architecture → analyze（analyze 可拿到架构数据） |
| `tests/test_graph.py` | 修改 | 更新占位节点测试：`architecture_node` 改为 `asyncio.run()` 调用 + 真实产出验证 |

**关键技术点：**

- **模块分组算法**：按前两级目录前缀聚合，`ROOT_IGNORE` 集合（tests/docs/examples/.github 等）单独分到对应组，避免与核心业务模块混淆
- **入口识别 fallback 链**：10 种命名模式按优先级匹配 → 根目录 `.py` → 任意 `.py`，确保任何项目都能找到入口
- **AST import 提取**：区分 `import X`（`ast.Import`，从 `names` 字段提取）和 `from .X import Y`（`ast.ImportFrom`，从 `module` + `level` 字段提取），相对导入用 `.` 数量表示层级
- **项目内 import 过滤**：`is_project_import()` 同时检测相对导入（以 `.` 开头）和绝对导入（前缀匹配已知模块名），排除 `os`、`sys`、`numpy` 等外部依赖
- **模块关系推断**：从 `{file: [imports]}` 反查 `{file: module}` 索引，构建 `{from_module, to_module}` 有向边，去重后输出
- **LLM 只做语义理解**：数据提取（模块、入口、import、关系）全部由 ArchitectureAnalyzer 在无 LLM 的情况下完成，ArchitectureAgent 只负责语义解读（模式识别、职责推断、中文总结）
- **节点顺序重排**：M8 将 architecture 移到 analyze 之前，使 analyze 节点能同时拿到 dependencies + architecture 两个维度的数据来增强分析质量
- **占位测试适配**：`architecture_node` 从同步占位变为异步实现后，旧测试需要加 `asyncio.run()` 包装 + 更新预期结果

### Step 5: 验收标准

```bash
# 运行 M8 专项测试
uv run pytest tests/test_architecture.py -v
# 预期：12 passed
#   - 3 分组：TinyDB 模块/多层目录 src.controller/扁平项目
#   - 4 入口：main.py / __main__.py / app.py / fallback
#   - 2 AST：import 提取 / 空代码
#   - 1 模型：ArchitectureResult 字段校验
#   - 2 集成：LLM TinyDB 架构报告 / 空项目

# 全量回归测试
uv run pytest -v
# 预期：70/70 passed
#   M2: 9 + M3: 4 + M4: 6 + M5: 5 + M6: 16 + chat: 6 + M7: 12 + M8: 12

# 验证工作流结构
uv run python -c "from opensource_analyst.graph.workflow import export_workflow_mermaid; print(export_workflow_mermaid())"
# 预期：Mermaid 图中 architecture 节点位于 dependency 和 analyze 之间
```

---

*笔记结束。最后更新：2026-06-04*
