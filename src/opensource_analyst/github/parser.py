"""文件树 + 语言统计."""

from opensource_analyst.github.client import GitHubClient


class RepoParser:
    """解析 GitHub 仓库的目录结构和语言统计。

    使用方式:
        client = GitHubClient()
        parser = RepoParser(client)
        files = await parser.fetch_file_tree("msiemens", "tinydb")
        langs = await parser.fetch_languages("msiemens", "tinydb")
    """

    def __init__(self, client: GitHubClient) -> None:
        self._client = client

    async def fetch_file_tree(self, owner: str, repo: str) -> list[str]:
        """获取仓库完整文件路径列表（递归）。

        Returns:
            文件路径列表，如 ["tinydb/__init__.py", "tinydb/database.py"]
        """
        # 先获取仓库信息，拿到默认分支名
        repo_data = await self._client._request(
            f"/repos/{owner}/{repo}", owner=owner, repo=repo
        )
        default_branch: str = repo_data.get("default_branch", "main")

        data = await self._client._request(
            f"/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1",
            owner=owner, repo=repo,
        )

        tree: list[dict] = data.get("tree", [])
        return [
            item["path"]
            for item in tree
            if item.get("type") == "blob"
        ]

    async def fetch_languages(self, owner: str, repo: str) -> dict[str, int]:
        """获取仓库语言统计。

        Returns:
            语言与字节数映射，如 {"Python": 85642, "Shell": 123}
        """
        data = await self._client._request(
            f"/repos/{owner}/{repo}/languages",
            owner=owner, repo=repo,
        )

        return dict(data)
