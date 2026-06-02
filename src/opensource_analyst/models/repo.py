"""仓库数据模型."""

from pydantic import BaseModel


class RepoInfo(BaseModel):
    """GitHub 仓库的完整信息，供后续 Agent 使用。"""

    owner: str
    repo: str
    readme: str
    file_tree: list[str]
    languages: dict[str, int]
