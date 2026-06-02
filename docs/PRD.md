# Product Requirements Document — OpenSource Analyst

> 版本：v0.1.0
> 日期：2026-06-02
> 状态：Draft

---

## 1. 产品概述

### 1.1 背景

开发者面对一个陌生的开源项目时，通常需要数小时甚至数天才能理解：

- 这个项目是干什么的？
- 用了哪些技术栈？
- 代码怎么组织的？模块之间怎么协作？
- 我应该从哪里开始读代码？
- 如果我面试这个项目，会被问什么？

这些信息散落在 README、源码、配置文件、Issue 讨论中，没有人系统性整理。

### 1.2 愿景

**输入一个 GitHub 仓库地址，5 分钟内获得一份结构化的项目分析报告。**

### 1.3 一句话描述

OpenSource Analyst 是一个 AI 驱动的开源项目分析平台，输入 GitHub URL，自动产出项目概览、技术栈、架构分析、学习路线和面试知识点。

---

## 2. 目标用户

| 用户画像 | 场景 | 核心诉求 |
|----------|------|---------|
| **新手开发者** | 想参与开源但不知道从哪开始 | 需要学习路线引导 |
| **有经验开发者** | 需要快速评估一个第三方库 | 需要技术栈 + 架构概览 |
| **技术管理者** | 做技术选型，对比多个方案 | 需要客观的架构分析 |
| **面试候选人** | 需要准备一个开源项目的深度问题 | 需要面试知识点 |
| **技术博主/讲师** | 需要快速理解项目后出内容 | 需要全面但不啰嗦的摘要 |

---

## 3. 用户故事

### 3.1 主线流程

```
用户打开 Web 界面
  → 输入 https://github.com/langchain-ai/langgraph
    → 点击"开始分析"
      → 等待 2-5 分钟
        → 获得完整分析报告
```

### 3.2 报告内容

用户看到的报告包含 6 个部分：

| 序号 | 板块 | 回答的问题 |
|------|------|-----------|
| 1 | **项目概览** | 这是什么项目？解决什么问题？适合什么场景？ |
| 2 | **技术栈分析** | 用了哪些语言/框架/库？各依赖起什么作用？ |
| 3 | **架构分析** | 项目有哪些模块？模块之间怎么协作？入口在哪？ |
| 4 | **学习路线** | 我应该按什么顺序读代码？先看哪个文件？ |
| 5 | **面试知识点** | 这个项目涉及哪些核心技术点？可能问什么？ |
| 6 | **源码阅读建议** | 重点读哪些文件？哪些可以跳过？ |

---

## 4. 功能列表

### 4.1 核心功能（MVP：M2-M6）

| 功能 | 描述 | 对应里程碑 |
|------|------|-----------|
| 仓库信息获取 | 输入 URL，抓取 README + 目录结构 + 语言统计 | M2 |
| 基础分析 | 基于 README 生成项目概览 + 技术栈初判 | M3 |
| 代码索引 | 对仓库代码建向量索引，支持语义检索 | M4 |
| Web 界面 | REST API + Swagger 文档，可通过 API 调用 | M5 |
| 工作流引擎 | LangGraph 驱动的分析流水线，按序执行各步骤 | M6 |

### 4.2 进阶功能（M7-M10）

| 功能 | 描述 | 对应里程碑 |
|------|------|-----------|
| 依赖深度分析 | 解析 pom.xml/package.json/pyproject.toml | M7 |
| 架构深度分析 | 分析目录结构、模块职责、调用关系 | M8 |
| 学习路线生成 | 根据项目结构生成分步阅读路径 | M9 |
| 多 Agent 协作 | Coordinator 调度多个专家 Agent 并行分析 | M10 |

### 4.3 高级功能（M11-M12）

| 功能 | 描述 | 对应里程碑 |
|------|------|-----------|
| 外部信息集成 | MCP 接入 GitHub Issue/PR/Release + 网络搜索 | M11 |
| 架构图生成 | Mermaid 可视化输出模块关系图 | M12 |
| 面试题生成 | 针对项目的深度面试问答 | M12 |
| 自我反思 | 分析结果完整性检查，不完整则补充 | M12 |

### 4.4 不做的事（功能边界）

- 不做代码质量审查（lint、bug 检测）
- 不做安全漏洞扫描
- 不做性能 profiler
- 不做 CI/CD 流程分析
- 不存储用户分析历史（MVP 阶段）

---

## 5. 输入输出定义

### 5.1 输入

```json
POST /analyze
{
  "repo_url": "https://github.com/owner/repo",
  "options": {
    "deep_analysis": true,
    "include_interview_questions": true
  }
}
```

### 5.2 输出

```json
{
  "task_id": "uuid",
  "status": "completed",
  "result": {
    "overview": {
      "name": "LangGraph",
      "description": "...",
      "use_cases": ["...", "..."],
      "license": "MIT"
    },
    "tech_stack": {
      "languages": {"Python": "95%", "TypeScript": "5%"},
      "frameworks": ["FastAPI", "React"],
      "key_dependencies": [
        {"name": "langgraph", "purpose": "Agent workflow engine"},
        {"name": "langchain", "purpose": "LLM framework"}
      ]
    },
    "architecture": {
      "modules": ["api/", "agents/", "graph/", "rag/"],
      "entry_point": "src/main.py",
      "module_relationships": "...",
      "design_patterns": ["Coordinator-Agent", "StateGraph"]
    },
    "learning_path": [
      {"step": 1, "file": "README.md", "reason": "了解项目目标"},
      {"step": 2, "file": "src/main.py", "reason": "看入口和路由"},
      {"step": 3, "file": "src/graph/", "reason": "理解工作流核心"}
    ],
    "interview_points": [
      {"topic": "LangGraph StateGraph 设计", "difficulty": "medium"},
      {"topic": "Multi-Agent 通信机制", "difficulty": "hard"}
    ],
    "reading_suggestions": {
      "must_read": ["src/graph/", "src/agents/"],
      "can_skip": ["tests/", "docs/"],
      "read_order": "README → main.py → graph/ → agents/"
    }
  }
}
```

---

## 6. 非功能性需求

| 类别 | 要求 |
|------|------|
| **响应时间** | 单个仓库分析 < 5 分钟（中等规模仓库） |
| **异步处理** | 分析任务异步执行，通过 task_id 查询进度 |
| **错误处理** | 无效 URL、私有仓库、超大仓库需明确报错 |
| **扩展性** | 新增一种分析维度只需新增一个 Agent 文件 |
| **LLM 提供商** | 兼容 OpenAI Compatible API |
| **部署方式** | 本地开发用 uvicorn，生产用 Docker |

---

## 7. 验收标准

### 7.1 MVP（M2-M6）

- [ ] 输入 `https://github.com/langchain-ai/langgraph` 能返回结构化 JSON
- [ ] 返回结果包含 6 个分析板块
- [ ] 分析内容与仓库实际内容一致（非幻觉）
- [ ] REST API 通过 Swagger 可调用
- [ ] 分析任务异步执行，不阻塞 HTTP 响应

### 7.2 完整版（M7-M12）

- [ ] 多 Agent 自动协作，用户只需发一次请求
- [ ] 输出包含 Mermaid 架构图
- [ ] 能分析 LangGraph、Spring AI、Hermes 三个目标项目
- [ ] Agent 可调用 MCP 外部工具

---

## 8. 术语表

| 术语 | 解释 |
|------|------|
| Agent | 一个具有特定分析职责的 AI 单元 |
| Coordinator | 负责任务拆分和 Agent 调度的中央 Agent |
| LangGraph | LangChain 的图工作流框架，本项目用它编排分析流程 |
| MCP | Model Context Protocol，给 Agent 提供外部工具的标准协议 |
| RAG | Retrieval-Augmented Generation，先检索再生成 |
| ChromaDB | 开源向量数据库，存储代码片段的嵌入向量 |
