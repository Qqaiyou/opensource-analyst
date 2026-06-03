# Development Roadmap — OpenSource Analyst

> 版本：v0.1.0
> 日期：2026-06-02
> 状态：Draft

---

## 1. 里程碑总览

```text
M0      M1      M2      M3      M4      M5      M6      M7      M8      M9      M10     M11     M12
环境    设计    GitHub  单Agent  RAG    FastAPI LangGraph Dep    Arch   Learn  Coord   MCP    高级
 ✅      ◆      ○       ○       ○       ○       ○       ○       ○       ○       ○       ○       ○
```

| 阶段 | 名称 | 状态 | 预计工时 | 核心产出 |
|------|------|------|----------|---------|
| M0 | 环境搭建 | ✅ 已完成 | 0.5d | Python 3.14 + uv + FastAPI + LangGraph + ChromaDB |
| M1 | 项目设计 | ◆ 进行中 | 1d | PRD.md + ARCHITECTURE.md + ROADMAP.md |
| M2 | GitHub 仓库读取 | ⏳ | 1d | github/ 模块，API 返回 readme + languages |
| M3 | 单 Agent 分析 | ⏳ | 1.5d | POST /analyze，基于 README 输出分析结果 |
| M4 | Repository RAG | ⏳ | 2d | 代码索引 + 语义检索 + 仓库问答 |
| M5 | FastAPI 接口完善 | ⏳ | 1d | 异步任务 API + Swagger 文档 |
| M6 | LangGraph 工作流 | ⏳ | 2d | StateGraph + 4 个 Node 顺序执行 |
| M7 | Dependency Agent | ⏳ | 1.5d | 依赖文件解析 + 技术栈深度分析 |
| M8 | Architecture Agent | ⏳ | 2d | 模块分析 + 架构关系梳理 |
| M9 | Learning Agent | ⏳ | 1d | 学习路线 + 面试知识点 |
| M10 | Coordinator Agent | ⏳ | 2d | 多 Agent 动态调度 + 并行执行 |
| M11 | MCP 集成 | ⏳ | 2d | 3 个 MCP Server 接入 |
| M12 | 高级功能 | ⏳ | 2d | Mermaid 图 + Interview Agent + Reflection |
| **总计** | | | **~19.5d** | |

---

## 2. 阶段依赖关系

```text
M0 环境
 │
 M1 设计
 │
 M2 GitHub 读取 ─────────────┐
 │                           │
 M3 单 Agent ────┐           │
 │               │           │
 M4 RAG ────────┐│           │
 │              ││           │
 M5 FastAPI ────┤│           │
 │              ││           │
 M6 LangGraph ──┘│           │
 │               │           │
 │    ┌──────────┘           │
 │    │                      │
 M7 Dep Agent                │
 │    │                      │
 M8 Arch Agent               │
 │    │                      │
 M9 Learn Agent              │
 │    │                      │
 M10 Coordinator ────────────┘
 │
 M11 MCP
 │
 M12 高级
```

关键依赖说明：

| 被依赖 | 依赖它的阶段 | 原因 |
|--------|-------------|------|
| M2 GitHub 读取 | M3~M12 | 所有分析都需要仓库数据 |
| M6 LangGraph | M10 Coordinator | Coordinator 是 LangGraph 的动态路由升级版 |
| M7 Dep Agent | M9 Learn Agent | 学习路线需要知道技术栈 |
| M8 Arch Agent | M9 Learn Agent | 学习路线需要知道模块结构 |
| M7+8+9 Agent | M10 Coordinator | Coordinator 调度这些 Agent |

---

## 3. 分阶段详细计划

### 3.1 第一阶段：基础能力（M0-M3）

**目标**：跑通"输入 GitHub URL → 输出分析结果"的最简链路。

| 里程碑 | 详细任务 | 技术要点 |
|--------|---------|---------|
| **M2** GitHub 读取 | ① 实现 GitHub API 客户端 ② 抓取 README ③ 获取文件树 ④ 获取语言统计 | HTTPX 异步请求、GitHub REST API v3、错误处理（404/私有仓库/限流）|
| **M3** 单 Agent | ① 设计 LLM Prompt 模板 ② 创建基础 Agent 类 ③ 调用 LLM 分析 README ④ 返回结构化结果 | LangChain ChatModel、PromptTemplate、Pydantic OutputParser |

**M3 完成时**，用户可以：
```bash
curl -X POST http://localhost:8000/analyze \
  -d '{"repo_url": "https://github.com/langchain-ai/langgraph"}'
# 返回 JSON: { overview, tech_stack }
```

### 3.2 第二阶段：智能增强（M4-M6）

**目标**：从"只看 README"升级为"理解全部代码"。

| 里程碑 | 详细任务 | 技术要点 |
|--------|---------|---------|
| **M4** RAG | ① 递归抓取仓库代码文件 ② 文本分块策略 ③ Embedding 向量化 ④ ChromaDB 存储 ⑤ 语义检索接口 | RecursiveCharacterTextSplitter、OpenAI Embeddings、ChromaDB CRUD |
| **M5** FastAPI | ① 异步任务管理（内存队列）② GET /task/{id} 状态查询 ③ 请求/响应 Pydantic 模型 ④ Swagger 文档完善 | BackgroundTasks、asyncio、Pydantic v2 |
| **M6** LangGraph | ① 定义 GraphState ② 实现 4 个 Node ③ 构建 StateGraph ④ 顺序执行流水线 ⑤ 可视化工作流图 | StateGraph.add_node/add_edge、compile()、Mermaid 图导出 |

**M6 完成时**，系统有了完整的处理流水线：
```
LoadRepo → Analyze → Architecture → Learning
```

### 3.3 第三阶段：专家 Agent（M7-M9）

**目标**：每个分析维度由一个专业 Agent 负责。

| 里程碑 | 详细任务 | 技术要点 |
|--------|---------|---------|
| **M7** Dependency | ① 多语言依赖文件解析器（Python/JS/Java/Go）② 依赖分类（核心/测试/构建）③ 版本分析 | AST/TOML/JSON/XML 解析 |
| **M8** Architecture | ① 目录结构分析算法 ② 模块职责推断 ③ 入口文件识别 ④ 模块间 import 关系 | 静态代码分析、import 图 |
| **M9** Learning | ① 依赖拓扑排序 ② 阅读顺序生成 ③ 重点文件标记 ④ 面试题 LLM 生成 | 图算法、Prompt Engineering |

**每个 Agent 单独可测试**：
```bash
uv run pytest tests/test_dependency_agent.py -v
uv run pytest tests/test_architecture_agent.py -v
uv run pytest tests/test_learning_agent.py -v
```

### 3.4 第四阶段：系统集成（M10-M12）

**目标**：多 Agent 协作 + 外部工具 + 可视化。

| 里程碑 | 详细任务 | 技术要点 |
|--------|---------|---------|
| **M10** Coordinator | ① 任务分析（判断需要哪些 Agent）② 动态路由（条件边）③ 并行 Agent 执行 ④ 结果融合 | LangGraph conditional_edges、Send API、并行 fan-out |
| **M11** MCP | ① MCP Client 封装 ② GitHub MCP Server 接入 ③ Filesystem MCP Server 接入 ④ Browser MCP Server 接入 | MCP 协议、Tool 注册与发现 |
| **M12** 高级 | ① Mermaid 代码生成 ② Interview Agent ③ Reflection 检查 ④ 分析报告 Markdown 导出 | Mermaid.js 语法、Self-reflection Prompt |

---

## 4. 技术选型说明

### 4.1 LLM 提供商

| 选项 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| OpenAI (GPT-4o) | 速度快、生态好 | 成本较高 | **默认选择** |
| Claude (Anthropic) | 代码理解强 | API 兼容需适配 | **OpenAI Compatible 模式接入** |
| 本地模型 (Ollama) | 免费 | 效果差、速度慢 | 预留接口，不优先支持 |

**决策**：使用 LangChain 的 `ChatOpenAI`，通过 `base_url` 参数兼容任何 OpenAI Compatible API。用户通过环境变量切换。

### 4.2 向量数据库

| 选项 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| **ChromaDB** | 轻量、嵌入式、Python 原生 | 大规模性能不如 PGVector | **MVP 选择** |
| PostgreSQL + pgvector | 生产级、可扩展 | 需要额外服务 | 后续升级路径 |

### 4.3 部署方式

| 阶段 | 方式 | 命令 |
|------|------|------|
| 开发 | uvicorn hot-reload | `uv run uvicorn src.opensource_analyst.main:app --reload` |
| 生产 | Docker + uvicorn | `docker-compose up`（M12 后提供） |

---

## 5. 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| LLM 输出格式不稳定 | 高 | 分析结果不可用 | Pydantic OutputParser + retry + fallback |
| GitHub API 限流（60 req/h 无 Token）| 高 | 无法获取仓库数据 | 要求用户配置 GITHUB_TOKEN 环境变量 |
| 大型仓库分析超时 | 中 | 请求失败 | 文件大小限制 + 增量索引 + 超时告警 |
| LangGraph API 变更 | 低 | 代码不兼容 | 锁定版本号（1.2+）+ 升级前阅读 Changelog |
| ChromaDB 持久化损坏 | 低 | 向量数据丢失 | 按 repo_url hash 分 Collection，可重建索引 |
| LLM 成本过高 | 中 | 无法规模化使用 | 缓存分析结果 + 支持本地模型 + Token 预算控制 |
| MCP 协议不稳定 | 中 | M11 进度受阻 | M11 标记为"实验性"，核心流程不依赖 MCP |

---

## 6. Git 分支策略

```text
main
 │
 ├── m1-project-design        ← 当前阶段
 ├── m2-github-reader
 ├── m3-single-agent
 ├── m4-rag
 ├── ...
 └── m12-advanced

每个里程碑：
  1. git checkout -b mX-xxx
  2. 开发 + 测试
  3. git commit
  4. 合并回 main
  5. 打 tag: v0.X.0
```

提交信息格式：`<type>: <中文描述>`，如 `feat: 新增 GitHub 客户端，支持抓取 README`。

---

## 7. 验收标准总览

| 里程碑 | 验收条件 |
|--------|---------|
| M0 ✅ | `uv run uvicorn` 启动成功，`/` 和 `/health` 可访问 |
| M1 | 三份设计文档完整，内部一致，无拼写错误 |
| M2 | `github/` 模块可独立调用，返回 `{readme, languages, file_tree}` |
| M3 | `POST /analyze` 返回 `{overview, tech_stack}`，非 README 原文照搬 |
| M4 | 对目标仓库提问能引用具体代码片段回答 |
| M5 | Swagger UI 可交互，异步任务状态可查询 |
| M6 | LangGraph 流程图可导出，4 个 Node 按序执行 |
| M7 | `DependencyAgent` 能正确解析 pom.xml/package.json/pyproject.toml |
| M8 | `ArchitectureAgent` 能识别模块划分和入口文件 |
| M9 | `LearningAgent` 生成的阅读顺序符合项目实际结构 |
| M10 | 用户一次请求，多个 Agent 自动协作，无需手动调用 |
| M11 | Agent 能通过 MCP 读取真实的 GitHub Issue |
| M12 | 输出包含 Mermaid 图 + 面试题；Reflection 能发现遗漏并补充 |

---

## 8. 目标测试用例

完成 M12 后，以下三个开源项目应能分析通过：

```text
1. langgraph       (Python, 中等规模, LangChain 生态)
   https://github.com/langchain-ai/langgraph

2. spring-ai       (Java, 中大规模, Spring 生态)
   https://github.com/spring-projects/spring-ai

3. hermes           (Rust/Go, 小规模, 消息系统)
   https://github.com/hermes/hermes
```

---

*本文档随里程碑推进持续更新。*
