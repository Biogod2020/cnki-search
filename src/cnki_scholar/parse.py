"""Parse 知网空间 listresult / detail HTML into records."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from .models import Record, RecordDetail

CHALLENGE_MARKERS = (
    "安全验证",
    "验证码",
    "blockPuzzle",
    "403 Forbidden",
    "访问过于频繁",
    "异常访问",
)

CNKI_HOSTS = (
    "search.cnki.com.cn",
    "cdmd.cnki.com.cn",
    "www.cnki.com.cn",
    "cnki.net",
    "cnki.com.cn",
)


def is_challenge_html(html: str) -> bool:
    return any(marker in html for marker in CHALLENGE_MARKERS)


def is_cnki_url(url: str) -> bool:
    lowered = url.lower()
    return any(host in lowered for host in CNKI_HOSTS)


def normalize_href(href: str) -> str:
    href = (href or "").strip()
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return urljoin("https://search.cnki.com.cn", href)
    return href


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _title_from_anchor(anchor: Tag) -> str:
    raw = anchor.get_text(" ", strip=True)
    return _clean(re.sub(r"\s*CNKI文献\s*$", "", raw))


def _authors_from_item(item: Tag) -> str | None:
    names: list[str] = []
    source = item.select_one("p.source")
    if source is None:
        return None
    for link in source.select("a[data-key], a.author"):
        name = _clean(link.get_text(" ", strip=True))
        if name and name not in names:
            names.append(name)
    return "；".join(names) if names else None


def _year_from_item(item: Tag) -> str | None:
    source = item.select_one("p.source")
    blob = source.get_text(" ", strip=True) if source else item.get_text(" ", strip=True)
    dated = re.search(r"(19|20)\d{2}-\d{2}-\d{2}", blob)
    if dated:
        return dated.group(0)[:4]
    # Prefer a standalone year token after the author/source line, not years in snippets.
    if source:
        for span in source.find_all("span"):
            token = _clean(span.get_text(" ", strip=True))
            if re.fullmatch(r"(19|20)\d{2}", token):
                return token
    return None


def _kind_from_item(item: Tag) -> str | None:
    blob = item.get_text(" ", strip=True)
    for label in ("博士论文", "硕士论文", "期刊", "会议"):
        if label in blob:
            return label
    return None


def _venue_from_item(item: Tag) -> str | None:
    source = item.select_one("p.source")
    if source is None:
        return None
    parts = [_clean(span.get_text(" ", strip=True)) for span in source.find_all("span")]
    parts = [part for part in parts if part and not re.match(r"(19|20)\d{2}", part)]
    # Drop author-only first span if we already extracted authors separately.
    interesting = [part for part in parts if part not in {"导师:"}]
    if not interesting:
        return _clean(source.get_text(" ", strip=True)) or None
    return " ".join(interesting)


def parse_list_html(html: str) -> list[Record]:
    """Turn a 知网空间 listresult HTML fragment into records."""
    soup = BeautifulSoup(html, "lxml")
    records: list[Record] = []
    seen: set[str] = set()
    for item in soup.select("div.list-item"):
        anchor = item.select_one("p.tit a.left") or item.select_one("p.tit a")
        if anchor is None:
            continue
        href = normalize_href(str(anchor.get("href") or ""))
        title = _title_from_anchor(anchor)
        if not title or not href or href in seen:
            continue
        seen.add(href)
        snippet_node = item.select_one("p.nr")
        records.append(
            Record(
                title=title,
                url=href,
                authors=_authors_from_item(item),
                year=_year_from_item(item),
                venue=_venue_from_item(item),
                kind=_kind_from_item(item),
                snippet=_clean(snippet_node.get_text(" ", strip=True))[:240]
                if snippet_node
                else None,
            )
        )
    return records


def parse_detail_html(html: str, url: str) -> RecordDetail:
    soup = BeautifulSoup(html, "lxml")
    text = _clean(soup.get_text(" ", strip=True))
    fields: dict[str, str] = {}
    for key, pattern in {
        "abstract": r"【摘要】：\s*(.+?)(?:\s*【|$)",
        "institution": r"【学位授予单位】：\s*(.+?)(?:\s*【|$)",
        "degree": r"【学位级别】：\s*(.+?)(?:\s*【|$)",
        "year": r"【学位授予年份】：\s*(.+?)(?:\s*【|$)",
    }.items():
        match = re.search(pattern, text)
        if match:
            fields[key] = match.group(1).strip()
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    if title:
        title = re.split(r"--《", title, maxsplit=1)[0].strip()
    return RecordDetail(
        status="ok",
        url=url,
        title=title,
        abstract=fields.get("abstract"),
        institution=fields.get("institution"),
        degree=fields.get("degree"),
        year=fields.get("year"),
    )
