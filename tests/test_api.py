"""API 集成测试 — 端到端：POST /analyze → 轮询 → 获取结果."""

import time

import pytest
from fastapi.testclient import TestClient

from opensource_analyst.main import app

client = TestClient(app)


def test_root() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "running" in resp.text


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_analyze_invalid_url() -> None:
    resp = client.post("/analyze", json={"repo_url": "https://gitlab.com/a/b"})
    assert resp.status_code == 400
    assert "不是有效的 GitHub URL" in resp.json()["detail"]


def test_analyze_full_flow() -> None:
    """完整流程：发起分析 → 轮询 → 获取结果。"""
    # 1) 发起分析
    resp = client.post(
        "/analyze",
        json={"repo_url": "https://github.com/msiemens/tinydb"},
    )
    assert resp.status_code == 202
    data = resp.json()
    task_id = data["task_id"]
    assert data["status"] == "pending"

    # 2) 轮询直到完成
    for _ in range(30):
        resp = client.get(f"/task/{task_id}")
        assert resp.status_code == 200
        status = resp.json()["status"]
        if status in ("completed", "error"):
            break
        time.sleep(3)

    assert status == "completed", f"任务状态: {status}"

    # 3) 获取结果
    resp = client.get(f"/task/{task_id}/result")
    assert resp.status_code == 200
    result = resp.json()
    assert result["task_id"] == task_id
    assert "overview" in result["result"]
    assert "tech_stack" in result["result"]


def test_task_not_found() -> None:
    resp = client.get("/task/nonexistent123")
    assert resp.status_code == 404
    assert "不存在" in resp.json()["detail"]
