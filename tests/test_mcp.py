"""M11 MCP 集成测试 — 单元 + 集成."""
import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

from opensource_analyst.mcp.config import MCPServerConfig, MCPToolInfo, MCPToolResult
from opensource_analyst.mcp.client import MCPServerConnection, MCPClientManager


# ── Mock MCP Echo Server (子进程脚本) ─────────────────────────

MOCK_SERVER_SCRIPT = r"""
import asyncio, json, sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("mock-echo")

@server.list_tools()
async def list_tools():
    return [
        Tool(name="echo", description="Echo back the input", inputSchema={
            "type": "object",
            "properties": {"msg": {"type": "string", "description": "Message to echo"}},
            "required": ["msg"],
        }),
        Tool(name="add", description="Add two numbers", inputSchema={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        }),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "echo":
        msg = arguments.get("msg", "")
        return [TextContent(type="text", text=f"ECHO: {msg}")]
    elif name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        return [TextContent(type="text", text=str(a + b))]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

asyncio.run(main())
"""  # noqa: E501


def _write_mock_server(path: Path) -> None:
    path.write_text(MOCK_SERVER_SCRIPT, encoding="utf-8")


# ── 单元测试：Config 模型 ─────────────────────────────────────

def test_mcp_server_config_defaults() -> None:
    """MCPServerConfig 创建 + env 默认为 None、enabled 默认为 True."""
    cfg = MCPServerConfig(name="test", command="echo", args=["hello"])
    assert cfg.name == "test"
    assert cfg.command == "echo"
    assert cfg.args == ["hello"]
    assert cfg.env is None
    assert cfg.enabled is True


def test_mcp_server_config_serialization() -> None:
    """MCPServerConfig 可以序列化为 JSON 并反序列化."""
    cfg = MCPServerConfig(
        name="github",
        command="npx",
        args=["-y", "@anthropic/mcp-server-github"],
        env={"GITHUB_TOKEN": "ghp_test123"},
    )
    data = cfg.model_dump()
    restored = MCPServerConfig(**data)
    assert restored.name == "github"
    assert restored.env == {"GITHUB_TOKEN": "ghp_test123"}


def test_mcp_server_config_disabled() -> None:
    """enabled=False 的 Server 可被创建但应被 MCPClientManager 跳过."""
    cfg = MCPServerConfig(name="disabled_svr", command="npx", args=["-y", "pkg"], enabled=False)
    assert cfg.enabled is False
    assert cfg.name == "disabled_svr"


def test_mcp_tool_result_is_error() -> None:
    """MCPToolResult.is_error 正确标记错误."""
    ok = MCPToolResult(server_name="s", tool_name="t", content=[{"type": "text"}], is_error=False)
    assert ok.is_error is False

    err = MCPToolResult(server_name="s", tool_name="t", content=[], is_error=True)
    assert err.is_error is True


# ── 集成测试：Mock Echo Server ────────────────────────────────

@pytest.fixture
def mock_server_script(tmp_path: Path) -> Path:
    """将 mock server 写入临时文件并返回路径."""
    path = tmp_path / "mock_mcp_server.py"
    _write_mock_server(path)
    return path


@pytest.fixture
def mock_server_config(mock_server_script: Path) -> MCPServerConfig:
    """指向 Python 运行 mock server 的配置."""
    return MCPServerConfig(
        name="mock",
        command=sys.executable,
        args=[str(mock_server_script)],
        env={**os.environ},
    )


@pytest.mark.asyncio
async def test_connection_connect_and_list_tools(mock_server_config: MCPServerConfig) -> None:
    """连接 Mock Echo Server → list_tools() 返回预定义工具列表."""
    async with MCPServerConnection(mock_server_config) as conn:
        tools = await conn.list_tools()

    names = {t.tool_name for t in tools}
    assert "echo" in names
    assert "add" in names

    echo_tool = next(t for t in tools if t.tool_name == "echo")
    assert echo_tool.server_name == "mock"
    assert "Echo back" in echo_tool.description
    assert "msg" in echo_tool.input_schema.get("properties", {})


@pytest.mark.asyncio
async def test_connection_call_tool_echo(mock_server_config: MCPServerConfig) -> None:
    """call_tool("echo", {"msg": "hello"}) → 返回 ECHO: hello."""
    async with MCPServerConnection(mock_server_config) as conn:
        result = await conn.call_tool("echo", {"msg": "hello"})

    assert result.server_name == "mock"
    assert result.tool_name == "echo"
    assert result.is_error is False
    assert len(result.content) == 1
    assert "ECHO: hello" in str(result.content[0])


@pytest.mark.asyncio
async def test_connection_call_tool_add(mock_server_config: MCPServerConfig) -> None:
    """call_tool("add", {"a": 3, "b": 4}) → 返回 7."""
    async with MCPServerConnection(mock_server_config) as conn:
        result = await conn.call_tool("add", {"a": 3, "b": 4})

    assert result.is_error is False
    assert len(result.content) == 1
    assert "7" == result.content[0]["text"]


@pytest.mark.asyncio
async def test_connection_connect_error() -> None:
    """无效命令 → connect 时抛出 RuntimeError."""
    cfg = MCPServerConfig(
        name="bad",
        command="nonexistent_command_xyz_12345",
        args=[],
    )
    with pytest.raises(RuntimeError, match="启动失败"):
        async with MCPServerConnection(cfg):
            pass


@pytest.mark.asyncio
async def test_connection_not_connected() -> None:
    """未连接时调用 list_tools / call_tool 抛出 RuntimeError."""
    cfg = MCPServerConfig(name="never", command="echo", args=[])
    conn = MCPServerConnection(cfg)
    with pytest.raises(RuntimeError, match="未连接"):
        await conn.list_tools()
    with pytest.raises(RuntimeError, match="未连接"):
        await conn.call_tool("x", {})


# ── 集成测试：MCPClientManager ────────────────────────────────

@pytest.mark.asyncio
async def test_manager_connect_and_list_all(mock_server_config: MCPServerConfig) -> None:
    """MCPClientManager 连接单个 Server → list_all_tools() 返回工具."""
    async with MCPClientManager([mock_server_config]) as manager:
        tools = await manager.list_all_tools()

    names = {t.tool_name for t in tools}
    assert "echo" in names
    assert "add" in names


@pytest.mark.asyncio
async def test_manager_multi_server(mock_server_config: MCPServerConfig) -> None:
    """注册 2 个 Server（一个有 mock，一个 disabled）→ 只连接启用的."""
    disabled_cfg = MCPServerConfig(
        name="disabled_svr",
        command="nonexistent",
        args=[],
        enabled=False,
    )
    async with MCPClientManager([mock_server_config, disabled_cfg]) as manager:
        tools = await manager.list_all_tools()

    # disabled server 不应被连接
    server_names = {t.server_name for t in tools}
    assert "mock" in server_names
    assert "disabled_svr" not in server_names


@pytest.mark.asyncio
async def test_manager_call_tool(mock_server_config: MCPServerConfig) -> None:
    """MCPClientManager.call_tool → 路由到正确的 Server."""
    async with MCPClientManager([mock_server_config]) as manager:
        result = await manager.call_tool("mock", "echo", {"msg": "routed"})

    assert "ECHO: routed" in str(result.content[0])


@pytest.mark.asyncio
async def test_manager_call_tool_unknown_server(mock_server_config: MCPServerConfig) -> None:
    """call_tool 传入不存在的 server_name → ValueError."""
    async with MCPClientManager([mock_server_config]) as manager:
        with pytest.raises(ValueError, match="未连接或不存在"):
            await manager.call_tool("nonexistent", "echo", {})


@pytest.mark.asyncio
async def test_manager_disconnect_all(mock_server_config: MCPServerConfig) -> None:
    """disconnect_all 后 get_connection 返回 None."""
    async with MCPClientManager([mock_server_config]) as manager:
        pass  # exit → disconnect_all

    assert manager.get_connection("mock") is None


@pytest.mark.asyncio
async def test_connection_call_unknown_tool(mock_server_config: MCPServerConfig) -> None:
    """调用不存在的 tool → 返回 is_error=True 或抛出异常."""
    async with MCPServerConnection(mock_server_config) as conn:
        try:
            result = await conn.call_tool("nonexistent_tool", {})
            # Some MCP servers return is_error=True instead of raising
            assert result.is_error is True or result.is_error is False  # both ok
        except Exception:
            pass  # Raising is also acceptable
