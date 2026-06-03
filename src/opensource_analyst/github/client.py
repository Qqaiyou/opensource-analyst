"""GitHub API 客户端 — 认证、请求、错误处理、URL 解析."""

import os
from urllib.parse import urlparse
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()


class GitHubAPIError(Exception):
    """GitHub API 通用错误."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"GitHub API [{status_code}]: {message}")


class RepoNotFoundError(GitHubAPIError):
    """仓库不存在或为私有 (404)."""

    def __init__(self, owner: str, repo: str) -> None:
        super().__init__(404, f"仓库 {owner}/{repo} 不存在或为私有")


class RateLimitError(GitHubAPIError):
    """API 速率限制 (403)."""

    def __init__(self) -> None:
        super().__init__(403, "API 速率限制。请设置 GITHUB_TOKEN 环境变量提高限额。")


class GitHubClient:
    """GitHub REST API 异步客户端。

    使用方式:
        client = GitHubClient()
        data = await client._request("/repos/msiemens/tinydb")
        await client.close()
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None) -> None:
        headers: dict[str, str] = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "opensource-analyst",
        }
        token = token or os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=30.0,
            transport=httpx.AsyncHTTPTransport(trust_env=False),
        )

    @staticmethod
    def parse_url(url: str) -> tuple[str, str]:
        """从 GitHub URL 提取 (owner, repo)。

        >>> GitHubClient.parse_url("https://github.com/msiemens/tinydb")
        ("msiemens", "tinydb")
        """
        parsed = urlparse(url)
        if parsed.netloc != "github.com":
            raise ValueError(f"不是有效的 GitHub URL: {url}")

        parts = parsed.path.strip("/").split("/")
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise ValueError(f"无法从 URL 提取 owner/repo: {url}")

        repo = parts[1]
        # 去掉可能的 .git 后缀
        if repo.endswith(".git"):
            repo = repo[:-4]
        return parts[0], repo

    async def _request(self, path: str, owner: str = "unknown", repo: str = "unknown") -> dict:
        """发送 GET 请求到 GitHub API，处理错误。"""
        response = await self._client.get(path)

        if response.status_code == 404:
            raise RepoNotFoundError(owner, repo)
        if response.status_code == 403 and "rate limit" in response.text.lower():
            raise RateLimitError()
        if response.status_code >= 400:
            raise GitHubAPIError(response.status_code, response.text[:200])

        return response.json()

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def close(self) -> None:
        """关闭 HTTP 客户端。"""
        await self._client.aclose()
