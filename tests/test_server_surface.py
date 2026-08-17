from __future__ import annotations

from cnki_scholar.server import mcp


def test_mcp_tools_are_cnki_only() -> None:
    tools = {tool.name: tool for tool in mcp._tool_manager.list_tools()}
    assert "search" in tools
    assert "get_record" in tools
    joined = " ".join(
        [
            tools["search"].description or "",
            tools["get_record"].description or "",
            mcp.instructions or "",
        ]
    )
    assert "知网" in joined or "CNKI" in joined
    assert "download" not in tools
    lowered = joined.lower()
    for banned in ("openalex", "pubmed", "bing", "wanfang"):
        assert banned not in lowered
