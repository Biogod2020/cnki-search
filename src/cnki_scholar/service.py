"""CNKI Space search and record lookup. Metadata only."""

from __future__ import annotations

import time

from .client import (
    SearchField,
    SearchKind,
    SearchSort,
    fetch_detail,
    fetch_listresult,
)
from .models import Record, RecordDetail, SearchResponse
from .parse import is_challenge_html, is_cnki_url, parse_detail_html, parse_list_html

KIND_LABELS = {
    "journal": {"期刊"},
    "phd": {"博士论文"},
    "master": {"硕士论文"},
    "thesis": {"博士论文", "硕士论文"},
}


def _filter_kind(records: list[Record], kind: SearchKind) -> list[Record]:
    labels = KIND_LABELS.get(kind)
    if not labels:
        return records
    return [item for item in records if item.kind in labels]


def search_cnki(
    query: str,
    *,
    field: SearchField = "theme",
    page: int = 1,
    author: str | None = None,
    advisor: str | None = None,
    year: str | None = None,
    kind: SearchKind = "all",
    sort: SearchSort = "relevance",
) -> SearchResponse:
    query = " ".join(query.split())
    author = " ".join(author.split()) if author else None
    advisor = " ".join(advisor.split()) if advisor else None
    year = year.strip() if year else None
    if not query and not author and not advisor:
        return SearchResponse(status="error", query="", error="empty_query")
    page = min(max(int(page), 1), 50)
    started = time.perf_counter()
    try:
        http = fetch_listresult(
            query,
            field=field,
            page=page,
            author=author,
            advisor=advisor,
            year=year,
            kind=kind,
            sort=sort,
        )
    except ValueError as exc:
        return SearchResponse(status="error", query=query, page=page, error=str(exc))
    except Exception as exc:  # noqa: BLE001 - surface transport to the MCP caller
        return SearchResponse(
            status="error",
            query=query,
            field=field,
            page=page,
            error=f"{type(exc).__name__}: {exc}",
            elapsed_ms=round((time.perf_counter() - started) * 1000),
        )

    elapsed = round((time.perf_counter() - started) * 1000)
    if http.status_code == 403 or is_challenge_html(http.text):
        return SearchResponse(
            status="blocked",
            query=query,
            field=field,
            page=page,
            elapsed_ms=elapsed,
            error="cnki_space_challenge",
        )
    if http.status_code >= 400:
        return SearchResponse(
            status="error",
            query=query,
            field=field,
            page=page,
            elapsed_ms=elapsed,
            error=f"http_{http.status_code}",
        )

    records = _filter_kind(parse_list_html(http.text), kind)
    return SearchResponse(
        status="ok",
        query=query,
        field=field,
        page=page,
        returned_count=len(records),
        records=records,
        elapsed_ms=elapsed,
    )


def get_record(url: str) -> RecordDetail:
    url = url.strip()
    if not url:
        return RecordDetail(status="error", url="", error="empty_url")
    if not is_cnki_url(url):
        return RecordDetail(
            status="error",
            url=url,
            error="url_must_be_cnki",
        )
    started = time.perf_counter()
    try:
        http = fetch_detail(url)
    except Exception as exc:  # noqa: BLE001
        return RecordDetail(
            status="error",
            url=url,
            error=f"{type(exc).__name__}: {exc}",
        )
    _ = started
    if http.status_code == 403 or is_challenge_html(http.text):
        return RecordDetail(status="blocked", url=http.url, error="cnki_space_challenge")
    if http.status_code >= 400:
        return RecordDetail(status="error", url=http.url, error=f"http_{http.status_code}")
    return parse_detail_html(http.text, http.url)
