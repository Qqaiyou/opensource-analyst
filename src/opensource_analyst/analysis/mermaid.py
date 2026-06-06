"""Mermaid 可视化图生成器 — 纯静态，无 LLM 调用.

从 ArchitectureResult / TechStack / 依赖数据分析结果直接生成
Mermaid.js 流程图字符串，可用于 Markdown 渲染或 API 输出。

支持三种图:
    - module_flowchart:     模块关系图 (flowchart LR)
    - dependency_graph:     文件依赖图 (flowchart LR)
    - tech_stack_diagram:   技术栈全景图 (flowchart LR)
"""

from __future__ import annotations

from opensource_analyst.models.analysis import (
    ArchitectureResult,
    Dependency,
    MermaidDiagrams,
    ModuleInfo,
    TechStack,
)


def build_module_flowchart(
    architecture: ArchitectureResult | None,
) -> str:
    """构建模块关系图.

    每个模块用一个 subgraph 包裹，内部列出 key_files.
    边 (edge) 来自 module_relations 中的 from→to 关系。

    Args:
        architecture: M8 ArchitectureAgent 产出，含 modules 和 module_relations.

    Returns:
        Mermaid flowchart LR 字符串，或空字符串（无可渲染内容时）。
    """
    if not architecture or not architecture.modules:
        return ""

    lines = ["flowchart LR"]
    indent = "    "

    # 每个模块一个 subgraph
    for mod in architecture.modules:
        safe_name = _sanitize(mod.name)
        lines.append(f"{indent}subgraph {safe_name}[{_escape_label(mod.name)}]")
        for i, kf in enumerate(mod.key_files[:5]):  # 最多 5 个文件
            file_id = f"{safe_name}_f{i}"
            display = kf.split("/")[-1] or kf
            lines.append(f"{indent}{file_id}[{_escape_label(display)}]")
        lines.append(f"{indent}end")

    # 模块间依赖边
    if architecture.module_relations:
        lines.append("")
        for rel in architecture.module_relations[:20]:  # 最多 20 条边
            src_name = rel.get("from", "")
            tgt_name = rel.get("to", "")
            rel_type = rel.get("type", "depends")
            if src_name and tgt_name:
                src_safe = _sanitize(src_name)
                tgt_safe = _sanitize(tgt_name)
                label = _escape_label(rel_type)
                lines.append(f"{indent}{src_safe} -- {label} --> {tgt_safe}")

    # 若无 subgraph，至少返回空
    if len(lines) == 1:
        return ""

    return "\n".join(lines)


def build_dependency_graph(
    import_map: dict[str, list[str]] | None,
    modules: list[ModuleInfo] | None,
) -> str:
    """构建文件依赖图.

    从 import_map（{file: [imports]}）提取有向边。
    如果传递了 modules，按模块分组着色（通过 subgraph 体现）。

    Args:
        import_map: {文件路径: [项目内部 import 列表]}
        modules: 模块列表，用于分组文件; 可选.

    Returns:
        Mermaid flowchart LR 字符串，或空字符串.
    """
    if not import_map:
        return ""

    # 过滤：只保留有边（有内部 import 的路径）
    filtered = {k: v for k, v in import_map.items() if v}
    if not filtered:
        return ""

    lines = ["flowchart LR"]
    indent = "    "

    # 引用计数，给每个文件分配短 ID
    node_ids: dict[str, str] = {}
    node_counter = 0

    def _get_id(path: str) -> str:
        nonlocal node_counter
        if path not in node_ids:
            node_ids[path] = f"n{node_counter}"
            node_counter += 1
        return node_ids[path]

    # 按模块分组 subgraph
    module_file_map: dict[str, list[str]] = {}
    if modules:
        for mod in modules:
            for kf in mod.key_files:
                for fp in filtered:
                    if fp == kf or fp.endswith(f"/{kf}") or fp.startswith(mod.path):
                        module_file_map.setdefault(mod.name, []).append(fp)

    # 为已分组的模块画 subgraph
    assigned = set()
    for mod_name, file_paths in module_file_map.items():
        if not file_paths:
            continue
        safe_name = _sanitize(mod_name)
        lines.append(f"{indent}subgraph {safe_name}[{_escape_label(mod_name)}]")
        for fp in file_paths:
            fid = _get_id(fp)
            display = fp.split("/")[-1] or fp
            lines.append(f"{indent}{fid}[{_escape_label(display)}]")
            assigned.add(fp)
        lines.append(f"{indent}end")

    # 未分配到模块的文件
    unassigned = [fp for fp in filtered if fp not in assigned]
    if unassigned:
        lines.append(f"{indent}subgraph Other[_Others_]")
        for fp in unassigned:
            fid = _get_id(fp)
            display = fp.split("/")[-1] or fp
            lines.append(f"{indent}{fid}[{_escape_label(display)}]")
        lines.append(f"{indent}end")

    # 边
    lines.append("")
    edges_added = 0
    for src_path, targets in filtered.items():
        for tgt in targets[:5]:  # 每条边最多 5 个目标
            # 尝试在 import_map 的 key 中匹配
            tgt_path = _find_import_target(tgt, import_map)
            if tgt_path and tgt_path != src_path and edges_added < 40:
                lines.append(
                    f"{indent}{_get_id(src_path)} --> {_get_id(tgt_path)}"
                )
                edges_added += 1

    if len(lines) == 1:
        return ""

    return "\n".join(lines)


def build_tech_stack_diagram(
    tech_stack: TechStack | None,
    dependencies: list[Dependency] | None = None,
) -> str:
    """构建技术栈全景图.

    分层展示:
        - 顶层: 项目名
        - 第二层: 编程语言
        - 第三层: 框架/运行时
        - 第四层: 核心依赖（已分类）

    Args:
        tech_stack: M3/M10 产出的技术栈信息.
        dependencies: M7 产出的依赖分类列表.

    Returns:
        Mermaid flowchart LR 字符串，或空字符串.
    """
    # 如果没有 tech_stack 也没有 dependencies，返回空
    if not tech_stack and not dependencies:
        return ""

    lines = ["flowchart LR"]
    indent = "    "

    # 语言层
    lang_nodes: list[str] = []
    if tech_stack:
        for lang in tech_stack.languages:
            lid = _sanitize(f"lang_{lang}")
            lines.append(f"{indent}{lid}[{_escape_label(lang)}]")
            lang_nodes.append(lid)
        if lang_nodes:
            lang_node_str = f"Langs[{_escape_label('Languages') if lang_nodes else ''}]"
            lines.append(f"{indent}Langs -->|{_escape_label('Programming Languages')}| {lang_nodes[0]}" if len(lang_nodes) == 1 else "")
            if len(lang_nodes) <= 1:
                lines.pop()
                lines.pop()

    # 框架层
    framework_nodes: list[str] = []
    if tech_stack and tech_stack.frameworks:
        for fw in tech_stack.frameworks:
            fid = _sanitize(f"fw_{fw}")
            lines.append(f"{indent}{fid}[{_escape_label(fw)}]")
            framework_nodes.append(fid)
        for fn in framework_nodes:
            if lang_nodes:
                lines.append(f"{indent}{lang_nodes[0]} --> {fn}")
            else:
                lines.append(f"{indent}Lang --> {fn}")

    # 依赖层
    if dependencies:
        cat_nodes: dict[str, list[str]] = {}
        for dep in dependencies:
            cat = dep.category or "other"
            safe_cat = _sanitize(f"cat_{cat}")
            dep_id = _sanitize(f"dep_{dep.name}")
            display = f"{dep.name}"
            if dep.version:
                display += f" {dep.version}"
            lines.append(f"{indent}{dep_id}[{_escape_label(display)}]")
            cat_nodes.setdefault(cat, []).append(dep_id)

        # 按分类画 subgraph（有 2+ 同类依赖时）
        for cat, deps in cat_nodes.items():
            lines.append(f"{indent}subgraph {_sanitize(f'sg_{cat}')}[{_escape_label(f'{cat.upper()} Dependencies')}]")
            for d_id in deps:
                lines.append(f"{indent}{d_id}")
            lines.append(f"{indent}end")
            # 框架 → 依赖 连线
            target = framework_nodes[0] if framework_nodes else (lang_nodes[0] if lang_nodes else "")
            if deps and target:
                lines.append(f"{indent}{target} --> {deps[0]}")

    if len(lines) == 1:
        return ""

    return "\n".join(lines)


def build_all_mermaid(
    architecture: ArchitectureResult | None = None,
    import_map: dict[str, list[str]] | None = None,
    tech_stack: TechStack | None = None,
    dependencies: list[Dependency] | None = None,
) -> MermaidDiagrams:
    """一键生成三种 Mermaid 图.

    Args:
        architecture: M8 架构分析结果.
        import_map: M8 提取的项目内部 import 映射.
        tech_stack: M3/M10 技术栈.
        dependencies: M7 依赖分析.

    Returns:
        MermaidDiagrams: 三种图字符串.
    """
    modules = architecture.modules if architecture else None

    return MermaidDiagrams(
        module_flowchart=build_module_flowchart(architecture),
        dependency_graph=build_dependency_graph(import_map, modules),
        tech_stack_diagram=build_tech_stack_diagram(tech_stack, dependencies),
    )


# ── 辅助函数 ──────────────────────────────────────────


def _sanitize(name: str) -> str:
    """将任意字符串转为安全的 Mermaid 节点 ID（字母数字 + 下划线）. """
    safe = ""
    for ch in name:
        if ch.isalnum():
            safe += ch
        else:
            safe += "_"
    # 不能以数字开头
    if safe and safe[0].isdigit():
        safe = "n" + safe
    return safe or "node"


def _escape_label(text: str) -> str:
    """转义 Mermaid 节点标签文本中的特殊字符."""
    return (
        text.replace('"', "'")
        .replace("[", "(")
        .replace("]", ")")
        .replace("|", "/")
    )


def _find_import_target(
    import_name: str, import_map: dict[str, list[str]],
) -> str | None:
    """在 import_map 的 key 中查找与 import_name 最佳匹配的文件路径.

    例如:
        import_name = "tinydb.database"
        import_map keys = ["tinydb/__init__.py", "tinydb/database.py", ...]
        → 返回 "tinydb/database.py"
    """
    # 将模块名路径化: "tinydb.database" → "tinydb/database"
    candidate = import_name.replace(".", "/")
    # 精确匹配：找到完全一样的文件
    for fp in import_map:
        if fp == candidate or fp == candidate + ".py":
            return fp
        if fp.endswith("/" + candidate) or fp.endswith("/" + candidate + ".py"):
            return fp
    # 模糊匹配：取最长公共前缀
    best: str | None = None
    best_len = 0
    for fp in import_map:
        fp_no_ext = fp.rsplit(".", 1)[0] if "." in fp else fp
        if candidate in fp_no_ext or fp_no_ext in candidate:
            if len(fp_no_ext) > best_len:
                best = fp
                best_len = len(fp_no_ext)
    return best
