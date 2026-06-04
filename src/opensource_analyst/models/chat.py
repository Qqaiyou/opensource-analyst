"""RAG 对话数据模型."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /chat 请求体。"""

    repo_url: str = Field(..., examples=["https://github.com/msiemens/tinydb"])
    question: str = Field(
        ..., min_length=1, max_length=2000,
        examples=["这个项目怎么实现数据库查询？"],
    )


class SourceInfo(BaseModel):
    """引用来源。"""

    file: str
    score: float | None = None


class ChatResponse(BaseModel):
    """POST /chat 响应体。"""

    question: str
    answer: str
    repo_url: str
    sources: list[SourceInfo] = []
