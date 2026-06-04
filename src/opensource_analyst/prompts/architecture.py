"""架构分析 Prompt 模板."""

ARCHITECTURE_PROMPT = """你是一个专业的软件架构分析师。请基于以下信息分析这个 GitHub 仓库的架构。

## 项目信息
- 仓库: {owner}/{repo}
- 主语言: {languages}

## README 摘要
{readme_summary}

## 模块分组（按目录结构自动识别）
{modules_summary}

## 入口文件
{entry_file}

## 模块间 Import 关系
{import_relations}

## 依赖分析结果（来自 DependencyAgent）
{dependencies_summary}

## 要求
请基于上述信息进行全面架构分析：
1. **architecture_pattern**: 识别项目的架构模式（如 MVC / 分层 / 插件式 / 管道-过滤器 / 微内核 等）
2. **modules**: 对每个模块说明其职责、关键文件、对外暴露的符号
3. **module_relations**: 模块间的依赖关系（哪个模块依赖哪个模块）
4. **architecture_summary**: 用 2-3 句话总结项目的整体架构

注意：
- 如果模块分组信息有限，请根据 README 和文件结构合理推断
- 模块职责和架构模式要结合项目实际功能来描述
- 用中文输出描述性文字

严格按 JSON 格式输出（不要输出其他内容，不要用 markdown 代码块包裹）：

{{
  "architecture_pattern": "架构模式描述",
  "modules": [
    {{
      "name": "模块名",
      "path": "模块路径",
      "responsibility": "模块职责（中文）",
      "key_files": ["关键文件1", "关键文件2"],
      "imports": ["被该模块导入的其他模块"],
      "exported_symbols": ["核心类或函数名"]
    }}
  ],
  "entry_file": "入口文件路径",
  "module_relations": [
    {{"from": "源模块", "to": "目标模块", "type": "imports"}}
  ],
  "architecture_summary": "架构总结（2-3 句中文）"
}}
"""
