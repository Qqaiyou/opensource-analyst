"""FastAPI 应用入口."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from opensource_analyst.api.analyze import router as analyze_router
from opensource_analyst.api.task import router as task_router
from opensource_analyst.api.chat import router as chat_router
from opensource_analyst.api.conversation import router as conversation_router, init_conversation_mcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(
    title="OpenSource Analyst",
    description="基于 LangGraph + Multi-Agent + MCP + RAG 的开源项目分析平台",
    version="0.2.0",
)

app.include_router(analyze_router)
app.include_router(task_router)
app.include_router(chat_router)
app.include_router(conversation_router)

# 挂载前端页面
frontend_dir = Path(__file__).parent / "frontend"
chat_html = frontend_dir / "index.html"


@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """对话前端页面。"""
    if chat_html.exists():
        return HTMLResponse(chat_html.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Chat page not found</h1>", status_code=404)


@app.get("/chat/", response_class=HTMLResponse)
async def chat_page_slash():
    """对话前端页面（带尾部斜杠）。"""
    return await chat_page()


@app.get("/")
async def root() -> dict[str, str]:
    """根路径 - 服务状态."""
    return {"message": "OpenSource Analyst is running!"}


@app.get("/health")
async def health() -> dict[str, str]:
    """健康检查端点."""
    return {"status": "ok"}


@app.get("/dashboard")
async def dashboard() -> HTMLResponse:
    """Phase 2 仪表板页面（遗留）。"""
    dashboard_path = Path("docs/phase2-dashboard.html")
    if dashboard_path.exists():
        return HTMLResponse(dashboard_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)
