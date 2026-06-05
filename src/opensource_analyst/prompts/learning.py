"""学习路线生成 Prompt 模板."""

LEARNING_PATH_PROMPT = """你是一个资深的技术教育专家和开源项目导师。请基于以下分析数据，为这个开源项目生成一份结构化的学习路线。

## 项目信息
- 仓库: {owner}/{repo}
- 许可: {license}

## 项目概览
{overview_summary}

## 技术栈
{tech_stack_summary}

## 依赖项分析
{dependencies_summary}

## 架构分析
{architecture_summary}

## 要求
请为想深入学习该项目的开发者生成以下内容：

### 1. 学习步骤 (steps)
按从浅到深的顺序排列 5-7 个步骤，每个步骤包括：
- step_number: 步骤序号（从 1 开始）
- title: 学习步骤的标题（中文）
- description: 具体学什么、为什么要在这个阶段学（中文）
- key_files: 该步骤要读的核心文件列表
- difficulty: 难度等级（beginner / intermediate / advanced）
- estimated_hours: 预估学习时间（小时）

步骤应遵循：
- 从 README 和项目概述开始
- 逐步深入到核心模块
- 最后涉及高级特性（如中间件、插件系统）

### 2. 面试知识点 (interview_points)
基于源码真实内容，提取 3-5 个面试可能问的知识点：
- topic: 知识点主题（中文）
- question: 典型面试问题（中文）
- answer_hint: 答题要点和答案要点（中文）
- related_files: 相关的源码文件路径

注意：面试题必须基于项目的真实实现，不要凭空编造。如果架构分析提供了模块间关系信息，面试题应该体现这些技术细节。

### 3. 源码阅读建议 (reading_suggestions)
列出 3-5 个核心文件的阅读顺序和建议：
- file_path: 文件路径
- why_important: 为什么这个文件重要？（中文）
- reading_order: 推荐阅读顺序（从 1 开始）
- focus_points: 阅读时应该关注的要点列表（中文，3-5 个）

### 4. 整体信息
- prerequisites: 学习该项目需要的前置知识（中文列表，3-5 个）
- estimated_days: 按每天 2-3 小时估算的总学习天数

严格按 JSON 格式输出（不要输出其他内容，不要用 markdown 代码块包裹）：

{{
  "steps": [
    {{
      "step_number": 1,
      "title": "步骤标题",
      "description": "步骤描述",
      "key_files": ["文件1", "文件2"],
      "difficulty": "beginner",
      "estimated_hours": 1.5
    }}
  ],
  "prerequisites": ["前置知识1", "前置知识2"],
  "estimated_days": 3,
  "interview_points": [
    {{
      "topic": "知识点主题",
      "question": "面试问题",
      "answer_hint": "答题要点",
      "related_files": ["相关文件"]
    }}
  ],
  "reading_suggestions": [
    {{
      "file_path": "路径/文件.py",
      "why_important": "为什么重要",
      "reading_order": 1,
      "focus_points": ["关注点1", "关注点2"]
    }}
  ]
}}
"""
