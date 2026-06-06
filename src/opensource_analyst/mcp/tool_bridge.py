"""MCP Tool Bridge — 将 MCP 工具转换为 LangChain StructuredTool.

MCPClientManager.list_all_tools() 返回 MCPToolInfo 列表，
本模块将它们转为 LangGraph ToolNode 可执行的 BaseTool。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, create_model

from opensource_analyst.mcp.client import MCPClientManager
from opensource_analyst.mcp.config import MCPToolInfo

logger = logging.getLogger(__name__)


def _json_schema_to_pydantic(schema: dict[str, Any]) -> type[BaseModel]:
    """将 JSON Schema 转换为 Pydantic 模型，用于 StructuredTool 的参数定义。

    MVP 策略：用一个宽松的 model 接受任意 JSON 字符串参数，
    因为 DeepSeek function calling 对复杂嵌套 schema 的兼容性不稳定。
    """
    return create_model(
        "ToolArgs",
        arguments=(str, ...),  # 单个 JSON string 参数
    )


def _make_mcp_tool(
    manager: MCPClientManager,
    server_name: str,
    tool_info: MCPToolInfo,
) -> StructuredTool:
    """为单个 MCP 工具创建 LangChain StructuredTool。"""

    async def _call(arguments: str = "{}") -> str:
        """调用 MCP 工具。arguments 为 JSON 字符串。"""
        try:
            args_dict = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError:
            args_dict = {}

        result = await manager.call_tool(server_name, tool_info.tool_name, args_dict)
        if result.is_error:
            return f"[MCP Error] {result.content}"
        return json.dumps(result.content, ensure_ascii=False, indent=2)

    # 工具名：mcp_{server}_{tool}，防止冲突
    safe_name = f"mcp_{server_name}_{tool_info.tool_name}".replace("-", "_").replace("/", "_")

    return StructuredTool.from_function(
        coroutine=_call,
        name=safe_name,
        description=f"[MCP/{server_name}] {tool_info.description or tool_info.tool_name}",
        args_schema=_json_schema_to_pydantic(tool_info.input_schema),
    )


async def build_mcp_tools(manager: MCPClientManager) -> list[StructuredTool]:
    """从 MCPClientManager 构建所有可用 MCP 工具的 LangChain tool 列表。"""
    tools: list[StructuredTool] = []
    try:
        all_tools = await manager.list_all_tools()
    except Exception:
        logger.warning("无法列出 MCP 工具，对话中将无 MCP 能力", exc_info=True)
        return tools

    for tool_info in all_tools:
        try:
            tool = _make_mcp_tool(manager, tool_info.server_name, tool_info)
            tools.append(tool)
        except Exception:
            logger.warning("转换 MCP 工具 '%s/%s' 失败", tool_info.server_name, tool_info.tool_name, exc_info=True)

    logger.info("已构建 %d 个 MCP LangChain 工具", len(tools))
    return tools
