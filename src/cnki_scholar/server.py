from __future__ import annotations

import warnings

warnings.filterwarnings(
    "ignore",
    message=r"Field 'lifespan' has an incomplete definition",
    category=UserWarning,
)

from mcp.server.fastmcp import FastMCP

from .client import SearchField, SearchKind, SearchSort
from .models import RecordDetail, SearchResponse
from .service import get_record, search_cnki

mcp = FastMCP(
    name="cnki-search",
    instructions=(
        "Search 知网 / CNKI literature metadata on the public 知网空间 surface. "
        "Use search with field=theme|title|keyword|content|summary, optional author, advisor, year, and kind. "
        "Use get_record to read an abstract and degree fields from a CNKI detail page. "
        "This server does not download PDFs or search non-CNKI providers."
    ),
    json_response=True,
)


@mcp.tool(name="search", title="Search CNKI / 知网", structured_output=True)
async def search_tool(
    query: str = "",
    field: SearchField = "theme",
    page: int = 1,
    author: str | None = None,
    advisor: str | None = None,
    year: str | None = None,
    kind: SearchKind = "all",
    sort: SearchSort = "relevance",
) -> SearchResponse:
    """Search 知网空间 metadata. query may be empty if author or advisor is set.

    Args:
        query: Search text. Exact title works best with field=title.
        field: theme (主题), title (篇名), keyword (关键词), content (全文), summary (摘要).
        page: Result page, starting at 1.
        author: Author name (作者).
        advisor: Thesis advisor (导师).
        year: Publication or degree year, e.g. 2023.
        kind: all, journal (期刊), thesis (博硕), phd (博士), master (硕士).
        sort: relevance, date, downloads, cites.
    """
    return search_cnki(
        query,
        field=field,
        page=page,
        author=author,
        advisor=advisor,
        year=year,
        kind=kind,
        sort=sort,
    )


@mcp.tool(name="get_record", title="Get CNKI record metadata", structured_output=True)
async def get_record_tool(url: str) -> RecordDetail:
    """Fetch metadata from a 知网 / CDMD / cnki.com.cn record page. Not a PDF download.

    Args:
        url: A CNKI Space or CDMD detail URL returned by search.
    """
    return get_record(url)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
