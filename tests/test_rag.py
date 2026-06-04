"""RAG 模块测试 — 百炼 Embedding + ChromaDB + TinyDB 索引检索."""

import os

import pytest
from dotenv import load_dotenv

load_dotenv()

from opensource_analyst.vectorstore.chroma import VectorStore
from opensource_analyst.rag.indexer import CodeIndexer
from opensource_analyst.rag.retriever import CodeRetriever

COLLECTION = "test_tinydb_m4"
TINYDB_FILES = [
    "tinydb/__init__.py",
    "tinydb/database.py",
    "tinydb/table.py",
    "tinydb/queries.py",
    "tinydb/storages.py",
    "tinydb/middlewares.py",
    "tinydb/operations.py",
    "tinydb/utils.py",
    "tinydb/version.py",
    "setup.py",
    "README.rst",
    "LICENSE",
    "Makefile",
    "tests/test_tinydb.py",
    "docs/conf.py",
]


# ── 单元测试：文件过滤逻辑（不依赖 VectorStore） ──

class TestFilter:
    """_filter_files 是纯逻辑，可以直接测。"""

    def test_python_files_included(self) -> None:
        # 不通过 CodeIndexer，直接测静态逻辑
        from opensource_analyst.rag.indexer import CODE_EXTENSIONS, EXCLUDE_DIRS

        result: list[str] = []
        for path in TINYDB_FILES:
            parts = path.split("/")
            if any(d in EXCLUDE_DIRS for d in parts):
                continue
            ext = "." + path.split(".")[-1] if "." in path else ""
            if ext not in CODE_EXTENSIONS:
                continue
            result.append(path)

        assert "tinydb/database.py" in result
        assert "tinydb/__init__.py" in result

    def test_docs_excluded(self) -> None:
        from opensource_analyst.rag.indexer import EXCLUDE_DIRS

        filtered: list[str] = []
        for path in TINYDB_FILES:
            parts = path.split("/")
            if any(d in EXCLUDE_DIRS for d in parts):
                continue
            filtered.append(path)

        assert "docs/conf.py" not in filtered
        assert "tests/test_tinydb.py" not in filtered

    def test_readme_excluded_by_extension(self) -> None:
        from opensource_analyst.rag.indexer import CODE_EXTENSIONS

        ext = "." + "README.rst".split(".")[-1]
        assert ext not in CODE_EXTENSIONS


# ── Embedding 集成测试 ──────────────────────

class TestEmbedding:
    @pytest.fixture(autouse=True)
    def _cleanup(self) -> None:
        yield
        try:
            VectorStore("_emb_test").delete_collection()
        except Exception:
            pass

    def test_embedding_returns_1024_dim(self) -> None:
        """验证百炼 text-embedding-v4 返回 1024 维向量。"""
        from opensource_analyst.vectorstore.chroma import DashScopeEmbeddings

        emb = DashScopeEmbeddings(api_key=os.getenv("DASH_SCOPE_API_KEY") or "")
        result = emb.embed_query("Hello world")
        assert len(result) == 1024


# ── RAG 全链路集成测试 ──────────────────────

@pytest.fixture(scope="module")
def vector_store() -> VectorStore:
    store = VectorStore(COLLECTION)
    yield store
    store.delete_collection()


class TestRAGFlow:
    def test_index_and_search(self, vector_store: VectorStore) -> None:
        """完整流程：索引 TinyDB 代码 → 搜索 → 验证结果。"""
        import asyncio

        indexer = CodeIndexer(vector_store)
        retriever = CodeRetriever(vector_store)

        count = asyncio.run(
            indexer.index_repo(
                "msiemens",
                "tinydb",
                TINYDB_FILES,
                github_token=os.getenv("GITHUB_TOKEN"),
            )
        )
        assert count > 0

        results = retriever.search("数据库存储和查询", k=3)
        assert len(results) >= 1
        assert len(results[0]["content"]) > 20

    def test_search_as_context_format(self, vector_store: VectorStore) -> None:
        """验证 search_as_context 返回格式正确的上下文文本。"""
        retriever = CodeRetriever(vector_store)
        context = retriever.search_as_context("middleware", k=2)

        assert "🔹" in context
        assert "```" in context
