"""MCP Client 层 — MCPServerConnection + MCPClientManager.

通过 stdio transport 连接外部 MCP Server 进程，提供统一的工具发现与调用接口。
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from mcp import Tool
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from opensource_analyst.mcp.config import MCPServerConfig, MCPToolInfo, MCPToolResult

logger = logging.getLogger(__name__)


def _tool_to_info(server_name: str, tool: Tool) -> MCPToolInfo:
    """将 MCP SDK Tool 对象转为项目内部的 MCPToolInfo."""
    return MCPToolInfo(
        server_name=server_name,
        tool_name=tool.name,
        description=tool.description or "",
        input_schema=tool.inputSchema if isinstance(tool.inputSchema, dict) else {},
    )


class MCPServerConnection:
    """单个 MCP Server 的 stdio transport 连接管理.

    用法:
        async with MCPServerConnection(config) as conn:
            tools = await conn.list_tools()
            result = await conn.call_tool("echo", {"msg": "hello"})
    """

    def __init__(self, config: MCPServerConfig) -> None:
        self.config = config
        self._session: ClientSession | None = None
        self._stdio_ctx: Any = None   # stdio_client async generator context
        self._read: Any = None
        self._write: Any = None

    async def connect(self) -> None:
        """启动子进程并建立 MCP 会话."""
        params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args,
            env=self.config.env,
        )
        try:
            self._stdio_ctx = stdio_client(params)
            self._read, self._write = await self._stdio_ctx.__aenter__()
        except Exception:
            logger.exception("Failed to spawn MCP Server '%s'", self.config.name)
            self._stdio_ctx = None
            raise RuntimeError(f"MCP Server '{self.config.name}' 启动失败")

        session = ClientSession(self._read, self._write)
        await session.__aenter__()
        await session.initialize()
        self._session = session
        logger.info("MCP Server '%s' 已连接", self.config.name)

    async def disconnect(self) -> None:
        """关闭 session 并清理子进程."""
        if self._session is not None:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception:
                logger.warning("Error closing session for '%s'", self.config.name, exc_info=True)
            self._session = None
        if self._stdio_ctx is not None:
            try:
                await self._stdio_ctx.__aexit__(None, None, None)
            except Exception:
                logger.warning("Error closing stdio for '%s'", self.config.name, exc_info=True)
            self._stdio_ctx = None
            self._read = None
            self._write = None
        logger.info("MCP Server '%s' 已断开", self.config.name)

    async def list_tools(self) -> list[MCPToolInfo]:
        """列出该 Server 提供的所有工具."""
        if self._session is None:
            raise RuntimeError(f"Server '{self.config.name}' 未连接，请先调用 connect()")
        result = await self._session.list_tools()
        return [_tool_to_info(self.config.name, t) for t in result.tools]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> MCPToolResult:
        """调用指定工具并返回结果."""
        if self._session is None:
            raise RuntimeError(f"Server '{self.config.name}' 未连接，请先调用 connect()")
        try:
            raw = await self._session.call_tool(tool_name, arguments or {})
            content_blocks = [
                block.model_dump(mode="json") for block in raw.content
            ]
            return MCPToolResult(
                server_name=self.config.name,
                tool_name=tool_name,
                content=content_blocks,
                is_error=raw.isError or False,
            )
        except Exception:
            logger.exception(
                "Tool call '%s/%s' failed", self.config.name, tool_name
            )
            raise

    async def __aenter__(self) -> "MCPServerConnection":
        await self.connect()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.disconnect()


class MCPClientManager:
    """管理多个 MCP Server 连接 — 统一的生命周期 + 跨 Server 工具路由.

    用法:
        async with MCPClientManager([github_cfg, fs_cfg]) as manager:
            all_tools = await manager.list_all_tools()
            result = await manager.call_tool("github", "search_issues", {"q": "bug"})
    """

    def __init__(self, configs: list[MCPServerConfig]) -> None:
        self.configs = configs
        self._connections: dict[str, MCPServerConnection] = {}

    async def connect_all(self) -> None:
        """并行连接所有已启用的 Server."""
        enabled = [c for c in self.configs if c.enabled]
        for cfg in enabled:
            conn = MCPServerConnection(cfg)
            try:
                await conn.connect()
                self._connections[cfg.name] = conn
            except RuntimeError:
                logger.warning("跳过 MCP Server '%s'（连接失败）", cfg.name)

        if self._connections:
            logger.info("已连接 %d/%d MCP Server", len(self._connections), len(enabled))
        else:
            logger.info("没有可用的 MCP Server 连接")

    async def disconnect_all(self) -> None:
        """断开所有连接."""
        for name, conn in list(self._connections.items()):
            await conn.disconnect()
            del self._connections[name]

    async def list_all_tools(self) -> list[MCPToolInfo]:
        """列出所有已连接 Server 的全部工具."""
        all_tools: list[MCPToolInfo] = []
        for conn in self._connections.values():
            try:
                all_tools.extend(await conn.list_tools())
            except Exception:
                logger.warning(
                    "无法列出 Server '%s' 的工具", conn.config.name, exc_info=True
                )
        return all_tools

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> MCPToolResult:
        """调用指定 Server 上的指定工具."""
        conn = self._connections.get(server_name)
        if conn is None:
            raise ValueError(f"MCP Server '{server_name}' 未连接或不存在")
        return await conn.call_tool(tool_name, arguments)

    def get_connection(self, name: str) -> MCPServerConnection | None:
        return self._connections.get(name)

    async def __aenter__(self) -> "MCPClientManager":
        await self.connect_all()
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.disconnect_all()
