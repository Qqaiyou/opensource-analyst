"""GET /task/{task_id} — 查询任务状态与结果."""

from fastapi import APIRouter, HTTPException

from opensource_analyst.models.task import TaskStatus, TaskResult
from opensource_analyst.api.analyze import _store

router = APIRouter()


@router.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str) -> TaskStatus:
    """查询任务状态（pending / running / completed / error）。"""
    data = _store.get(task_id)
    if data is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskStatus(**data)


@router.get("/task/{task_id}/result", response_model=TaskResult)
async def get_task_result(task_id: str) -> TaskResult:
    """获取分析结果。仅当 status 为 completed 或 error 时返回。"""
    data = _store.get(task_id)
    if data is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    if data["status"] not in ("completed", "error"):
        raise HTTPException(status_code=409, detail="任务尚未完成，请稍后再试")

    return TaskResult(**data)
