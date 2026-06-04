"""依赖分析 Prompt 模板."""

DEPENDENCY_ANALYSIS_PROMPT = """你是一个专业的技术栈分析师。请基于解析出的项目依赖数据分析技术栈。

## 项目信息
- 名称: {name}
- 主语言: {languages}

## README 摘要
{readme_summary}

## 解析出的依赖文件
{dep_files_summary}

## 依赖清单（以下是从项目中实际解析出的依赖项）
{parsed_deps}

## 要求
对以上每个依赖项进行深度分析：
1. **category**: 分类为 core（运行时核心依赖）/ dev（开发工具）/ build（构建工具）/ test（测试框架）/ peer（对等依赖）
2. **purpose**: 用 1 句中文说明该依赖在项目中的作用

如果上述依赖清单不为空，请只分析清单中的依赖项。
如果清单为空（项目没有标准依赖文件或依赖文件不存在），请根据 README 和文件结构推断可能的依赖项。

严格按 JSON 数组格式输出（不要输出其他内容，不要用 markdown 代码块包裹）：

[
  {{
    "name": "依赖名称",
    "version": "版本约束（如果有）或 null",
    "category": "core/dev/build/test/peer",
    "purpose": "在项目中的作用（中文）"
  }}
]
"""
