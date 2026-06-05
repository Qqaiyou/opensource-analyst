# Milestone 9 学习笔记 — Learning Agent

> 日期：2026-06-05
> 关联提交：feat: 完成 Milestone 9 — Learning Agent

---

## 1. 概念

### 什么是 Learning Agent

Learning Agent 是 OpenSource Analyst 的第七个专家 Agent，职责是**综合前面所有分析结果**（项目概览、技术栈、依赖、架构），由 LLM 生成一条**结构化的学习路线**。

与 M7（Dependency）和 M8（Architecture）不同，Learning Agent 是**纯 LLM Agent**——不涉及静态代码解析，只做信息综合与推理。

### 核心产出

| 产出 | 说明 |
|------|------|
| `LearningStep` | 有序学习步骤，含标题、描述、关键文件、难度、预估时间 |
| `InterviewPoint` | 面试知识点，含主题、典型问题、答题要点、相关文件 |
| `ReadingSuggestion` | 源码阅读建议，含文件路径、重要性说明、阅读顺序、关注点 |
| `LearningPath` | 顶层容器，聚合以上三项 + 前置知识 + 预估天数 |

---

## 2. 设计

### 数据流

```
repo_info ─── README + 语言统计 ────┐
overview ─── 描述 + 适用场景 ────────┤
tech_stack ─── 语言 + 框架 ──────────┼──→ LearningAgent.analyze() ──→ LearningPath
dependencies ─── name + category + purpose ─┤
architecture ─── pattern + modules + summary ─┤
```

### 目录结构（M9 新增/修改）

```
src/opensource_analyst/
├── prompts/learning.py     ← NEW  LEARN_PATH_PROMPT 模板
├── agents/learning.py      ← NEW  LearningAgent 类
├── models/analysis.py      ← MOD  新增 4 个模型
├── graph/state.py          ← MOD  learning_path 类型化
├── graph/nodes.py          ← MOD  learning_node 替换占位
api/analyze.py              ← MOD  AnalysisResult 包含 learning_path
tests/test_learning.py      ← NEW  4 个测试
```

### 模型设计

```python
class LearningStep(BaseModel):
    step_number: int
    title: str
    description: str
    key_files: list[str]
    difficulty: str          # beginner | intermediate | advanced
    estimated_hours: float

class InterviewPoint(BaseModel):
    topic: str
    question: str
    answer_hint: str
    related_files: list[str]

class ReadingSuggestion(BaseModel):
    file_path: str
    why_important: str
    reading_order: int
    focus_points: list[str]

class LearningPath(BaseModel):
    steps: list[LearningStep]
    prerequisites: list[str]
    estimated_days: int
    interview_points: list[InterviewPoint]
    reading_suggestions: list[ReadingSuggestion]
```

### Prompt 设计策略

- 注入全部上下文（overview + tech_stack + dependencies + architecture）
- 每个字段有 fallback 文本（"未提供..."），保证容错
- 要求 LLM 按 beginner → intermediate → advanced 递进排列
- 面试题必须基于真实源码实现，不凭空编造

---

## 3. 实现

### LearningAgent

```python
class LearningAgent(BaseAgent):
    def analyze(
        self,
        repo_info, overview, tech_stack, dependencies, architecture,
    ) -> LearningPath:
        # 1. 组装上下文摘要（每个字段有 fallback）
        # 2. 注入 LEARN_PATH_PROMPT
        # 3. LLM 调用 → _invoke_json(prompt)
        # 4. _parse_result → LearningPath
```

### learning_node 替换

从 `return {"learning_path": None}` 占位 → 真实 5 步链路：
```
收集 state 字段 → 实例化 LearningAgent → analyze() → 返回 LearningPath
```

### GraphState 类型更新

```python
# before
learning_path: NotRequired[Any]

# after
learning_path: NotRequired[LearningPath | None]
```

---

## 4. 验收标准

| 测试 | 说明 |
|------|------|
| `test_learning_step_model` | 6 字段模型校验 |
| `test_learning_path_model` | 嵌套模型校验（steps + interview + reading） |
| `test_learning_agent_tinydb` | 真实 LLM 调用，steps ≥ 4，interview ≥ 2，reading ≥ 3 |
| `test_learning_agent_minimal` | 最小输入容错，steps ≥ 3 |

### 运行命令

```bash
uv run pytest tests/test_learning.py -v
uv run pytest tests/test_graph.py -v  # 含 learning_node 替换后测试
```

### 工作流 (M9)

```
load_repo → index_code → retrieve_context → dependency → architecture → analyze → learning → END
              ↓ error?        ↓ error?       ↓ error?    ↓ error?      ↓ error?  ↓ error?
              END             END            END         END           END       END
```

---

## 5. 代码审查发现

1. **workflow.py 双路由 bug**: `add_edge("architecture", "learning")` 与 conditional edge 冲突，导致 learning_node 在 analyze_node 之前执行 → 已删除冗余边
2. **API 输出线缆缺失**: `AnalysisResult` 缺少 `learning_path` 字段 → 已添加
3. **License 字段错误**: `repo_info.languages.get("license")` 对 `dict[str, int]` 无效 → 已修复为文本 fallback

---

## 6. 技术要点

- **纯 LLM Agent**: M9 是完全靠 prompt engineering 的 Agent，不需要静态分析
- **信息综合**: 核心价值在于"把所有分析变成可执行的行动计划"
- **容错设计**: 每个输入字段都有 fallback，缺失任一分析结果也能生成基本路线
- **Backend 线程修复**: `run_in_executor` 将同步 LLM 调用移到独立线程，避免阻塞事件循环
