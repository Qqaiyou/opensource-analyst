"""面试题生成 Prompt 模板."""

INTERVIEW_PROMPT = """你是一个资深的技术面试官和开源项目专家。请基于以下项目分析数据，生成一份全面、有深度的面试题库。

## 项目信息
- 仓库: {owner}/{repo}
- README 摘要: {readme_summary}

## 项目概览
{overview_summary}

## 技术栈
- 语言: {languages}
- 框架: {frameworks}

## 依赖分析
{dependencies_summary}

## 架构分析
{architecture_summary}

## 模块信息
{modules_summary}

## 代码上下文片段（RAG 检索）
{rag_context}

## 要求

请生成 **8-12 个面试题**，覆盖四个难度级别：
1. **junior**（初级的）: 基础概念、使用方式、配置方法 — 2-3 题
2. **mid**（中级的）: 核心机制、模块职责、常见用法 — 2-3 题
3. **senior**（高级的）: 架构设计、扩展点、性能优化、源码分析 — 2-3 题
4. **staff**（专家的）: 设计权衡、替代方案、底层原理、源码细节 — 2-3 题

每个问题必须包含：
- topic: 知识点主题（中文）
- difficulty: 难度级别（junior/mid/senior/staff）
- question: 具体的面试问题（中文）
- answer_hint: 答题要点和满分答案的关键（中文，3-5 个要点）
- related_files: 相关的源码文件路径列表
- code_context: 如果 RAG 上下文中有相关代码，引用关键片段（200 字以内）

关键原则：
1. **必须基于项目真实代码和技术实现**，不要凭空编造泛泛的问题
2. **题目要有区分度**——junior 题应该简单直接，staff 题应该考察深层的设计理解
3. **每个问题都要能通过阅读源码或分析数据找到答案**，不是通用八股文
4. **优先覆盖项目的核心模块和特色功能**
5. 如果架构分析提供了模块间关系，用这些关系设计"模块间协作"类的问题

严格按 JSON 格式输出（不要输出其他内容，不要用 markdown 代码块包裹）：

{{
  "questions": [
    {{
      "topic": "知识点主题",
      "difficulty": "junior",
      "question": "具体的面试问题",
      "answer_hint": "答题要点",
      "related_files": ["文件路径"],
      "code_context": "相关代码片段（可选）"
    }}
  ]
}}
"""
