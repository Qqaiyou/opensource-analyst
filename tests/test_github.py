"""GitHub 模块测试 — 使用 TinyDB 作为真实测试目标."""

import pytest
from src.opensource_analyst.github.client import (
    GitHubClient,
    GitHubAPIError,
    RepoNotFoundError,
    RateLimitError,
)
from src.opensource_analyst.github.readme import ReadmeFetcher
from src.opensource_analyst.github.parser import RepoParser

TARGET = ("msiemens", "tinydb")


# ── URL 解析（单元测试） ──────────────────────────

class TestParseUrl:
    def test_valid_url(self) -> None:
        owner, repo = GitHubClient.parse_url(
            "https://github.com/msiemens/tinydb"
        )
        assert owner == "msiemens"
        assert repo == "tinydb"

    def test_url_with_trailing_slash(self) -> None:
        owner, repo = GitHubClient.parse_url(
            "https://github.com/msiemens/tinydb/"
        )
        assert owner == "msiemens"
        assert repo == "tinydb"

    def test_not_github_url(self) -> None:
        with pytest.raises(ValueError, match="不是有效的 GitHub URL"):
            GitHubClient.parse_url("https://gitlab.com/user/repo")

    def test_too_short_url(self) -> None:
        with pytest.raises(ValueError, match="无法从 URL 提取 owner/repo"):
            GitHubClient.parse_url("https://github.com/owneronly")


# ── API 集成测试 ────────────────────────────────

@pytest.fixture
async def client() -> GitHubClient:
    c = GitHubClient()
    yield c
    await c.close()


@pytest.mark.anyio
async def test_fetch_readme() -> None:
    async with GitHubClient() as c:
        fetcher = ReadmeFetcher(c)
        content = await fetcher.fetch_readme(*TARGET)
        assert len(content) > 100
        assert "TinyDB" in content


@pytest.mark.anyio
async def test_fetch_file_tree() -> None:
    async with GitHubClient() as c:
        parser = RepoParser(c)
        files = await parser.fetch_file_tree(*TARGET)
        assert len(files) > 0
        assert "tinydb/__init__.py" in files


@pytest.mark.anyio
async def test_fetch_languages() -> None:
    async with GitHubClient() as c:
        parser = RepoParser(c)
        langs = await parser.fetch_languages(*TARGET)
        assert "Python" in langs


@pytest.mark.anyio
async def test_repo_not_found() -> None:
    async with GitHubClient() as c:
        parser = RepoParser(c)
        with pytest.raises(RepoNotFoundError):
            await parser.fetch_file_tree("this-user-does-not-exist-xyz", "fake-repo-123456")


@pytest.mark.anyio
async def test_full_flow() -> None:
    """端到端：从 URL 到 RepoInfo 的完整流程。"""
    from src.opensource_analyst.models.repo import RepoInfo

    owner, repo = GitHubClient.parse_url("https://github.com/msiemens/tinydb")

    async with GitHubClient() as c:
        readme = await ReadmeFetcher(c).fetch_readme(owner, repo)
        files = await RepoParser(c).fetch_file_tree(owner, repo)
        langs = await RepoParser(c).fetch_languages(owner, repo)

    info = RepoInfo(
        owner=owner, repo=repo,
        readme=readme, file_tree=files, languages=langs,
    )

    assert info.owner == "msiemens"
    assert info.repo == "tinydb"
    assert len(info.readme) > 100
    assert "tinydb/__init__.py" in info.file_tree
    assert "Python" in info.languages
