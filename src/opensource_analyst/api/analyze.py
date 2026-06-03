"""POST /analyze — 发起分析任务."""

import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException

from opensource_analyst.models.task import AnalyzeRequest, TaskStatus, TaskResult
from opensource_analyst.github.client import GitHubClient
from opensource_analyst.github.readme import ReadmeFetcher
from opensource_analyst.github.parser import RepoParser
from opensource_analyst.models.repo import RepoInfo
from opensource_analyst.agents.base import Analyzer

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
    """后台执行完整的分析流水线。"""
    try:
        _store[task_id]["status"] = "running"

        owner, repo = GitHubClient.parse_url(repo_url)

        async with GitHubClient() as gh:
            readme = await ReadmeFetcher(gh).fetch_readme(owner, repo)
            files = await RepoParser(gh).fetch_file_tree(owner, repo)
            langs = await RepoParser(gh).fetch_languages(owner, repo)

        repo_info = RepoInfo(
            owner=owner, repo=repo,
            readme=readme, file_tree=files, languages=langs,
        )

        analyzer = Analyzer()
        result = analyzer.analyze(repo_info)

        _store[task_id]["status"] = "completed"
        _store[task_id]["result"] = result.model_dump()
    except Exception as e:
        _store[task_id]["status"] = "error"
        _store[task_id]["error"] = str(e)
