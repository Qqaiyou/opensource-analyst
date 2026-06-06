# OpenSource Analyst - 项目进度跟踪

> 最后更新：2026-06-06
> 当前阶段：Milestone 13 ✅ 已完成 | 全部 13 个里程碑完成

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
| M4 | Repository RAG | ✅ 已完成 | 2026-06-02 | - |
| M5 | FastAPI 接口 | ✅ 已完成 | 2026-06-02 | - |
| M6 | LangGraph 工作流 | ✅ 已完成 | 2026-06-03 | - |
| M7 | Dependency Agent | ✅ 已完成 | 2026-06-04 | - |
| M8 | Architecture Agent | ✅ 已完成 | 2026-06-04 | - |
| M9 | Learning Agent | ✅ 已完成 | 2026-06-05 | - |
| M10 | Coordinator Agent | ✅ 已完成 | 2026-06-05 | - |
| M11 | MCP 集成 | ✅ 已完成 | 2026-06-06 | - |
| M12 | 高级功能 | ✅ 已完成 | 2026-06-06 | `dc6beaf` |
| M13 | 交互式对话 | ✅ 已完成 | 2026-06-06 | `ff676d4` |

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

## 七、Milestone 4 完成详情

### 7.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| DashScopeEmbeddings | `src/opensource_analyst/vectorstore/chroma.py` | 百炼 Embedding 适配器 + VectorStore（ChromaDB 封装） |
| CodeIndexer | `src/opensource_analyst/rag/indexer.py` | 代码文件过滤 + GitHub raw 下载 + 分块 + 批量索引 |
| CodeRetriever | `src/opensource_analyst/rag/retriever.py` | 语义搜索 + LLM 上下文拼接 |
| 测试 | `tests/test_rag.py` | 6 个测试（3 单元 + 3 集成） |

### 7.2 测试结果

```
M4 新增：6/6 PASSED
  - 3 单元测试：文件过滤逻辑（.py 保留 / docs 排除 / .rst 排除）
  - 1 单元测试：百炼 text-embedding-v3 返回 1024 维向量
  - 2 集成测试：TinyDB 索引 → 搜索 → 上下文拼接
全项目：18/19 PASSED（1 个 GitHub API 瞬时 SSL 错误，与 M4 无关）
```

### 7.3 技术要点

- **Embedding 模型**：阿里百炼 `text-embedding-v3`，1024 维，通过 OpenAI Compatible 接口接入
- **自建适配器** `DashScopeEmbeddings`：实现了 LangChain `Embeddings` 接口，逐条请求 + 3 次重试解决网络波动
- **分块策略**：`RecursiveCharacterTextSplitter`，chunk_size=1000, overlap=200
- **文件过滤**：排除 tests/、docs/、node_modules/、非代码扩展名、>500KB 文件、上限 200 文件
- **GitHub 下载**：并发 async + 自适应 master/main 分支

---

## 八、Milestone 5 完成详情

### 8.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| AnalyzeRequest/TaskStatus/TaskResult | `src/opensource_analyst/models/task.py` | 请求/响应 Pydantic 模型 |
| POST /analyze | `src/opensource_analyst/api/analyze.py` | 发起分析 + BackgroundTasks 后台执行 |
| GET /task/{id} | `src/opensource_analyst/api/task.py` | 状态查询 + 结果获取 |
| main.py 修改 | `src/opensource_analyst/main.py` | 注册 analyze/task 两个 router |
| API 测试 | `tests/test_api.py` | 5 个测试（含端到端全链路）|

### 8.2 测试结果

```
24/24 PASSED
  M2: 9 tests (GitHub 客户端)
  M3: 4 tests (Agent 分析)
  M4: 6 tests (RAG 索引检索)
  M5: 5 tests (API 接口)
```

### 8.3 API 端点

| 方法 | 路径 | 用途 | 状态码 |
|------|------|------|--------|
| POST | `/analyze` | 发起分析 | 202 Accepted |
| GET | `/task/{id}` | 查询状态 | 200 / 404 |
| GET | `/task/{id}/result` | 获取结果 | 200 / 404 / 409 |

### 8.4 技术要点

- **异步任务**：FastAPI BackgroundTasks，请求立即返回 task_id，后台执行 M2+M3 全链路
- **内存存储**：MVP 用 `dict[str, dict]`，后续可替换 Redis
- **URL 校验**：复用 M2 的 `GitHubClient.parse_url()`，非 GitHub 域名直接 400
- **轮询模式**：用户 POST /analyze → 拿 task_id → 轮询 GET /task/{id} → GET /task/{id}/result
- **代理修复**：`GitHubClient` 添加 `trust_env=False`，解决 Windows 系统代理导致 httpx 连接失败的问题
- **导入修复**：`parser.py` / `readme.py` / 测试文件 中的 `from src.opensource_analyst.*` 改为 `from opensource_analyst.*` 相对导入

---

## 九、Milestone 6 完成详情

### 9.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| GraphState | `src/opensource_analyst/graph/state.py` | TypedDict 共享状态（9 字段：新增 code_indexed、rag_context） |
| Nodes | `src/opensource_analyst/graph/nodes.py` | 6 个节点（load_repo / index_code / retrieve_context / analyze / architecture / learning） |
| Workflow | `src/opensource_analyst/graph/workflow.py` | build_workflow() + export_workflow_mermaid() + 条件边错误短路 |
| API 改造 | `src/opensource_analyst/api/analyze.py` | _run_analysis 改为 LangGraph 工作流调用 |
| Analyzer 增强 | `src/opensource_analyst/agents/base.py` | analyze() 新增 rag_context 可选参数，注入代码上下文 |
| VectorStore | `src/opensource_analyst/vectorstore/chroma.py` | 新增 count() 方法，检查 collection 是否已有数据 |
| **对话 API** | `src/opensource_analyst/api/chat.py` | POST /chat — RAG 对话接口 |
| 对话模型 | `src/opensource_analyst/models/chat.py` | ChatRequest / ChatResponse / SourceInfo |
| 对话 Prompt | `src/opensource_analyst/prompts/chat.py` | RAG 对话 prompt 模板 |
| 测试 | `tests/test_graph.py` | 16 个测试（新增错误路径、RAG 节点、Mermaid 导出、短路测试） |
| 测试 | `tests/test_chat.py` | 6 个测试（模型校验、端点校验、全链路集成） |

### 9.2 测试结果

```
46/46 PASSED (310s)
  M2: 9 tests (GitHub 客户端)
  M3: 4 tests (Agent 分析)
  M4: 6 tests (RAG 索引检索)
  M5: 5 tests (API 接口)
  M6: 16 tests (LangGraph 工作流 — 新增 9)
  chat: 6 tests (RAG 对话接口 — 新增)
```

### 9.3 工作流结构

```
load_repo → index_code → retrieve_context → analyze → architecture → learning → END
   │          ↓ error?       ↓ error?        ↓ error?
   │          END            END             END
   │
 GitHub API    RAG 索引      RAG 检索        LLM 分析      占位 (M8)    占位 (M9)
           (ChromaDB 已有数据则跳过)
```

### 9.4 新增 API 端点

| 方法 | 路径 | 用途 | 状态码 |
|------|------|------|--------|
| POST | `/analyze` | 发起分析 | 202 Accepted |
| GET | `/task/{id}` | 查询状态 | 200 / 404 |
| GET | `/task/{id}/result` | 获取结果 | 200 / 404 / 409 |
| **POST** | **`/chat`** | **RAG 对话提问** | **200 / 400 / 422** |

### 9.5 技术要点

- **RAG 集成**：load_repo 后接 index_code（建 ChromaDB 索引）→ retrieve_context（语义检索代码片段）→ analyze 注入 LLM prompt
- **索引复用**：`VectorStore.count()` 检查已有文档数，>0 则跳过下载+Embedding，直接复用
- **条件路由**：每个节点后检查 error，有 error 则短路到 END，后续节点不再空跑
- **Mermaid 导出**：`export_workflow_mermaid()` 返回工作流图 Mermaid 标记字符串
- **对话接口**：POST /chat 接收自然语言问题，用已建索引做 RAG 检索 → DeepSeek 回答，返回答案+代码引用来源
- **防御性编程**：每个节点检查 repo_info 是否缺失，analyze_node 有缺失防护
- **异步/同步混编**：index_code_node 为 async（下载+Embedding 为 IO 密集），retrieve_context_node 为 sync
- **代码审查修复**：`build_workflow()` 返回类型修正为 `CompiledStateGraph`；`BaseAgent.invoke()` 替代 `_invoke()`；chat.py LLM 调用新增 502 错误处理；indexer.py 删除死代码

### 9.6 Git 提交记录

```
37d6324 fix: 代码审查修复 — 返回值类型、错误处理、死代码清理
7b4f65e feat: 将 Embedding 模型从 text-embedding-v3 升级为 text-embedding-v4
760c64c feat: 完善 Milestone 6 — RAG 接入工作流 + 对话接口 + 错误路由
3b58389 feat: 完成 Milestone 6 — LangGraph 工作流
```

---

## 九点五、Milestone 7 完成详情

### 9.5.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| DependencyFileParser | `src/opensource_analyst/github/dependency_parser.py` | 依赖文件检测(8种格式) + 多语言解析(pyproject.toml/package.json/pom.xml/go.mod/Cargo.toml 等) |
| DependencyAgent | `src/opensource_analyst/agents/dependency.py` | LLM 依赖分类(core/dev/build/test/peer) + 用途解读 |
| DependencyPrompt | `src/opensource_analyst/prompts/dependency.py` | 依赖分析专用 prompt 模板 |
| Dependency 模型增强 | `src/opensource_analyst/models/analysis.py` | 新增 version、category 字段 |
| GraphState 扩展 | `src/opensource_analyst/graph/state.py` | 新增 parsed_dependencies、dependencies 字段 (9→11 字段) |
| dependency_node | `src/opensource_analyst/graph/nodes.py` | 新增工作流节点 (6→7 节点) |
| Workflow 更新 | `src/opensource_analyst/graph/workflow.py` | 插入 dependency 节点到 retrieve_context 和 analyze 之间 |
| OVERVIEW_PROMPT 增强 | `src/opensource_analyst/prompts/overview.py` | 新增 {dependencies} 占位符，注入依赖分析数据 |
| Analyzer 增强 | `src/opensource_analyst/agents/base.py` | analyze() 新增 dependencies 参数 |
| 测试 | `tests/test_dependency.py` | 12 个测试(6 检测 + 3 解析 + 1 模型 + 2 集成 LLM) |

### 9.5.2 测试结果

```
58/58 PASSED (M2-M7 累计)
  M2:  9 tests (GitHub 客户端)
  M3:  4 tests (Agent 分析)
  M4:  6 tests (RAG 索引检索)
  M5:  5 tests (API 接口)
  M6: 16 tests (LangGraph 工作流)
  chat: 6 tests (RAG 对话接口)
  M7: 12 tests (依赖检测 + 解析 + Agent 分析)  ← 新增
```

### 9.5.3 工作流结构 (M7)

```
load_repo → index_code → retrieve_context → dependency → analyze → architecture → learning → END
              ↓ error?        ↓ error?       ↓ error?    ↓ error?
              END             END            END         END

GitHub API    RAG 索引      RAG 检索      依赖解析     LLM 分析     占位         占位
           (复用已有索引)                + LLM 分类   (注入依赖数据)
```

### 9.5.4 支持的依赖文件格式

| 生态 | 文件 | 解析方式 | 分类粒度 |
|------|------|---------|---------|
| Python | pyproject.toml | TOML | dependencies / optional / build-system |
| Python | setup.py | 正则 | install_requires |
| Python | setup.cfg | configparser | install_requires |
| Python | requirements.txt | 行解析 | core |
| Node.js | package.json | JSON | dependencies / devDependencies / peerDependencies |
| Java | pom.xml | XML regex | groupId:artifactId (含 test scope 识别) |
| Java | build.gradle(.kts) | 正则 | implementation / testImplementation / compileOnly |
| Go | go.mod | 行解析 | require 块 |
| Rust | Cargo.toml | TOML | dependencies / dev-dependencies / build-dependencies |

### 9.5.5 数据流

```
file_tree → DependencyFileParser.detect_dep_files() → [pyproject.toml, ...]
  → fetch_and_parse() → [ParsedDependency(name, version, source, category)]
  → DependencyAgent.analyze() → [Dependency(name, version, category, purpose)]
  → GraphState.dependencies
  → Analyzer.analyze(dependencies=...) → OVERVIEW_PROMPT 注入依赖数据
  → AnalysisResult.tech_stack.key_dependencies (增强版)
```

### 9.5.6 技术要点

- **多语言解析器**：一个 Parser 类覆盖 8 种文件格式，按文件名分发到静态方法
- **PEP 508 拆分**：`_split_pep508()` 统一处理 `name>=version` 格式，同时支持 >=、==、~=、^ 等版本约束
- **分类体系**：core(运行时) / dev(开发工具) / build(构建) / test(测试) / peer(对等依赖)
- **LLM 增强**：依赖文件提取的硬数据 + LLM 语义理解，既准确又有深度
- **错误短路保持**：dependency 节点完全遵循现有的 error→END 短路模式
- **向后兼容**：`Analyzer.analyze(dependencies=None)` 默认值保证旧调用路径不破坏

---

## 九点六、Milestone 8 完成详情

### 9.6.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| ArchitectureAnalyzer | `src/opensource_analyst/github/architecture_analyzer.py` | 模块分组 + 入口文件识别 + AST import 提取 + 模块关系推断 |
| ArchitectureAgent | `src/opensource_analyst/agents/architecture.py` | LLM 架构模式识别 + 模块职责推断 + 架构报告生成 |
| ArchitecturePrompt | `src/opensource_analyst/prompts/architecture.py` | 架构分析专用 prompt 模板 |
| ArchitectureResult 模型 | `src/opensource_analyst/models/analysis.py` | ArchitectureResult + ModuleInfo Pydantic 模型 |
| GraphState 增强 | `src/opensource_analyst/graph/state.py` | architecture 字段类型从 Any → ArchitectureResult |
| architecture_node 实现 | `src/opensource_analyst/graph/nodes.py` | 占位节点 → 完整 5 步分析链路 |
| 工作流重排 | `src/opensource_analyst/graph/workflow.py` | 节点顺序改为 dependency → architecture → analyze |
| 测试 | `tests/test_architecture.py` | 12 个测试 (8 单元 + 2 模型 + 2 集成 LLM) |
| 测试修复 | `tests/test_graph.py` | 更新占位节点测试以适配 async 真实实现 |

### 9.6.2 测试结果

```
70/70 PASSED (M2-M8 累计)
  M2:   9 tests (GitHub 客户端)
  M3:   4 tests (Agent 分析)
  M4:   6 tests (RAG 索引检索)
  M5:   5 tests (API 接口)
  M6:  16 tests (LangGraph 工作流)
  M7:  12 tests (依赖检测 + 解析 + Agent 分析)
  chat: 6 tests (RAG 对话接口)
  M8:  12 tests (模块分组 + 入口识别 + AST + 模型 + Agent)  ← 新增
```

### 9.6.3 工作流结构 (M8)

```
load_repo → index_code → retrieve_context → dependency → architecture → analyze → learning → END
              ↓ error?        ↓ error?       ↓ error?    ↓ error?      ↓ error?
              END             END            END         END           END

GitHub API    RAG 索引      RAG 检索      依赖解析    架构分析       LLM 分析     占位
           (复用已有索引)                + LLM 分类  (静态+LLM)    (注入全部上下文)
```

### 9.6.4 架构分析数据流

```
file_tree → ArchitectureAnalyzer.group_modules() → {module_name: [files]}
  → ArchitectureAnalyzer.identify_entry_file() → "tinydb/__init__.py"
  → download_key_files() (最多 30 个 .py) → {path: source_code}
  → ArchitectureAnalyzer.extract_imports() × N → {path: [import_name]}
  → ArchitectureAnalyzer.infer_module_relations() → [{from, to, type}]
  → ArchitectureAgent.analyze() (LLM) → ArchitectureResult
```

### 9.6.5 技术要点

- **模块分组算法**：按前两级目录分组，识别 ROOT_IGNORE 中的非源码目录并单独分类
- **入口识别优先级**：__main__.py > main.py > app.py > server.py > run.py > ... > fallback 首个 .py
- **AST import 提取**：处理 `import X`（绝对）和 `from .X import Y`（相对）两种语法
- **项目内 import 过滤**：`is_project_import()` 排除标准库和第三方库，只保留项目内部引用
- **模块关系推断**：从 import_map 反向构建 {from_module → to_module} 的有向图
- **LLM 介入点**：只做语义理解（模式识别、职责推断、总结），不做数据提取
- **节点顺序优化**：dependency → architecture → analyze，使 analyze 能同时拿到依赖和架构两维数据

---

## 九点七、Milestone 9 完成详情

### 9.7.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| LearningAgent | `src/opensource_analyst/agents/learning.py` | 综合全部分析结果的纯 LLM Agent |
| LEARNING_PATH_PROMPT | `src/opensource_analyst/prompts/learning.py` | 学习路线 + 面试知识点 + 阅读建议 prompt 模板 |
| 新增模型 | `src/opensource_analyst/models/analysis.py` | LearningStep / InterviewPoint / ReadingSuggestion / LearningPath 四个 Pydantic 模型 |
| GraphState 增强 | `src/opensource_analyst/graph/state.py` | learning_path 类型从 Any → LearningPath \| None |
| learning_node 实现 | `src/opensource_analyst/graph/nodes.py` | 占位节点 → 完整 5 步分析链路 |
| API 输出线缆 | `src/opensource_analyst/api/analyze.py` | AnalysisResult 新增 learning_path 字段 + 线程修复 |
| 工作流修复 | `src/opensource_analyst/graph/workflow.py` | 删除冗余的 architecture→learning 边 |
| 测试 | `tests/test_learning.py` | 4 个测试 (2 模型 + 2 集成 LLM) |
| 测试修复 | `tests/test_graph.py` | 更新 learning_node 占位测试 |

### 9.7.2 测试结果

```
75/75 PASSED (M2-M9 累计)
  M2:   9 tests (GitHub 客户端)
  M3:   4 tests (Agent 分析)
  M4:   6 tests (RAG 索引检索)
  M5:   5 tests (API 接口)
  M6:  17 tests (LangGraph 工作流)
  M7:  12 tests (依赖检测 + 解析 + Agent 分析)
  chat: 6 tests (RAG 对话接口)
  M8:  12 tests (模块分组 + 入口识别 + AST + 模型 + Agent)
  M9:   4 tests (模型 + LearningAgent 集成)  ← 新增
```

### 9.7.3 工作流结构 (M9)

```
load_repo → index_code → retrieve_context → dependency → architecture → analyze → learning → END
              ↓ error?        ↓ error?       ↓ error?    ↓ error?      ↓ error?  ↓ error?
              END             END            END         END           END       END

GitHub API    RAG 索引      RAG 检索      依赖解析    架构分析       LLM 分析  学习路线
           (复用已有索引)                + LLM 分类  (静态+LLM)    (注入全部  (综合生成)
                                                                  上下文)
```

### 9.7.4 数据模型

| 模型 | 字段 | 用途 |
|------|------|------|
| LearningStep | step_number, title, description, key_files, difficulty, estimated_hours | 单个学习步骤 |
| InterviewPoint | topic, question, answer_hint, related_files | 面试知识点 |
| ReadingSuggestion | file_path, why_important, reading_order, focus_points | 源码阅读建议 |
| LearningPath | steps, prerequisites, estimated_days, interview_points, reading_suggestions | 顶层聚合容器 |

### 9.7.5 技术要点

- **纯 LLM Agent**：M9 不涉及静态代码解析，完全依靠 prompt engineering + 上下文注入
- **信息综合**：注入 overview + tech_stack + dependencies + architecture 全部分析结果到 LLM
- **容错设计**：每个输入字段有 fallback（"未提供..."），缺失任一分析结果也能生成基本路线
- **线程修复**：`run_in_executor` 将同步 LLM 调用移到独立线程，避免阻塞事件循环
- **工作流修复**：删除 workflow.py 中冗余的 `architecture → learning` 直接边，确保 analyze 先于 learning 执行

---

## 九点八、Milestone 10 完成详情

### 9.8.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| AgentRegistry | `src/opensource_analyst/agents/registry.py` | AgentSpec 数据类 + AgentRegistry 注册表（注册、就绪判断、完成判断） |
| CoordinatorAgent | `src/opensource_analyst/agents/coordinator.py` | 调度引擎（asyncio.gather 并行执行 + 独立容错 + logging） |
| build_analysis_registry | `src/opensource_analyst/graph/nodes.py` | 注册 4 个分析 Agent 的工厂函数（含模块级缓存） |
| coordinator_node | `src/opensource_analyst/graph/nodes.py` | 新增调度节点（调用 CoordinatorAgent.run_round） |
| Workflow 重构 | `src/opensource_analyst/graph/workflow.py` | 从 7 节点串行边 → 4 节点 + coordinator 循环边 |
| main.py 修改 | `src/opensource_analyst/main.py` | 添加 `logging.basicConfig(level=INFO)` |
| 测试 | `tests/test_coordinator.py` | 12 个测试（6 registry + 4 coordinator + 2 factory） |
| 测试更新 | `tests/test_graph.py` | 3 个 M10 测试（coordinator_node + tinydb_m10 + mermaid） |

### 9.8.2 测试结果

```
91/91 PASSED
  M2:   9 tests (GitHub 客户端)
  M3:   4 tests (Agent 分析)
  M4:   6 tests (RAG 索引检索)
  M5:   5 tests (API 接口)
  M6:  17 tests (LangGraph 工作流)
  M7:  12 tests (依赖检测 + 解析 + Agent 分析)
  chat: 6 tests (RAG 对话接口)
  M8:  12 tests (模块分组 + 入口识别 + AST + 模型 + Agent)
  M9:   4 tests (模型 + LearningAgent 集成)
  M10: 16 tests (registry + coordinator + workflow 集成)  ← 新增
```

### 9.8.3 工作流结构 (M10)

```
load_repo → index_code → retrieve_context → coordinator ⇄ END
  (pipeline 固定管道)                         ↑  ↓
                                          (loop 直到全部完成)

coordinator 内部并行调度:
  Round 1: asyncio.gather(dependency, architecture, analyze)
  Round 2: asyncio.gather(learning)
  Round 3: all_done → END
```

### 9.8.4 核心架构决策

- **AgentRegistry**：声明式注册 — 每个 Agent 声明 `dependencies`（需要哪些 state key）和 `produces`（产出哪些 state key）
- **CoordinatorAgent.run_round()**：读取 registry → `get_ready(state)` → `asyncio.gather` 并行执行 → 合并结果
- **调度 DAG**：
  - Round 1: dependency / architecture / analyze 三者 `repo_info` 就绪即可并行
  - Round 2: learning 需要 overview + tech_stack + architecture 全部就绪
- **所有阻塞 LLM 调用均通过 `loop.run_in_executor(None, ...)` 包装**，确保 asyncio.gather 真正并行
- **Registry 模块级缓存**：`build_analysis_registry()` 使用 global 缓存，确保 coordinator_node 和 _should_loop_coordinator 共享同一实例

### 9.8.5 容错设计

| 机制 | 实现 |
|------|------|
| Agent 级隔离 | `asyncio.gather(return_exceptions=True)` — 单一 Agent 异常记录到 `{name}_error` key，不抛异常 |
| 循环终止保护 | `_should_loop_coordinator` 检查 `all_done` → 即使有 Agent 失败最终也会退出 |
| Fallback 链 | learning_node 内部对缺失输入有 "未提供..." fallback，M9 已有 |
| Error 短路保持 | pipeline 阶段 `_should_continue` 不变，load_repo 失败仍然 END |

### 9.8.6 技术要点

- **并行调度**：Coordinator 不做具体分析，只管理 Agent 的生命周期 — 找到就绪 → 并行执行 → 收集结果
- **条件循边**：`_should_loop_coordinator` 条件路由实现 `coordinator → coordinator` 自循环
- **API 不变**：POST /analyze 请求/响应、AnalysisResult 数据结构完全不变
- **日志可见**：`logging.basicConfig(level=INFO)` 让 Coordinator 调度信息在终端输出
- **测试可见**：集成测试含 `print()` 输出 Round 1/2/3 的完整中间结果

---

## 九点九、Milestone 11 完成详情

### 9.9.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| MCPServerConfig | `src/opensource_analyst/mcp/config.py` | 单个 MCP Server 的启动配置 Pydantic 模型 |
| MCPToolInfo | `src/opensource_analyst/mcp/config.py` | MCP Tool 元信息模型（server_name, tool_name, description, input_schema） |
| MCPToolResult | `src/opensource_analyst/mcp/config.py` | Tool 调用结果模型（content, is_error） |
| MCPServerConnection | `src/opensource_analyst/mcp/client.py` | 单个 MCP Server 的 stdio transport 连接管理（connect/disconnect/list_tools/call_tool） |
| MCPClientManager | `src/opensource_analyst/mcp/client.py` | 多 Server 管理器（connect_all/disconnect_all/list_all_tools/路由 call_tool） |
| __init__.py 更新 | `src/opensource_analyst/mcp/__init__.py` | 导出 5 个公开 API |
| 测试 | `tests/test_mcp.py` | 15 个测试（4 单元 + 11 集成） |

### 9.9.2 测试结果

```
106/106 PASSED (全量)
  M2-M10: 91 tests (全部通过，零回归)
  M11:   15 tests (4 单元 + 11 集成)  ← 新增

M11 测试明细:
  单元测试 (4):
    - Config 创建 + 默认值
    - Config 序列化/反序列化
    - enabled=False 标记
    - MCPToolResult.is_error 标记

  集成测试 — 连接 (6):
    - connect → list_tools → 2 个工具
    - call_tool("echo") → ECHO: hello
    - call_tool("add", {3,4}) → 7
    - 无效命令 → RuntimeError("启动失败")
    - 未连接调用 → RuntimeError("未连接")
    - 未知工具 → 容错处理

  集成测试 — Manager (5):
    - list_all_tools 跨 Server 聚合
    - 启用/禁用混合 → 只连接启用的
    - call_tool 路由到正确 Server
    - 不存在的 Server → ValueError
    - disconnect 后连接清理
```

### 9.9.3 架构设计

```
能力层 — mcp/
├── config.py           ← 3 个 Pydantic 模型（MCPServerConfig / MCPToolInfo / MCPToolResult）
└── client.py           ← MCPServerConnection + MCPClientManager（stdio transport 连接管理）

调用流程:
  MCPServerConnection(config)
    ├─→ connect(): 启动子进程 + stdio_client + ClientSession + initialize 握手
    ├─→ list_tools() → [MCPToolInfo, ...]
    ├─→ call_tool(name, args) → MCPToolResult
    └─→ disconnect(): 关闭 session + stdio context

  MCPClientManager([configs])
    ├─→ connect_all(): 逐一连接已启用的 Server（失败跳过不阻断）
    ├─→ list_all_tools(): 聚合所有 Server 的工具
    ├─→ call_tool(server_name, tool_name, args): 路由到对应 Server
    └─→ disconnect_all(): 清理所有连接
```

### 9.9.4 核心架构决策

- **stdio transport**：MCP Server 以子进程方式启动，通过 stdin/stdout JSON-RPC 通信。无需额外网络端口，完全本地化
- **独立能力层**：不修改任何现有 Agent、Graph、API 代码，MCP 作为独立的能力层存在
- **声明式配置**：MCPServerConfig 声明 Server 的启动方式（command + args + env），支持 enabled=False 选择性禁用
- **Mock Server 测试**：用 Python 内建 MCP Server 做 Echo Mock，覆盖真实 stdio transport 的完整链路，避免依赖外部 npm 包

### 9.9.5 容错设计

| 机制 | 实现 |
|------|------|
| 连接失败跳过 | Manager.connect_all() 中单个 Server 连接失败不阻断其他 Server |
| 工具调用异常透传 | call_tool() 中异常通过 logger.exception 记录后重新抛出 |
| 未连接防护 | list_tools() / call_tool() 检查 `_session is not None`，否则抛出 RuntimeError |
| 资源清理 | disconnect() 依次关闭 session → stdio context，每步独立 try/except |

### 9.9.6 技术要点

- **MCP SDK v1.27.2**：使用官方 `mcp` Python 包，提供 `StdioServerParameters`、`stdio_client`、`ClientSession` 等底层 API
- **async context manager**：MCPServerConnection 和 MCPClientManager 均支持 `async with`，确保连接生命周期自动管理
- **stdio_client 生命周期**：保存 `_stdio_ctx` 引用，确保 `__aexit__` 在连接关闭时正确清理子进程
- **现阶段为独立能力层**：真实 MCP Server（GitHub/Filesystem/Browser npm 包）待后续集成，当前只搭建了连接管理框架

---

## 九点十、Milestone 12 完成详情

### 9.10.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| Mermaid 图生成器 | `src/opensource_analyst/analysis/mermaid.py` | 纯静态 Mermaid 流程图生成（模块关系图/文件依赖图/技术栈全景图） |
| Mermaid 图生成器 init | `src/opensource_analyst/analysis/__init__.py` | 子包初始化 |
| Interview Agent | `src/opensource_analyst/agents/interview.py` | LLM 面试题生成（junior/mid/senior/staff 四级） |
| Interview Prompt | `src/opensource_analyst/prompts/interview.py` | 面试题生成 prompt 模板 |
| Reflection Agent | `src/opensource_analyst/agents/reflection.py` | LLM 自检 Agent（完整性/准确性/深度/一致性四维度评分） |
| Reflection Prompt | `src/opensource_analyst/prompts/reflection.py` | 反思 prompt 模板 |
| 模型增强 | `src/opensource_analyst/models/analysis.py` | 新增 7 个模型（MermaidDiagrams / InterviewQuestion / InterviewResult / ReflectionIssue / ReflectionResult / AnalysisResult 增强） |
| GraphState 增强 | `src/opensource_analyst/graph/state.py` | 新增 4 个字段（mermaid_diagrams / interview_result / reflection / import_map） |
| Nodes 增强 | `src/opensource_analyst/graph/nodes.py` | 新增 3 个节点（mermaid_node / interview_node / reflection_node）+ architecture_node 导出 import_map |
| Registry 增强 | `src/opensource_analyst/graph/nodes.py` | build_analysis_registry 注册 3 个新 Agent，实现 6 轮调度 |
| API 增强 | `src/opensource_analyst/api/analyze.py` | AnalysisResult 包含全部 M12 新字段 |
| 版本号 | `src/opensource_analyst/__init__.py` | 0.1.0 → 0.2.0 |
| 测试 | `tests/test_mermaid.py` | 14 个测试（全部纯静态，无 LLM 调用） |
| 测试 | `tests/test_interview.py` | 4 个测试（2 单元 + 2 集成 LLM） |
| 测试 | `tests/test_reflection.py` | 4 个测试（2 单元 + 2 集成 LLM） |

### 9.10.2 测试结果

```
全部 M12 单元测试（无 LLM）: 18/18 PASSED
  - test_mermaid.py:    14 tests (纯静态 Mermaid 生成)
  - test_interview.py:   2 tests (模型校验)
  - test_reflection.py:  2 tests (模型校验)
```

### 9.10.3 新增 Pydantic 模型

| 模型 | 字段 | 用途 |
|------|------|------|
| MermaidDiagrams | module_flowchart, dependency_graph, tech_stack_diagram | Mermaid 可视化图字符串 |
| InterviewQuestion | topic, difficulty, question, answer_hint, related_files, code_context | 单个面试题 |
| InterviewResult | questions, total_questions, difficulty_distribution | 面试题集合 |
| ReflectionIssue | category, severity, description, suggestion | 反思发现的问题 |
| ReflectionResult | completeness_score, issues, summary | 反思结果 |

### 9.10.4 LangGraph 工作流（M12）

```
load_repo → index_code → retrieve_context → coordinator ⇄ END
                                             ↑  ↓
                                        (多轮调度)

coordinator Round 1: asyncio.gather(dependency, architecture, analyze)
coordinator Round 2: asyncio.gather(learning)
coordinator Round 3: mermaid_node (纯静态，无 LLM)
coordinator Round 4: interview_node (LLM 面试题)
coordinator Round 5: reflection_node (LLM 自检)
coordinator Round 6: all_done → END
```

### 9.10.5 Mermaid 图生成策略

- **模块关系图**（module_flowchart）：基于 ArchitectureResult.modules 和 module_relations 生成 flowchart LR，每个模块一个 subgraph，边表示模块间依赖
- **文件依赖图**（dependency_graph）：基于 import_map（{file: [imports]}）生成有向图，按模块分组，edge 最多 40 条
- **技术栈全景图**（tech_stack_diagram）：分四层展示项目名/语言/框架/核心依赖
- 所有图为纯字符串生成，无 LLM 调用，零失败风险

### 9.10.6 技术要点

- **纯静态 Mermaid**：`mermaid_node` 全部基于已有数据的字符串拼接，无 LLM 调用，不会失败
- **Agent 注册自动化**：M12 新增的 interview/mermaid/reflection 三个 Agent 注册到 `build_analysis_registry()`，Coordinator 自动在后续轮次调度
- **import_map 传递**：`architecture_node` 新增产出 `import_map`，供 `mermaid_node` 的文件依赖图使用
- **AnalysisResult 向后兼容**：所有 M12 新增字段均为 `Optional`，不影响现有 API 调用方
- **版本提升**：0.1.0 → 0.2.0，标志 M12 高级功能完成

---

## 九点十一、Milestone 13 完成详情

### 9.11.1 产出文件

| 文件 | 路径 | 内容 |
|------|------|------|
| ConversationState | `src/opensource_analyst/graph/conversation_state.py` | 对话状态 TypedDict（messages + add_messages reducer + 分析结果字段） |
| ConversationGraph | `src/opensource_analyst/graph/conversation.py` | build_conversation_graph() — ReAct 循环图（call_model ⇄ tool_node） |
| ReactAgent | `src/opensource_analyst/agents/react_agent.py` | 单 ReAct Agent，绑定 search_code + MCP tools |
| MCP Tool Bridge | `src/opensource_analyst/mcp/tool_bridge.py` | build_mcp_tools() — MCPToolInfo → LangChain StructuredTool |
| Conversation Prompt | `src/opensource_analyst/prompts/conversation.py` | ReAct 系统提示词（中文，注入分析结果 + 工具使用规范） |
| Conversation API | `src/opensource_analyst/api/conversation.py` | 5 个端点（/start /{id}/message /{id}/stream /{id}/history DELETE） |
| Session Store | `src/opensource_analyst/api/session.py` | ConversationSessionStore — 内存会话管理 + AnalysisResult 摘要压缩 |
| Conversation Models | `src/opensource_analyst/models/conversation.py` | Pydantic 模型（请求/响应/ReasoningStep） |
| Chat Frontend | `src/opensource_analyst/frontend/chat.html` | 三栏交互式聊天 UI（SSE 流式 + Mermaid 渲染 + 推理轨迹面板） |
| BaseAgent 增强 | `src/opensource_analyst/agents/base.py` | 新增 invoke_messages()、bind_tools()、llm 属性 |
| main.py 更新 | `src/opensource_analyst/main.py` | 注册 conversation router + 挂载 frontend + 版本→0.2.0 |
| graph/__init__.py 更新 | `src/opensource_analyst/graph/__init__.py` | 导出 conversation graph + ConversationState |
| 测试 | `tests/test_conversation_state.py` | 10 个测试（模型 + State + Prompt） |
| 测试 | `tests/test_conversation_api.py` | 10 个测试（SessionStore + API） |

### 9.11.2 测试结果

```
全量：128 + 20 = 148 PASSED（零回归）
  M13 新增 20 tests（全部纯单元，无 LLM 依赖）:
    test_conversation_state.py: 10 tests (模型 / State / Prompt)
    test_conversation_api.py:   10 tests (SessionStore 全部方法 + API 模型)
```

### 9.11.3 核心架构

```
POST /analyze (M0-M12 管线) → 分析结果存入 _store
    │
    ▼
POST /conversation/start → 从 _store 加载结果 → 压缩为文本摘要 → 创建会话
    │
    ▼
POST /conversation/{id}/message → ReAct 对话图
    │
    ▼
call_model → LLM (含 search_code + MCP tools) → AIMessage
    │                    │
    │  无 tool_calls   有 tool_calls
    │                    │
    ▼                    ▼
  END               tool_node (执行 search_code / MCP call)
                        │
                        ▼
                   ToolMessage → call_model (循环继续)
```

### 9.11.4 对话工具

| 工具 | 来源 | 用途 |
|------|------|------|
| search_code | CodeRetriever + VectorStore | 语义搜索代码片段 |
| call_mcp_* | MCPClientManager → StructuredTool | 调用外部 MCP 工具（动态注入） |

### 9.11.5 新增 API 端点

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/conversation/start` | 基于 task_id 创建会话 |
| POST | `/conversation/{id}/message` | 发送消息，返回回复 + 推理步骤 |
| GET | `/conversation/{id}/stream` | SSE 流式输出 |
| GET | `/conversation/{id}/history` | 对话历史 |
| DELETE | `/conversation/{id}` | 删除会话 |

### 9.11.6 前端 (chat.html)

- **访问**：`http://localhost:8000/chat`
- **三栏布局**：左侧分析摘要 + 中间对话流 + 右侧推理轨迹
- **流程**：输入 GitHub URL → 自动调 /analyze → 轮询状态 → 自动创建对话 → 开始聊天
- **SSE 流式**：打字效果 + 工具调用实时展示
- **Mermaid 渲染**：内联渲染 Mermaid 图
- **Markdown 渲染**：marked.js 渲染 + 代码高亮

### 9.11.7 技术要点

- **两图分离**：分析图（build_workflow）和对话图（build_conversation_graph）完全独立，零侵入
- **单 Agent ReAct**：仅 2 个工具（search_code + MCP），DeepSeek function calling 风险极低
- **分析摘要注入**：AnalysisResult 压缩为文本注入系统提示词，避免上下文膨胀
- **MCP 动态注入**：MCP 工具列表序列化到 ConversationState，tool_node 动态还原执行
- **模块级共享 MCPManager**：API 层设置 set_mcp_manager()，图内通过 _shared_mcp_manager 调用
- **Session 复用 analyze 内存存储**：conversation API 读取 api/analyze.py 的 task _store 获取分析结果

---

## 十、快速启动命令

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

## 十一、开发规范速查

- **设计优先**：每个功能先输出设计文档，确认后再编码
- **类型完整**：所有函数使用类型注解
- **Pydantic**：禁止返回裸字典，使用 Pydantic 模型
- **依赖注入**：禁止大量全局变量
- **单一职责**：一个 Agent 一个文件
- **编写测试**：每个核心模块必须有测试

---

*本文件由 AI 维护，每次里程碑完成后更新。*
