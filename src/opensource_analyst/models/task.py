"""任务相关数据模型."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from opensource_analyst.models.analysis import AnalysisResult


class AnalyzeRequest(BaseModel):
    """POST /analyze 请求体。"""

    repo_url: str = Field(..., examples=["https://github.com/msiemens/tinydb"])


class TaskStatus(BaseModel):
    """任务状态信息。"""

    task_id: str
    status: str  # "pending" | "running" | "completed" | "error"
    repo_url: str
    created_at: str


class TaskResult(BaseModel):
    """任务完成后的完整结果。"""

    task_id: str
    status: str
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None
