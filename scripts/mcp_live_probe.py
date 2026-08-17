#!/usr/bin/env python3
"""Drive the shipped MCP stdio server: initialize, tools/list, search."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DEFAULT_QUERY = "SCA3发病年龄的临床预测模型构建与罕见变异关联研究"
SERVER = Path(__file__).resolve().parents[1] / ".venv" / "bin" / "cnki-scholar"


def _tool_dump(tools) -> dict:
    return {
        "names": [tool.name for tool in tools.tools],
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in tools.tools
        ],
    }


def _call_dump(result) -> dict:
    structured = getattr(result, "structuredContent", None)
    texts = []
    for block in result.content or []:
        text = getattr(block, "text", None)
        if text:
            texts.append(text)
    parsed = structured
    if parsed is None and texts:
        try:
            parsed = json.loads(texts[0])
        except json.JSONDecodeError:
            parsed = None
    return {
        "isError": getattr(result, "isError", False),
        "structured": parsed,
        "texts": texts,
    }


async def _session_call(query: str) -> tuple[dict, dict]:
    params = StdioServerParameters(
        command=str(SERVER),
        args=[],
        cwd=str(SERVER.parent.parent),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            called = await session.call_tool("search", {"query": query})
            return _tool_dump(listed), _call_dump(called)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--list-out", type=Path, required=True)
    parser.add_argument("--search-out", type=Path, required=True)
    args = parser.parse_args()
    listed, called = asyncio.run(_session_call(args.query))
    args.list_out.write_text(json.dumps(listed, ensure_ascii=False, indent=2), encoding="utf-8")
    args.search_out.write_text(json.dumps(called, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"list": listed["names"], "search_error": called["isError"]}, ensure_ascii=False))
    return 0 if "search" in listed["names"] and not called["isError"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
