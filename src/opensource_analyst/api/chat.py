"""POST /chat — RAG 对话接口."""

from fastapi import APIRouter, HTTPException

from opensource_analyst.models.chat import ChatRequest, ChatResponse, SourceInfo
from opensource_analyst.github.client import GitHubClient
from opensource_analyst.vectorstore.chroma import VectorStore
from opensource_analyst.rag.retriever import CodeRetriever
from opensource_analyst.agents.base import BaseAgent
from opensource_analyst.prompts.chat import CHAT_PROMPT

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """基于 RAG 索引的仓库对话——用自然语言对代码提问。

    需要先对同一 repo_url 调用 POST /analyze 建好索引。
    集合名由 repo_url 推导：{owner}_{repo}。
    """
    try:
        owner, repo = GitHubClient.parse_url(req.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    collection = f"{owner}_{repo}"

    # 打开向量索引（先由 /analyze 建好）
    try:
        store = VectorStore(collection)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    retriever = CodeRetriever(store)

    # 语义检索
    raw_results = retriever.search(req.question, k=10)
    code_context = retriever.search_as_context(req.question, k=10)

    # README 摘要：用第一条结果的 content 的前 500 字符作为项目简介
    readme_summary = ""
    if raw_results:
        readme_summary = raw_results[0].get("content", "")[:500]

    prompt = CHAT_PROMPT.format(
        question=req.question,
        readme_summary=readme_summary,
        code_context=code_context,
    )

    agent = BaseAgent()
    answer = agent._invoke(prompt)

    sources = [
        SourceInfo(
            file=r.get("metadata", {}).get("source", "unknown"),
            score=r.get("score"),
        )
        for r in raw_results
    ]

    return ChatResponse(
        question=req.question,
        answer=answer,
        repo_url=req.repo_url,
        sources=sources,
    )
