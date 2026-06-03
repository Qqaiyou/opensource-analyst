"""POST /analyze — 发起分析任务."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException

from opensource_analyst.models.task import AnalyzeRequest, TaskStatus, TaskResult
from opensource_analyst.models.analysis import AnalysisResult
from opensource_analyst.github.client import GitHubClient
from opensource_analyst.graph.workflow import build_workflow

router = APIRouter()

# MVP: 内存存储（后续可替换为 Redis）
_store: dict[str, dict] = {}


@router.post("/analyze", response_model=TaskStatus, status_code=202)
async def start_analysis(req: AnalyzeRequest, bg: BackgroundTasks) -> TaskStatus:
    """发起仓库分析任务，立即返回 task_id，后台异步执行。"""
    try:
        GitHubClient.parse_url(req.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    task_id = uuid4().hex[:12]
    now = datetime.now(timezone.utc).isoformat()

    _store[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "repo_url": req.repo_url,
        "created_at": now,
    }

    bg.add_task(_run_analysis, task_id, req.repo_url)

    return TaskStatus(
        task_id=task_id,
        status="pending",
        repo_url=req.repo_url,
        created_at=now,
    )


async def _run_analysis(task_id: str, repo_url: str) -> None:
    """通过 LangGraph 工作流执行分析流水线。"""
    try:
        _store[task_id]["status"] = "running"

        app = build_workflow()
        state = await app.ainvoke({"repo_url": repo_url})

        if state.get("error"):
            raise RuntimeError(state["error"])

        result = AnalysisResult(
            overview=state["overview"],
            tech_stack=state["tech_stack"],
        )

        _store[task_id]["status"] = "completed"
        _store[task_id]["result"] = result.model_dump()
    except Exception as e:
        _store[task_id]["status"] = "error"
        _store[task_id]["error"] = str(e)
