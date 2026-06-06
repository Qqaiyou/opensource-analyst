"""MCP 配置模型 — MCPServerConfig, MCPToolInfo, MCPToolResult."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """单个 MCP Server 的启动配置.

    Example:
        MCPServerConfig(
            name="github",
            command="npx",
            args=["-y", "@anthropic/mcp-server-github"],
            env={"GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]},
        )
    """

    name: str = Field(description="逻辑名称，如 'github' / 'filesystem'")
    command: str = Field(description="启动命令，如 'npx' / 'python'")
    args: list[str] = Field(default_factory=list, description="命令参数")
    env: dict[str, str] | None = Field(default=None, description="环境变量")
    enabled: bool = Field(default=True, description="是否启用")


class MCPToolInfo(BaseModel):
    """MCP Tool 的元信息 — 供 Agent 发现工具时使用."""

    server_name: str
    tool_name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)


class MCPToolResult(BaseModel):
    """单次 Tool 调用结果."""

    server_name: str
    tool_name: str
    content: list[dict[str, Any]] = Field(default_factory=list)
    is_error: bool = False
