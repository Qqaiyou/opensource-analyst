"""架构分析器 — 从文件树提取模块结构、入口文件和 import 关系（不涉及 LLM）."""

import ast
import re
from collections import defaultdict

import httpx


class ArchitectureAnalyzer:
    """从 GitHub 仓库的文件树做静态架构分析。

    三个能力：
    1. group_modules() — 按目录层级分组，识别模块边界
    2. identify_entry_file() — 基于命名模式识别程序入口
    3. extract_imports() — AST 解析 Python 文件的 import 语句
    """

    # 入口文件命名模式（按优先级）
    ENTRY_PATTERNS = [
        "__main__.py",
        "main.py",
        "app.py",
        "server.py",
        "run.py",
        "cli.py",
        "manage.py",
        "index.js",
        "index.ts",
        "main.go",
        "App.java",
    ]

    ROOT_IGNORE = {
        "tests", "test", "docs", "doc", "examples", "example",
        "benchmarks", "bench", "scripts", ".github", ".circleci",
        "node_modules", ".git", "__pycache__", "build", "dist",
    }

    @staticmethod
    def group_modules(file_tree: list[str]) -> dict[str, list[str]]:
        """将文件树按目录前缀分组为逻辑模块。

        Returns:
            {module_name: [file_path, ...]}，其中 module_name 是目录名（用 . 分隔层级）
        """
        groups: dict[str, list[str]] = {}

        for path in file_tree:
            parts = path.split("/")

            if len(parts) == 1:
                # 根目录文件
                groups.setdefault("root", []).append(path)
                continue

            top = parts[0]
            if top in ArchitectureAnalyzer.ROOT_IGNORE or top.startswith("."):
                groups.setdefault(top, []).append(path)
                continue

            # 取前两层作为模块名（如 src/controllers → src.controllers）
            if len(parts) >= 3:
                module_name = ".".join(parts[:2])
            else:
                module_name = top

            groups.setdefault(module_name, []).append(path)

        return groups

    @staticmethod
    def identify_entry_file(file_tree: list[str]) -> str | None:
        """基于命名模式识别项目入口文件。

        按优先级扫描：__main__.py > main.py > app.py > ...
        只取根目录或 src/ 下的入口文件。
        """
        # 按优先级尝试匹配
        for pattern in ArchitectureAnalyzer.ENTRY_PATTERNS:
            for path in file_tree:
                filename = path.split("/")[-1]
                if filename == pattern:
                    return path

        # Fallback: 在根目录下找第一个 .py 文件
        for path in file_tree:
            if path.endswith(".py") and "/" not in path:
                return path
        # Fallback: 在整个树中找第一个 .py 文件
        for path in file_tree:
            if path.endswith(".py"):
                return path

        return None

    @staticmethod
    def extract_imports(source_code: str) -> list[str]:
        """用 Python AST 提取文件的 import 语句。

        Returns:
            import 目标列表，如 ["tinydb.database", "os", ".storages"]
        """
        imports: list[str] = []
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    level = node.level  # 相对导入的层级
                    if level > 0:
                        imports.append("." * level + node.module)
                    else:
                        imports.append(node.module)

        return imports

    @staticmethod
    def is_project_import(import_name: str, modules: dict[str, list[str]]) -> bool:
        """判断一个 import 是否是项目内部模块引用（非标准库、非第三方）。"""
        # 相对导入一定是项目内
        if import_name.startswith("."):
            return True

        # 检查是否匹配已知模块名的前缀
        for module_name in modules:
            if import_name.startswith(module_name):
                return True
        return False

    @staticmethod
    def infer_module_relations(
        modules: dict[str, list[str]],
        import_map: dict[str, list[str]],
    ) -> list[dict]:
        """根据各文件的 import 列表推断模块间的关系。

        Returns:
            [{from: "module_a", to: "module_b", type: "imports"}, ...]
        """
        relations: list[dict] = []
        seen: set[tuple[str, str]] = set()

        # 构建 file → module 的索引
        file_to_module: dict[str, str] = {}
        for mod_name, files in modules.items():
            for f in files:
                file_to_module[f] = mod_name

        for file_path, imports in import_map.items():
            from_mod = file_to_module.get(file_path, "unknown")
            for imp in imports:
                # 尝试匹配 import 到模块
                for mod_name in modules:
                    if imp.startswith(mod_name):
                        key = (from_mod, mod_name)
                        if key not in seen and from_mod != mod_name:
                            seen.add(key)
                            relations.append({
                                "from": from_mod,
                                "to": mod_name,
                                "type": "imports",
                            })
                        break

        return relations

    async def download_key_files(
        self,
        owner: str,
        repo: str,
        file_tree: list[str],
        github_token: str | None = None,
        max_files: int = 30,
    ) -> dict[str, str]:
        """下载项目关键 Python 文件用于 AST 分析。

        Args:
            max_files: 最多下载文件数（控制下载量）

        Returns:
            {file_path: source_code}
        """
        python_files = [f for f in file_tree if f.endswith(".py")][:max_files]

        headers: dict[str, str] = {}
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        results: dict[str, str] = {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            for path in python_files:
                content = await self._fetch_file(client, owner, repo, path, headers)
                if content is not None:
                    results[path] = content

        return results

    async def _fetch_file(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        path: str,
        headers: dict[str, str],
    ) -> str | None:
        """从 GitHub raw 下载单个文件。"""
        for branch in ["master", "main"]:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.text
            except Exception:
                continue
        return None
