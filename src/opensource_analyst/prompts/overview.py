"""项目概览 & 技术栈分析 Prompt 模板."""

OVERVIEW_PROMPT = """你是一个专业的开源项目分析专家。请基于以下信息分析这个 GitHub 仓库。

## README 内容
{readme}

## 文件结构（前 200 个文件）
{file_tree}

## 语言统计
{languages}

## 依赖分析结果（从依赖文件中解析 + LLM 深度解读）
{dependencies}

## 要求
1. 仔细阅读 README，理解项目的目标、功能和适用场景
2. 根据文件结构和语言统计，判断技术栈
3. 参考「依赖分析结果」中的依赖数据来完善技术栈分析
4. 严格按 JSON 格式输出（不要输出其他内容，不要用 markdown 代码块包裹）

{{
  "overview": {{
    "name": "项目的精确名称",
    "description": "用 2-3 句话概括项目是什么、解决什么问题（中文）",
    "use_cases": ["适用场景1", "适用场景2", "适用场景3"],
    "license": "许可证类型，如 MIT、Apache-2.0、GPL-3.0 等，如果不确定填 Unknown"
  }},
  "tech_stack": {{
    "languages": {{"语言名": "百分比或描述"}},
    "frameworks": ["使用的框架名称列表"],
    "key_dependencies": [
      {{"name": "依赖名", "version": "版本号或 null", "category": "core/dev/build/test/peer", "purpose": "在项目中的作用（中文）"}}
    ]
  }}
}}
"""
