# OpenSource Analyst Agent

输入 GitHub 仓库 URL，自动生成项目概览、技术栈分析、架构分析、学习路线、面试知识点、Mermaid 可视化图。支持交互式对话问答（ReAct Agent + RAG 语义搜索 + MCP 工具）。

## 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | FastAPI + Uvicorn |
| Agent 编排 | LangGraph 1.2+ (StateGraph + ReAct) |
| LLM | LangChain + ChatOpenAI (DeepSeek API, temperature=0.3) |
| Embedding | DashScope text-embedding-v3 (1024 维) |
| 向量数据库 | ChromaDB 1.5+ |
| HTTP | HTTPX 0.28+ |
| 数据模型 | Pydantic v2 |
| 包管理 | uv |
| 运行时 | Python 3.14 |

## 功能架构

```
输入 GitHub URL
    │
    ▼
┌─────────────────────────────────────────────────┐
│  LangGraph 分析工作流 (M0-M12)                    │
│                                                   │
│  load_repo → index_code → retrieve_context        │
│                                │                  │
│                     coordinator (并行调度)         │
│                       ├─ dependency (M7)          │
│                       ├─ architecture (M8)        │
│                       ├─ analyze (M3)             │
│                       ├─ learning (M9)            │
│                       ├─ mermaid (M12)            │
│                       ├─ interview (M12)          │
│                       └─ reflection (M12)         │
│                                                   │
│  输出: AnalysisResult (结构化报告)                 │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  ReAct 对话引擎 (M13)                             │
│                                                   │
│  用户提问 → LLM (分析摘要 + 历史上下文)             │
│              ├─ search_code (RAG 检索)            │
│              └─ call_mcp (外部工具)               │
│                                                    │
│  输出: 自然语言回答 + 推理步骤可视化                │
└─────────────────────────────────────────────────┘
```

## 项目结构

```
src/opensource_analyst/
├── main.py              # FastAPI 入口 (/, /health, /chat, /dashboard)
├── api/                  # REST API 路由
│   ├── analyze.py        # POST /analyze — 发起分析 (BackgroundTasks)
│   ├── task.py           # GET /task/{id}, /task/{id}/result — 状态与结果
│   ├── chat.py           # POST /chat — RAG 对话
│   ├── conversation.py   # M13: 对话端点 (start/message/stream/history)
│   └── session.py        # M13: 内存对话会话管理
├── agents/               # Agent 实现 (一个文件一个 Agent)
│   ├── base.py           # BaseAgent (LLM 封装) + Analyzer
│   ├── dependency.py     # M7: 依赖解析 Agent
│   ├── architecture.py   # M8: 架构分析 Agent
│   ├── learning.py       # M9: 学习路线 Agent
│   ├── interview.py      # M12: 面试题 Agent
│   ├── reflection.py     # M12: 质量自检 Agent
│   ├── registry.py       # M10: Agent 注册表 + 声明式调度
│   ├── coordinator.py    # M10: 并行调度引擎
│   └── react_agent.py    # M13: ReAct 对话 Agent
├── graph/                # LangGraph 工作流
│   ├── state.py          # 分析图状态 (GraphState, 15 字段)
│   ├── nodes.py          # 11 个工作流节点 + Agent 注册
│   ├── workflow.py       # build_workflow() + Mermaid 导出
│   ├── conversation.py   # M13: ReAct 对话图 (call_model ⇄ tool_node)
│   └── conversation_state.py # M13: 对话状态 (add_messages reducer)
├── github/               # GitHub API 客户端
│   ├── client.py         # GitHubClient (认证、异常、URL 解析)
│   ├── readme.py         # ReadmeFetcher
│   ├── parser.py         # RepoParser (文件树 + 语言统计)
│   ├── dependency_parser.py # M7: 多语言依赖文件解析
│   └── architecture_analyzer.py # M8: AST import 提取 + 模块分组
├── rag/                  # RAG 检索引擎
│   ├── indexer.py        # CodeIndexer (文件过滤 + 分块 + ChromaDB 索引)
│   └── retriever.py      # CodeRetriever (语义搜索 + 上下文拼接)
├── mcp/                  # MCP 集成能力层
│   ├── config.py         # MCPServerConfig / MCPToolInfo / MCPToolResult
│   ├── client.py         # MCPServerConnection + MCPClientManager
│   └── tool_bridge.py    # M13: MCP → LangChain StructuredTool 桥接
├── analysis/             # 静态分析工具
│   ├── __init__.py
│   └── mermaid.py        # M12: 三种 Mermaid 图生成
├── prompts/              # LLM 提示词模板
│   ├── overview.py       # 项目概览 + 技术栈分析
│   ├── dependency.py     # M7: 依赖分析
│   ├── architecture.py   # M8: 架构分析
│   ├── learning.py       # M9: 学习路线
│   ├── interview.py      # M12: 面试题
│   ├── reflection.py     # M12: 质量自检
│   ├── conversation.py   # M13: ReAct 对话系统提示词
│   └── chat.py           # RAG 问答
├── frontend/
│   └── index.html        # M13: 三栏交互式聊天 UI
├── vectorstore/
│   └── chroma.py         # DashScopeEmbeddings + VectorStore
└── models/               # Pydantic 数据模型
    ├── repo.py           # RepoInfo
    ├── analysis.py       # AnalysisResult + 15 子模型
    ├── task.py           # AnalyzeRequest / TaskStatus / TaskResult
    ├── chat.py           # ChatRequest / ChatResponse / SourceInfo
    └── conversation.py   # M13: 对话请求/响应模型
```

## 快速开始

```bash
# 1. 配置环境变量
# 编辑 .env 填入:
#   DEEPSEEK_API_KEY=你的 DeepSeek Key
#   GITHUB_TOKEN=你的 GitHub Token
#   DASH_SCOPE_API_KEY=你的阿里百炼 Key

# 2. 安装依赖
uv sync

# 3. 启动服务
uv run uvicorn src.opensource_analyst.main:app --reload

# 4. 打开浏览器
#    http://127.0.0.1:8000/chat  → 交互式分析 + 对话 UI
#    http://127.0.0.1:8000/docs  → API 文档
```

## API 端点

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/` | 服务状态 |
| GET | `/health` | 健康检查 |
| POST | `/analyze` | 发起仓库分析 |
| GET | `/task/{id}` | 查询分析状态 |
| GET | `/task/{id}/result` | 获取分析结果 |
| POST | `/chat` | RAG 代码问答 |
| POST | `/conversation/start` | 创建对话会话 |
| POST | `/conversation/{id}/message` | 发送对话消息 |
| GET | `/conversation/{id}/stream` | SSE 流式对话 |
| GET | `/conversation/{id}/history` | 对话历史 |
| DELETE | `/conversation/{id}` | 删除会话 |
| GET | `/chat` | 前端页面 |

**使用示例：**

```bash
# 发起分析
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/msiemens/tinydb"}'

# 返回 {"task_id": "a1b2c3d4e5f6", "status": "pending"}

# 轮询状态
curl http://localhost:8000/task/a1b2c3d4e5f6

# 获取结果
curl http://localhost:8000/task/a1b2c3d4e5f6/result
```

## 测试

```bash
# 全量测试 (148+ tests)
uv run pytest

# 单模块测试
uv run pytest tests/test_github.py -v
uv run pytest tests/test_agent.py -v
uv run pytest tests/test_rag.py -v
uv run pytest tests/test_coordinator.py -v
uv run pytest tests/test_conversation_api.py -v
```

## 里程碑

| 阶段 | 名称 | 状态 |
|------|------|------|
| M0 | 环境搭建 | ✅ |
| M1 | 项目设计 | ✅ |
| M2 | GitHub 仓库读取 | ✅ |
| M3 | 单 Agent 分析 | ✅ |
| M4 | Repository RAG | ✅ |
| M5 | FastAPI 接口 | ✅ |
| M6 | LangGraph 工作流 | ✅ |
| M7 | Dependency Agent | ✅ |
| M8 | Architecture Agent | ✅ |
| M9 | Learning Agent | ✅ |
| M10 | Coordinator Agent | ✅ |
| M11 | MCP 集成 | ✅ |
| M12 | 高级功能 (Mermaid/面试/反思) | ✅ |
| M13 | 交互式对话 (ReAct + 前端) | ✅ |

## 前端界面

访问 `http://localhost:8000/chat`：

- **左栏 — 分析报告**：Overview / Tech Stack(语言条形图) / Architecture(可展开模块卡片) / Learning Path(时间线) / Interview Questions / Mermaid 图 / Reflection(评分环)
- **中栏 — 对话**：Markdown 渲染消息 + 打字动画
- **右栏 — 推理轨迹**：竖向时间线 — Tool Call / Observation / Thought 每步可视化

## 开发规范

- **设计优先**：每个功能先输出设计文档，确认后再编码
- **类型完整**：所有函数使用类型注解
- **Pydantic**：禁止返回裸字典
- **单一职责**：一个 Agent 一个文件
- **Git 提交**：使用中文备注
