"""RAG 对话接口测试."""

import pytest
from fastapi.testclient import TestClient

from opensource_analyst.main import app
from opensource_analyst.models.chat import ChatRequest, ChatResponse, SourceInfo


client = TestClient(app)


# ── 模型测试 ────────────────────────────────────────────

def test_chat_request_model() -> None:
    """ChatRequest 模型验证。"""
    req = ChatRequest(
        repo_url="https://github.com/msiemens/tinydb",
        question="这个项目的数据库怎么实现的？",
    )
    assert req.repo_url == "https://github.com/msiemens/tinydb"
    assert "数据库" in req.question


def test_chat_request_empty_question_rejected() -> None:
    """空 question 应该被拒绝。"""
    with pytest.raises(Exception):
        ChatRequest(repo_url="https://github.com/a/b", question="")


def test_chat_response_model() -> None:
    """ChatResponse 模型构造。"""
    resp = ChatResponse(
        question="测试问题",
        answer="测试回答",
        repo_url="https://github.com/a/b",
        sources=[
            SourceInfo(file="src/main.py", score=0.92),
            SourceInfo(file="README.md", score=0.85),
        ],
    )
    assert len(resp.sources) == 2
    assert resp.sources[0].file == "src/main.py"


# ── 端点测试 ─────────────────────────────────────────────

def test_chat_invalid_url() -> None:
    """无效 URL 应返回 400。"""
    resp = client.post(
        "/chat",
        json={"repo_url": "https://gitlab.com/a/b", "question": "hello"},
    )
    assert resp.status_code == 400


def test_chat_empty_question() -> None:
    """空 question 应返回 422（Pydantic 校验）。"""
    resp = client.post(
        "/chat",
        json={"repo_url": "https://github.com/a/b", "question": ""},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_chat_integration() -> None:
    """先 analyze 建索引，再用 chat 提问。

    注意：此测试依赖 DASH_SCOPE_API_KEY 和 DEEPSEEK_API_KEY。
    """
    # Step 1: 发起分析（后台建 ChromaDB 索引）
    analyze_resp = client.post(
        "/analyze",
        json={"repo_url": "https://github.com/msiemens/tinydb"},
    )
    assert analyze_resp.status_code == 202
    task_id = analyze_resp.json()["task_id"]

    # Step 2: 轮询等待完成
    import time
    for _ in range(120):
        status_resp = client.get(f"/task/{task_id}")
        if status_resp.json()["status"] in ("completed", "error"):
            break
        time.sleep(3)

    assert status_resp.json()["status"] == "completed", (
        f"分析未完成: {status_resp.json()}"
    )

    # Step 3: 发起对话
    chat_resp = client.post(
        "/chat",
        json={
            "repo_url": "https://github.com/msiemens/tinydb",
            "question": "TinyDB 的查询引擎是怎么实现的？",
        },
    )
    assert chat_resp.status_code == 200

    data = chat_resp.json()
    assert data["question"] == "TinyDB 的查询引擎是怎么实现的？"
    assert len(data["answer"]) > 0
    assert data["repo_url"] == "https://github.com/msiemens/tinydb"
    # 应该有来源引用
    assert len(data["sources"]) > 0, "应该返回代码引用来源"
