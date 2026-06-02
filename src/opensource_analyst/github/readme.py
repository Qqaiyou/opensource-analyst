"""README 获取与解析."""

import base64
from src.opensource_analyst.github.client import GitHubClient, RepoNotFoundError


class ReadmeFetcher:
    """从 GitHub API 获取 README 内容。

    使用方式:
        client = GitHubClient()
        fetcher = ReadmeFetcher(client)
        content = await fetcher.fetch_readme("msiemens", "tinydb")
    """

    def __init__(self, client: GitHubClient) -> None:
        self._client = client

    async def fetch_readme(self, owner: str, repo: str) -> str:
        """获取仓库 README 的 Markdown 原文。

        Args:
            owner: 仓库拥有者，如 "msiemens"
            repo: 仓库名，如 "tinydb"

        Returns:
            README 的纯文本 Markdown 内容

        Raises:
            RepoNotFoundError: 仓库不存在或 README 不存在
        """
        try:
            data = await self._client._request(f"/repos/{owner}/{repo}/readme")
        except RepoNotFoundError:
            raise RepoNotFoundError(owner, repo)

        # GitHub README API 返回 base64 编码的内容
        content_b64: str = data.get("content", "")
        content_bytes = base64.b64decode(content_b64)
        return content_bytes.decode("utf-8")
