"""依赖文件检测与解析 — 从 file_tree 识别并解析多种语言的依赖声明."""

import json
import re
from typing import Optional

import httpx
from pydantic import BaseModel

# Python 3.10 兼容：tomllib 是 3.11+ 标准库，3.10 用 tomli 替代
try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


class ParsedDependency(BaseModel):
    """解析阶段的中间模型 — 从依赖文件提取的原始数据."""

    name: str
    version: str | None = None
    source_file: str
    category: str | None = None  # core / dev / build / test / peer


# 已知依赖文件名（不含路径前缀）
DEP_FILE_NAMES: set[str] = {
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
    "package.json", "pom.xml", "build.gradle", "build.gradle.kts",
    "go.mod", "Cargo.toml", "Gemfile", "composer.json",
}


class DependencyFileParser:
    """从文件树检测依赖文件，下载并解析依赖清单。

    使用方式:
        files = DependencyFileParser.detect_dep_files(file_tree)
        parser = DependencyFileParser()
        deps = await parser.fetch_and_parse("msiemens", "tinydb", files)
    """

    @staticmethod
    def detect_dep_files(file_tree: list[str]) -> list[str]:
        """从文件树中找出依赖文件的路径。

        匹配策略：只取根目录下的依赖文件（不带目录前缀），
        避免匹配到子目录中非项目根的依赖文件。
        """
        result: list[str] = []
        for path in file_tree:
            if "/" in path:
                continue
            if path in DEP_FILE_NAMES:
                result.append(path)
        return result

    async def fetch_and_parse(
        self,
        owner: str,
        repo: str,
        dep_files: list[str],
        github_token: Optional[str] = None,
    ) -> list[ParsedDependency]:
        """下载依赖文件并解析，返回所有依赖项的清单。

        Args:
            owner: 仓库拥有者
            repo: 仓库名
            dep_files: detect_dep_files() 返回的文件列表
            github_token: 可选 GitHub Token
        """
        headers: dict[str, str] = {}
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        all_deps: list[ParsedDependency] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for path in dep_files:
                content = await self._fetch_file(client, owner, repo, path, headers)
                if content is None:
                    continue

                parsed = self._parse_file(content, path)
                all_deps.extend(parsed)

        return all_deps

    async def _fetch_file(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        path: str,
        headers: dict[str, str],
    ) -> Optional[str]:
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

    def _parse_file(self, content: str, filename: str) -> list[ParsedDependency]:
        """根据文件名选择对应的解析器。"""
        if filename == "pyproject.toml":
            return self.parse_pyproject_toml(content, filename)
        elif filename == "package.json":
            return self.parse_package_json(content, filename)
        elif filename in ("requirements.txt", "requirements-dev.txt"):
            return self.parse_requirements_txt(
                content, filename,
                category="dev" if "dev" in filename else "core"
            )
        elif filename == "setup.cfg":
            return self.parse_setup_cfg(content, filename)
        elif filename == "setup.py":
            return self.parse_setup_py(content, filename)
        elif filename == "pom.xml":
            return self.parse_pom_xml(content, filename)
        elif filename == "build.gradle" or filename == "build.gradle.kts":
            return self.parse_gradle(content, filename)
        elif filename == "go.mod":
            return self.parse_go_mod(content, filename)
        elif filename == "Cargo.toml":
            return self.parse_cargo_toml(content, filename)
        else:
            return []

    # ── Python 生态 ──────────────────────────────────

    @staticmethod
    def parse_pyproject_toml(content: str, filename: str) -> list[ParsedDependency]:
        """解析 pyproject.toml 中的依赖声明。"""
        deps: list[ParsedDependency] = []
        try:
            data = tomllib.loads(content)
        except Exception:
            return deps

        project = data.get("project", {})

        # [project.dependencies]
        for dep_str in project.get("dependencies", []):
            name, version = DependencyFileParser._split_pep508(dep_str)
            deps.append(ParsedDependency(
                name=name, version=version, source_file=filename, category="core",
            ))

        # [project.optional-dependencies]
        for group, dep_list in project.get("optional-dependencies", {}).items():
            cat = "dev" if group in ("test", "dev", "testing") else group
            for dep_str in dep_list:
                name, version = DependencyFileParser._split_pep508(dep_str)
                deps.append(ParsedDependency(
                    name=name, version=version, source_file=filename, category=cat,
                ))

        # [build-system.requires]
        for dep_str in data.get("build-system", {}).get("requires", []):
            name, version = DependencyFileParser._split_pep508(dep_str)
            deps.append(ParsedDependency(
                name=name, version=version, source_file=filename, category="build",
            ))

        return deps

    @staticmethod
    def parse_setup_cfg(content: str, filename: str) -> list[ParsedDependency]:
        """解析 setup.cfg 中的 install_requires。"""
        import configparser
        deps: list[ParsedDependency] = []
        try:
            cfg = configparser.ConfigParser()
            cfg.read_string(content)
        except Exception:
            return deps

        for section in ("options", "metadata"):
            if cfg.has_option(section, "install_requires"):
                raw = cfg.get(section, "install_requires")
                for line in raw.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    name, version = DependencyFileParser._split_pep508(line)
                    deps.append(ParsedDependency(
                        name=name, version=version, source_file=filename, category="core",
                    ))
        return deps

    @staticmethod
    def parse_setup_py(content: str, filename: str) -> list[ParsedDependency]:
        """解析 setup.py 中的 install_requires（正则提取字符串列表）。"""
        deps: list[ParsedDependency] = []
        pattern = re.compile(
            r'install_requires\s*=\s*\[(.*?)\]', re.DOTALL
        )
        match = pattern.search(content)
        if not match:
            return deps

        # 提取引号内的字符串
        str_pattern = re.compile(r"""['"]([^'"]+)['"]""")
        for dep_str in str_pattern.findall(match.group(1)):
            name, version = DependencyFileParser._split_pep508(dep_str)
            if name:
                deps.append(ParsedDependency(
                    name=name, version=version, source_file=filename, category="core",
                ))
        return deps

    @staticmethod
    def parse_requirements_txt(
        content: str, filename: str, category: str = "core"
    ) -> list[ParsedDependency]:
        """解析 requirements.txt 格式的依赖列表。"""
        deps: list[ParsedDependency] = []
        for line in content.splitlines():
            line = line.strip()

            if not line or line.startswith("#"):
                continue
            if line.startswith("-e") or line.startswith("--"):
                continue
            if line.startswith("-r"):
                continue

            name, version = DependencyFileParser._split_pep508(line)
            if name:
                deps.append(ParsedDependency(
                    name=name, version=version, source_file=filename, category=category,
                ))
        return deps

    @staticmethod
    def _split_pep508(dep_str: str) -> tuple[str, Optional[str]]:
        """从 PEP 508 格式字符串提取 name 和 version。

        "requests>=2.28,<3" → ("requests", ">=2.28,<3")
        "flask" → ("flask", None)
        """
        dep_str = dep_str.strip()
        # 匹配 name[extras] version_spec 模式
        m = re.match(
            r'^([a-zA-Z0-9][\w\-.]*)\s*(.*)', dep_str
        )
        if not m:
            return "", None

        name = m.group(1)
        version_str = m.group(2).strip()
        return name, version_str if version_str else None

    # ── Node.js 生态 ─────────────────────────────────

    @staticmethod
    def parse_package_json(content: str, filename: str) -> list[ParsedDependency]:
        """解析 package.json 中的 dependencies / devDependencies / peerDependencies。"""
        deps: list[ParsedDependency] = []
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return deps

        sections: dict[str, str] = {
            "dependencies": "core",
            "devDependencies": "dev",
            "peerDependencies": "peer",
        }
        for section, category in sections.items():
            for name, version in data.get(section, {}).items():
                deps.append(ParsedDependency(
                    name=name, version=str(version), source_file=filename, category=category,
                ))
        return deps

    # ── Java 生态 ─────────────────────────────────────

    @staticmethod
    def parse_pom_xml(content: str, filename: str) -> list[ParsedDependency]:
        """解析 pom.xml 中的 <dependency> 声明（简单正则提取）。"""
        deps: list[ParsedDependency] = []
        # 匹配 <dependency> 块内的 groupId + artifactId + version
        pattern = re.compile(
            r'<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>\s*<version>([^<]*)</version>',
            re.DOTALL,
        )
        for m in pattern.finditer(content):
            group = m.group(1)
            artifact = m.group(2)
            ver = m.group(3) or None
            deps.append(ParsedDependency(
                name=f"{group}:{artifact}",
                version=ver,
                source_file=filename,
                category="core",
            ))

        # 标记 test scope
        test_pattern = re.compile(
            r'<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>\s*<version>([^<]*)</version>.*?<scope>test</scope>',
            re.DOTALL,
        )
        test_ids = {
            f"{m.group(1)}:{m.group(2)}"
            for m in test_pattern.finditer(content)
        }
        for dep in deps:
            if dep.name in test_ids:
                dep.category = "test"

        return deps

    @staticmethod
    def parse_gradle(content: str, filename: str) -> list[ParsedDependency]:
        """解析 build.gradle 中的依赖声明（简单正则）。"""
        deps: list[ParsedDependency] = []
        # implementation 'group:artifact:version'
        # testImplementation 'group:artifact:version'
        pattern = re.compile(
            r'(implementation|api|compileOnly|testImplementation|androidTestImplementation)\s+[\'"]([^\'"]+)[\'"]',
        )
        for m in pattern.finditer(content):
            scope = m.group(1)
            coord = m.group(2)
            parts = coord.split(":")
            name = f"{parts[0]}:{parts[1]}" if len(parts) >= 2 else coord
            ver = parts[2] if len(parts) >= 3 else None

            if scope.startswith("test") or scope.startswith("androidTest"):
                cat = "test"
            elif scope == "compileOnly":
                cat = "dev"
            else:
                cat = "core"

            deps.append(ParsedDependency(
                name=name, version=ver, source_file=filename, category=cat,
            ))
        return deps

    # ── Go 生态 ───────────────────────────────────────

    @staticmethod
    def parse_go_mod(content: str, filename: str) -> list[ParsedDependency]:
        """解析 go.mod 中的 require 块。"""
        deps: list[ParsedDependency] = []
        in_require = False
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("require ("):
                in_require = True
                continue
            if in_require:
                if line == ")":
                    in_require = False
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    deps.append(ParsedDependency(
                        name=parts[0], version=parts[1], source_file=filename, category="core",
                    ))
            else:
                m = re.match(r'^require\s+(\S+)\s+(\S+)', line)
                if m:
                    deps.append(ParsedDependency(
                        name=m.group(1), version=m.group(2), source_file=filename, category="core",
                    ))
        return deps

    # ── Rust 生态 ─────────────────────────────────────

    @staticmethod
    def parse_cargo_toml(content: str, filename: str) -> list[ParsedDependency]:
        """解析 Cargo.toml 中的依赖块。"""
        deps: list[ParsedDependency] = []
        try:
            data = tomllib.loads(content)
        except Exception:
            return deps

        sections: dict[str, str] = {
            "dependencies": "core",
            "dev-dependencies": "dev",
            "build-dependencies": "build",
        }
        for section, category in sections.items():
            deps_data = data.get(section, {})
            if not isinstance(deps_data, dict):
                continue
            for name, info in deps_data.items():
                if isinstance(info, str):
                    deps.append(ParsedDependency(
                        name=name, version=info, source_file=filename, category=category,
                    ))
                elif isinstance(info, dict):
                    ver = info.get("version")
                    deps.append(ParsedDependency(
                        name=name,
                        version=str(ver) if ver else None,
                        source_file=filename,
                        category=category,
                    ))
        return deps
