"""代码语义检索器 — 搜索 + 上下文拼接."""

from opensource_analyst.vectorstore.chroma import VectorStore


class CodeRetriever:
    """基于向量相似度的代码片段检索器。

    使用方式:
        store = VectorStore("msiemens_tinydb")
        retriever = CodeRetriever(store)
        results = retriever.search("数据库怎么实现的？", k=5)
        context = retriever.search_as_context("查询解析逻辑", k=3)
    """

    def __init__(self, vector_store: VectorStore) -> None:
        self._store = vector_store

    def search(self, query: str, k: int = 5) -> list[dict]:
        """搜索最相关的 k 个代码片段。

        Returns:
            [{content, metadata: {source, ...}, score}, ...]
        """
        return self._store.similarity_search(query, k=k)

    def search_as_context(self, query: str, k: int = 5) -> str:
        """搜索结果拼成 LLM 可用的上下文字符串。

        Returns:
            格式化的上下文文本，每个片段标注来源文件
        """
        results = self.search(query, k=k)
        if not results:
            return "(未找到相关代码)"

        parts: list[str] = []
        for i, r in enumerate(results, 1):
            source = r.get("metadata", {}).get("source", "unknown")
            content = r.get("content", "")
            score = r.get("score")
            score_str = f" [相似度: {score:.2f}]" if score else ""
            parts.append(
                f"🔹 片段 {i} — {source}{score_str}\n```\n{content}\n```"
            )

        return "\n\n".join(parts)
