"""代码文件索引器 — 下载、过滤、分块、向量化."""

import asyncio
from typing import Optional

import httpx
from langchain_text_splitters import RecursiveCharacterTextSplitter

from opensource_analyst.vectorstore.chroma import VectorStore

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".toml", ".yaml", ".yml", ".json",
    ".xml", ".cfg", ".ini", ".sql", ".css", ".html",
}

EXCLUDE_DIRS = {"tests", "test", "docs", "node_modules", ".git", "__pycache__"}
EXCLUDE_FILES = {".lock", ".md", ".rst", ".txt", "Makefile", "LICENSE", ".gitignore", ".png", ".svg", ".ico"}
MAX_FILE_SIZE = 500_000  # 500KB
MAX_INDEX_FILES = 200


class CodeIndexer:
    """将 GitHub 仓库代码建向量索引。

    使用方式:
        store = VectorStore("msiemens_tinydb")
        indexer = CodeIndexer(store)
        count = await indexer.index_repo("msiemens", "tinydb", file_tree)
    """

    def __init__(self, vector_store: VectorStore) -> None:
        self._store = vector_store
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""],
        )

    async def index_repo(
        self,
        owner: str,
        repo: str,
        file_tree: list[str],
        github_token: Optional[str] = None,
    ) -> int:
        """索引整个仓库，返回成功索引的文件数。

        Args:
            owner: 仓库拥有者
            repo: 仓库名
            file_tree: M2 产出的文件路径列表
            github_token: GitHub Token（可选，用于更高限流）
        """
        # 1. 过滤代码文件
        code_files = self._filter_files(file_tree)
        code_files = code_files[:MAX_INDEX_FILES]

        # 2. 并发下载文件内容
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = [
                self._fetch_file_content(client, owner, repo, path, github_token)
                for path in code_files
            ]
            contents = await asyncio.gather(*tasks)

        # 3. 分块 + 索引
        indexed = 0
        for path, content in zip(code_files, contents):
            if content is None:
                continue

            chunks = self._split_text(content, path)
            if not chunks:
                continue

            texts = [c["content"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]
            self._store.add_texts(texts, metadatas=metadatas)
            indexed += 1

        return indexed

    def _filter_files(self, file_tree: list[str]) -> list[str]:
        """过滤出需要索引的代码文件。"""
        result: list[str] = []
        for path in file_tree:
            parts = path.split("/")
            if any(d in EXCLUDE_DIRS for d in parts):
                continue
            if any(path.endswith(ext) for ext in EXCLUDE_FILES):
                continue
            ext = "." + path.split(".")[-1] if "." in path else ""
            if ext not in CODE_EXTENSIONS:
                continue
            result.append(path)
        return result

    async def _fetch_file_content(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        path: str,
        github_token: Optional[str] = None,
    ) -> Optional[str]:
        """从 GitHub raw 下载单个文件内容。"""
        headers: dict[str, str] = {}
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        # 先尝试 master，失败再试 main
        for branch in ["master", "main"]:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    text = resp.text
                    if len(text) > MAX_FILE_SIZE:
                        return None
                    return text
            except Exception:
                continue

        return None

    def _split_text(self, content: str, file_path: str) -> list[dict]:
        """将文件内容分块，每块带文件路径元数据。"""
        chunks = self._splitter.create_documents(
            texts=[content],
            metadatas=[{"source": file_path}],
        )
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in chunks
        ]
