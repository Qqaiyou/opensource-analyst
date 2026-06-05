"""FastAPI 应用入口."""

import logging

from fastapi import FastAPI

from opensource_analyst.api.analyze import router as analyze_router
from opensource_analyst.api.task import router as task_router
from opensource_analyst.api.chat import router as chat_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(
    title="OpenSource Analyst",
    description="基于 LangGraph + Multi-Agent + MCP + RAG 的开源项目分析平台",
    version="0.1.0",
)

app.include_router(analyze_router)
app.include_router(task_router)
app.include_router(chat_router)


@app.get("/")
async def root() -> dict[str, str]:
    """根路径 - 服务状态."""
    return {"message": "OpenSource Analyst is running!"}


@app.get("/health")
async def health() -> dict[str, str]:
    """健康检查端点."""
    return {"status": "ok"}
