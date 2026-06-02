# Architecture Design Document — OpenSource Analyst

> 版本：v0.1.0
> 日期：2026-06-02
> 状态：Draft

---

## 1. 架构总览

### 1.1 系统分层

```text
┌─────────────────────────────────────────────────────────────┐
│                      接入层 (API Layer)                      │
│                   FastAPI + Uvicorn + Swagger                │
│              POST /analyze   GET /task/{id}   GET /health    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    编排层 (Orchestration Layer)               │
│                        LangGraph StateGraph                  │
│                   Coordinator Agent (任务拆分 & 调度)         │
└───┬──────────┬──────────┬──────────┬────────────────────────┘
    │          │          │          │
┌───▼──┐  ┌───▼──┐  ┌───▼──┐  ┌───▼──┐
│ Repo │  │ Dep  │  │ Arch │  │Learn │  ← 专家 Agent 层
│Agent │  │Agent │  │Agent │  │Agent │    (Expert Agent Layer)
└──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
   │         │         │         │
┌──▼─────────▼─────────▼─────────▼────────────────────────────┐
│                      能力层 (Capability Layer)               │
├──────────────┬──────────────────┬───────────────────────────┤
│  GitHub 读取  │   RAG 检索引擎    │     MCP 工具集成           │
│  (github/)   │    (rag/)        │     (mcp/)                │
│  README      │  ChromaDB        │  GitHub MCP / Filesystem   │
│  文件树       │  Embedding       │  MCP / Browser MCP        │
│  语言统计     │  Semantic Search │                           │
└──────────────┴──────────────────┴───────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      数据层 (Data Layer)                     │
│          ChromaDB (向量)  +  Pydantic Models (结构)          │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **分层解耦** | 接入层、编排层、Agent 层、能力层各司其职，上层依赖下层 |
| **Agent 单一职责** | 每个 Agent 只负责一个分析维度，新增维度 = 新增 Agent 文件 |
| **State 驱动** | 所有 Agent 通过共享的 GraphState 通信，不直接互相调用 |
| **能力注入** | RAG、GitHub、MCP 作为能力注入到 Agent，Agent 不直接实现底层逻辑 |

---

## 2. Agent 系统架构

### 2.1 Agent 角色定义

```text
                          ┌──────────────────┐
                          │ CoordinatorAgent │
                          │                  │
                          │  接收分析请求     │
                          │  拆分为子任务     │
                          │  调度 Expert Agent │
                          │  汇总分析结果     │
                          └──┬───┬───┬───┬──┘
                             │   │   │   │
          ┌──────────────────┘   │   │   └──────────────────┐
          ▼                      ▼   ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   RepoAgent     │  │ DependencyAgent │  │ArchitectureAgent│
│                 │  │                 │  │                 │
│ 抓取 README     │  │ 解析依赖文件     │  │ 分析目录结构     │
│ 获取文件树      │  │ 识别技术栈       │  │ 识别模块职责     │
│ 统计语言占比    │  │ 分析依赖作用     │  │ 梳理模块关系     │
│ 提取元数据      │  │ 识别核心框架     │  │ 定位入口文件     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                             │
                             ▼
          ┌─────────────────────────────────┐
          │         LearningAgent           │
          │                                 │
          │ 基于架构分析结果生成学习路线      │
          │ 按依赖关系排序阅读顺序            │
          │ 标记重点文件和可跳过文件          │
          │ 提取面试相关的核心技术点          │
          └─────────────────────────────────┘
```

### 2.2 Agent 通信机制

Agent 之间**不直接通信**，通过 LangGraph State 共享数据：

```text
┌──────────────┐    写入     ┌─────────────────┐    读取    ┌──────────────┐
│  RepoAgent   │ ──────────→ │                 │ ←────────── │ ArchAgent    │
└──────────────┘             │  GraphState     │             └──────────────┘
                             │                 │
┌──────────────┐    写入     │ repo_url        │    读取    ┌──────────────┐
│  DepAgent    │ ──────────→ │ repo_data       │ ←────────── │ LearnAgent   │
└──────────────┘             │ tech_stack      │             └──────────────┘
                             │ architecture    │
                             │ learning_path   │
                             │ interview_qa    │
                             │ status          │
                             └─────────────────┘
```

---

## 3. LangGraph 工作流设计

### 3.1 StateGraph 定义

```text
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  load_repo  │  ← RepoAgent
                    │  Node       │    抓取仓库数据
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  analyze    │  ← DependencyAgent
                    │  Node       │    技术栈 & 依赖分析
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ architecture│  ← ArchitectureAgent
                    │  Node       │    模块 & 架构分析
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  learning   │  ← LearningAgent
                    │  Node       │    学习路线 & 面试点
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    END      │
                    └─────────────┘
```

### 3.2 GraphState 字段定义

```python
from typing import TypedDict, Optional, Any

class GraphState(TypedDict):
    # 输入
    repo_url: str                          # 用户输入的 GitHub URL

    # RepoAgent 产出
    repo_data: Optional[dict]              # README, file_tree, languages

    # DependencyAgent 产出
    tech_stack: Optional[dict]             # 语言、框架、依赖列表

    # ArchitectureAgent 产出
    architecture: Optional[dict]           # 模块、入口、模块关系

    # LearningAgent 产出
    learning_path: Optional[list]          # 分步阅读路线
    interview_qa: Optional[list]           # 面试知识点
    reading_suggestions: Optional[dict]    # 必读 / 可跳过

    # 流程控制
    status: str                            # "loading" | "analyzing" | "completed" | "error"
    error_message: Optional[str]           # 错误信息
```

### 3.3 条件路由（M10 阶段扩展）

到 M10 Coordinator Agent 阶段，analyze node 升级为动态路由：

```text
                    ┌─────────────┐
                    │  load_repo  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ coordinator │  ← 动态决策：需要哪些 Agent？
                    └──┬──┬──┬───┘
                       │  │  │
              ┌────────┘  │  └────────┐
              ▼           ▼           ▼
        ┌────────┐ ┌────────┐ ┌────────┐
        │  dep   │ │  arch  │ │ learn  │  ← 并行执行
        └───┬────┘ └───┬────┘ └───┬────┘
            │          │          │
            └──────────┼──────────┘
                       ▼
                ┌─────────────┐
                │   summarize │  ← 汇总结果
                └──────┬──────┘
                       │
                       ▼
                     END
```

---

## 4. RAG 流水线设计

### 4.1 索引阶段（离线 / 首次分析时执行）

```text
GitHub 仓库
    │
    ▼
┌──────────────┐
│ 文件抓取      │  ← GitHub API: README + src/ + docs/ + 配置文件
│ (github/)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 文本分块      │  ← RecursiveCharacterTextSplitter (chunk_size=1000)
│ (Chunking)   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 向量嵌入      │  ← OpenAI Embedding / 兼容接口
│ (Embedding)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 向量存储      │  ← ChromaDB (persist 到本地磁盘)
│ (ChromaDB)   │
└──────────────┘
```

### 4.2 检索阶段（每次查询时执行）

```text
用户查询: "这个项目怎么实现 Tool Calling？"
    │
    ▼
┌──────────────┐
│ Query Embed   │  ← 将查询转为向量
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Semantic      │  ← ChromaDB.similarity_search(k=5)
│ Search        │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Context       │  ← 将检索到的代码片段拼接为上下文
│ Assembly      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ LLM Generate  │  ← Prompt: 上下文 + 用户问题 → 生成回答
└──────────────┘
```

---

## 5. MCP 集成设计

### 5.1 MCP Server 列表

```text
┌─────────────────────────────────────────────────────┐
│                  MCP Client (mcp/)                   │
│                                                     │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ GitHub MCP    │  │ Filesystem   │  │ Browser   │ │
│  │ Server        │  │ MCP Server   │  │ MCP Server│ │
│  ├───────────────┤  ├──────────────┤  ├───────────┤ │
│  │ • Issues      │  │ • 读取本地   │  │ • 搜索    │ │
│  │ • PRs         │  │   代码文件   │  │ • 抓取    │ │
│  │ • Releases    │  │ • 写分析     │  │   网页    │ │
│  │ • Commits     │  │   结果文件   │  │ • 官方    │ │
│  │ • Search      │  │              │  │   文档    │ │
│  └───────────────┘  └──────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────┘
```

### 5.2 Agent 调用 MCP 的流程

```text
Agent: "我想知道最近 10 个 Issue 有哪些 bug"
   │
   ▼
LangGraph ToolNode
   │
   ▼
MCP Client → GitHub MCP Server → GitHub API
   │
   ▼
返回 Issue 列表 → Agent 分析 → 写入 GraphState
```

---

## 6. API 接口设计

### 6.1 端点列表

| 方法 | 路径 | 描述 | 里程碑 |
|------|------|------|--------|
| `GET` | `/` | 服务状态 | M0 ✅ |
| `GET` | `/health` | 健康检查 | M0 ✅ |
| `POST` | `/analyze` | 发起分析任务 | M5 |
| `GET` | `/task/{task_id}` | 查询任务状态 | M5 |
| `GET` | `/task/{task_id}/result` | 获取分析结果 | M5 |

### 6.2 异步任务模型

```text
POST /analyze {repo_url}
       │
       ▼
  ┌─────────────┐
  │ 创建 task_id │  ← UUID
  │ status=pending│
  └──────┬──────┘
         │
         ├──→ 立即返回 {"task_id": "xxx", "status": "pending"}
         │
         ▼
  ┌─────────────┐
  │ 后台执行     │  ← LangGraph Workflow
  │ 分析流水线   │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ status=done │  ← 结果写入内存/文件
  └─────────────┘

GET /task/{task_id}
  → {"task_id": "xxx", "status": "running|done|error"}

GET /task/{task_id}/result
  → 完整的分析结果 JSON
```

---

## 7. 数据流全链路

### 7.1 请求生命周期

```text
用户输入 GitHub URL
        │
        ▼
   FastAPI Router  ──→  参数校验 (Pydantic)
        │
        ▼
   创建 Task，返回 task_id，启动后台任务
        │
        ▼
   LangGraph Workflow 启动
        │
        ├──[1] RepoAgent ──→ GitHub API ──→ README + file_tree + languages
        │                                      │
        ├──[2] RAG Indexer ──→ 代码分块 ──→ ChromaDB 向量存储
        │                                      │
        ├──[3] DependencyAgent ──→ 解析依赖文件 ──→ tech_stack
        │                                      │
        ├──[4] ArchitectureAgent ──→ 分析目录 + RAG 检索 ──→ architecture
        │                                      │
        ├──[5] LearningAgent ──→ 生成学习路线 + 面试题
        │                                      │
        └──[6] 结果汇总 ──→ GraphState 完整写入 ──→ 返回 JSON
```

### 7.2 数据依赖关系

```text
repo_url ────→ RepoAgent ────→ repo_data
                                    │
                    ┌───────────────┤
                    ▼               ▼
            DependencyAgent   ArchitectureAgent
                    │               │
                    ▼               ▼
              tech_stack      architecture
                    │               │
                    └───────┬───────┘
                            ▼
                     LearningAgent
                            │
                    ┌───────┴───────┐
                    ▼               ▼
              learning_path   interview_qa
```

---

## 8. 目录结构映射

```text
opensource-analyst/                    ← 项目根
│
├── docs/                             ← 设计文档（M1 产出）
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
│
├── src/opensource_analyst/           ← 主包
│   │
│   ├── main.py                       ← FastAPI app 入口 + 路由注册
│   │
│   ├── api/                          ← 接入层：REST 路由
│   │   ├── analyze.py                ← POST /analyze
│   │   └── task.py                   ← GET /task/{id}
│   │
│   ├── agents/                       ← Agent 层：每个 Agent 一个文件
│   │   ├── base.py                   ← Agent 基类（LLM 初始化、通用逻辑）
│   │   ├── coordinator.py            ← CoordinatorAgent（M10）
│   │   ├── repo.py                   ← RepoAgent（M2）
│   │   ├── dependency.py             ← DependencyAgent（M7）
│   │   ├── architecture.py           ← ArchitectureAgent（M8）
│   │   └── learning.py               ← LearningAgent（M9）
│   │
│   ├── graph/                        ← 编排层：LangGraph 工作流
│   │   ├── state.py                  ← GraphState 定义
│   │   ├── workflow.py               ← StateGraph 构建（nodes + edges）
│   │   └── nodes.py                  ← 各 Node 实现
│   │
│   ├── rag/                          ← 能力层：RAG 检索
│   │   ├── indexer.py                ← 代码分块 + 向量化
│   │   ├── retriever.py              ← 语义检索
│   │   └── embeddings.py             ← Embedding 模型封装
│   │
│   ├── github/                       ← 能力层：GitHub 数据获取
│   │   ├── client.py                 ← GitHub API 客户端
│   │   ├── readme.py                 ← README 获取 & 解析
│   │   └── parser.py                 ← 文件树 + 语言统计
│   │
│   ├── mcp/                          ← 能力层：MCP 集成
│   │   ├── client.py                 ← MCP Client 封装
│   │   └── tools.py                  ← MCP Tool 注册
│   │
│   ├── vectorstore/                  ← 能力层：向量存储
│   │   └── chroma.py                 ← ChromaDB 初始化 + CRUD
│   │
│   ├── models/                       ← 数据层：Pydantic 模型
│   │   ├── repo.py                   ← RepoInfo, FileTree, LanguageStats
│   │   ├── analysis.py               ← AnalysisResult（全部 6 个板块）
│   │   └── task.py                   ← TaskStatus, TaskResult
│   │
│   └── prompts/                      ← 提示词模板
│       ├── overview.py               ← 项目概览 prompt
│       ├── dependency.py             ← 依赖分析 prompt
│       ├── architecture.py           ← 架构分析 prompt
│       └── learning.py               ← 学习路线 prompt
│
└── tests/                            ← 测试
    ├── test_github.py
    ├── test_agents.py
    ├── test_graph.py
    └── test_rag.py
```

---

## 9. 技术选型说明

| 决策 | 选择 | 原因 |
|------|------|------|
| LLM 框架 | LangChain + LangGraph | StateGraph 原生支持 Agent 工作流编排 |
| Web 框架 | FastAPI | 异步原生支持 + 自动 Swagger + Pydantic 集成 |
| 向量库 | ChromaDB | 轻量、Python 原生、无需外部服务 |
| LLM 提供商 | OpenAI Compatible API | 可切换 OpenAI / Claude / 本地模型 |
| HTTP 客户端 | HTTPX | 异步 + HTTP/2 + 连接池 |
| 数据校验 | Pydantic v2 | FastAPI 原生集成，禁止裸字典 |
| 包管理 | uv | 10x faster than pip，锁定文件可靠 |
| 异步处理 | asyncio + background tasks | MVP 阶段用内存队列，后续可升级 Celery/Redis |

---

## 10. 安全设计

| 关注点 | 措施 |
|------|------|
| **URL 校验** | 仅允许 github.com 域名，防止 SSRF |
| **Token 管理** | GitHub Token 从环境变量读取，不硬编码 |
| **LLM API Key** | 从环境变量读取，不写入配置文件 |
| **输入限制** | 限制仓库大小（文件数、总大小），防止资源耗尽 |
| **速率限制** | API 层限流，防止滥用 |
| **错误信息** | 生产环境不暴露内部堆栈信息 |

---

*本文档随项目演进持续更新。*
