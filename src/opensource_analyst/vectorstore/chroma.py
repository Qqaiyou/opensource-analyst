"""ChromaDB 向量存储封装."""

import os
from typing import Any, Optional

from chromadb import Client as ChromaClient
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings


class DashScopeEmbeddings(Embeddings):
    """阿里百炼 Embedding 适配器 — 兼容 OpenAI 接口但适配百炼参数格式."""

    def __init__(self, api_key: str, model: str = "text-embedding-v4") -> None:
        self.api_key = api_key
        self.model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        import time
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # 逐条请求，带重试
        embeddings: list[list[float]] = []
        for text in texts:
            for attempt in range(3):
                try:
                    resp = httpx.post(
                        "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
                        headers=headers,
                        json={
                            "model": self.model,
                            "input": text,
                        },
                        timeout=60.0,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        embeddings.append(data["data"][0]["embedding"])
                        break
                except Exception:
                    if attempt < 2:
                        time.sleep(2 * (attempt + 1))
                    else:
                        raise
            else:
                raise RuntimeError(
                    f"百炼 Embedding 失败 [{resp.status_code}]: {resp.text[:300]}"
                )

        return embeddings

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class VectorStore:
    """封装 ChromaDB 的向量存储和检索操作。

    使用方式:
        store = VectorStore("msiemens_tinydb")
        store.add_texts(["code chunk 1", "code chunk 2"], metadatas=[...])
        results = store.similarity_search("how does database work?", k=5)
    """

    def __init__(
        self,
        collection_name: str,
        persist_dir: str = ".chroma",
    ) -> None:
        api_key = os.getenv("DASH_SCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASH_SCOPE_API_KEY 未设置。请在 .env 文件中配置。")

        self._embeddings = DashScopeEmbeddings(api_key)

        self._client = ChromaClient(Settings(
            persist_directory=persist_dir,
            anonymized_telemetry=False,
        ))

        self._collection_name = collection_name

        self._store = Chroma(
            client=self._client,
            collection_name=collection_name,
            embedding_function=self._embeddings,
            persist_directory=persist_dir,
        )

    def add_texts(
        self, texts: list[str], metadatas: Optional[list[dict]] = None
    ) -> list[str]:
        """向量化文本并存入 Collection。"""
        docs = self._store.add_texts(texts=texts, metadatas=metadatas)
        return docs  # type: ignore[no-any-return]

    def similarity_search(self, query: str, k: int = 5) -> list[dict]:
        """语义搜索，返回最相关的 k 个文档。"""
        docs = self._store.similarity_search(query, k=k)
        results: list[dict] = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": doc.metadata.get("score"),
            })
        return results

    def count(self) -> int:
        """返回 Collection 内已存储的文档数。"""
        try:
            collection = self._client.get_collection(self._collection_name)
            return collection.count()
        except Exception:
            return 0

    def delete_collection(self) -> None:
        """删除当前 Collection（重新索引时使用）。"""
        self._client.delete_collection(self._collection_name)
