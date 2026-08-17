# cnki-search

[![MCP](https://img.shields.io/badge/MCP-stdio-555?labelColor=111)](https://modelcontextprotocol.io/)
[![DSH plugin](https://img.shields.io/badge/DSH-plugin-1a73e8?labelColor=111)](https://github.com/deepseek-ai/deepseek-harness)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776ab?labelColor=111)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-2ea44f?labelColor=111)](LICENSE)

**Anonymous literature metadata for 知网 / CNKI, as a Model Context Protocol server and a DeepSeek Harness plugin.**

`cnki-search` talks to the public **知网空间** HTML surface (`search.cnki.com.cn`), not the official KNS engine. Agents get titles, authors, years, venues, degree labels, and CNKI/CDMD URLs. They do **not** get PDFs, CAJ files, login sessions, or captcha bypass.

中文：这是给 MCP 宿主和 DeepSeek Harness 用的知网题录插件。走知网空间，不走 KNS 滑块，不下全文。

---

## Why this exists

Official KNS (`kns.cnki.net`) redirects anonymous HTTP clients to a slider challenge. Chrome TLS impersonation does not change that. 知网空间 exposes a `POST /search/listresult` form that returns list HTML **without login**. This repo is a thin, testable adapter over that surface.

```text
Claude / Cursor / Codex / DSH agent
        │  MCP stdio
        ▼
   cnki-search  (FastMCP)
        │  curl_cffi  impersonate=chrome
        ▼
search.cnki.com.cn/search/listresult
        │
        ▼
  title · authors · year · kind · CDMD/CJF URL
        │  optional
        ▼
cdmd.cnki.com.cn / www.cnki.com.cn   → abstract, degree, institution
```

DSH does not own this process. It starts the same stdio binary every other MCP host starts:

```text
DSH  →  @deepseek-ai/dsh-mcp-client  →  cnki-search  →  知网空间
```

Discovered tools appear as `mcp__cnki__search` and `mcp__cnki__get_record`.

---

## What it is / is not

| Does | Does not |
|---|---|
| Search 知网空间 metadata | Search KNS, Wanfang, PubMed, OpenAlex, Bing |
| Filter by theme / title / keyword / content / summary | Solve sliders or reuse browser cookies |
| Optional author, advisor, year, kind, sort | Download PDF or CAJ |
| Return `ok` / `blocked` / `error` | Pretend a challenge page is results |

If the HTML challenge appears, the tool returns `status="blocked"`. Strategy, query rewriting, and citation decisions stay in the agent.

---

## Install

Python 3.12+, [`uv`](https://github.com/astral-sh/uv) recommended.

```bash
git clone https://github.com/Biogod2020/cnki-search.git
cd cnki-search
uv sync --extra dev
```

Start the MCP stdio server (it waits on stdin; do not expect a prompt):

```bash
uv run cnki-search
```

The same entry point is installed as `.venv/bin/cnki-search`.

---

## Tools

### `search`

Search 知网空间. `query` may be empty if `author` or `advisor` is set.

| Argument | Values | Meaning |
|---|---|---|
| `query` | string | Search text |
| `field` | `theme` `title` `keyword` `content` `summary` | 主题 / 篇名 / 关键词 / 全文 / 摘要 |
| `page` | 1–50 | Page index |
| `author` | string | 作者 |
| `advisor` | string | 导师 |
| `year` | e.g. `2023` | Year facet |
| `kind` | `all` `journal` `thesis` `phd` `master` | 全部 / 期刊 / 博硕 / 博士 / 硕士 |
| `sort` | `relevance` `date` `downloads` `cites` | 相关度 / 时间 / 下载 / 被引 |

**Worked call** (live against 知网空间):

```json
{
  "query": "SCA3发病年龄的临床预测模型构建与罕见变异关联研究",
  "field": "title"
}
```

**Worked response:**

```json
{
  "status": "ok",
  "provider": "cnki",
  "query": "SCA3发病年龄的临床预测模型构建与罕见变异关联研究",
  "field": "title",
  "returned_count": 1,
  "records": [
    {
      "title": "SCA3发病年龄的临床预测模型构建与罕见变异关联研究",
      "url": "https://cdmd.cnki.com.cn/Article/CDMD-10533-1025564694.htm",
      "authors": "彭林柳",
      "year": "2023",
      "kind": "博士论文"
    }
  ]
}
```

Keyword + dissertation filter:

```json
{
  "query": "空间转录组",
  "field": "title",
  "kind": "thesis",
  "sort": "date"
}
```

Exact titles outperform bag-of-words `keyword` queries. `kind=phd` on a noisy `keyword` page can return zero hits if the first page is all journals — switch to `field=title` or `kind=thesis`.

### `get_record`

Fetch abstract and degree fields from a CNKI / CDMD URL returned by `search`. Not a full-text download.

```json
{ "url": "https://cdmd.cnki.com.cn/Article/CDMD-10533-1025564694.htm" }
```

Returns `title`, `abstract` (prefix), `institution`, `degree`, `year` when the detail page exposes them.

---

## DeepSeek Harness plugin

This repository is a **DSH plugin** in the same shape as [`dsh-bing-search`](https://github.com/Biogod2020/dsh-bing-search): a Python MCP stdio server launched by `@deepseek-ai/dsh-mcp-client`.

1. `uv sync` in this repo.
2. Point `command` at the absolute path of `.venv/bin/cnki-search`.

### Loader config (`cordis.yml`)

Use [`examples/dsh.cordis.yml`](examples/dsh.cordis.yml):

```yaml
- id: mcp-cnki
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: cnki
    transport: stdio
    command: /ABS/PATH/cnki-search/.venv/bin/cnki-search
    args: []
    toolCallTimeoutMs: 30000
    failOnStartupError: true
    reconnect:
      enabled: true
      initialDelayMs: 500
      maxDelayMs: 30000
      maxAttempts: 10
```

Windows: `C:\ABS\PATH\cnki-search\.venv\Scripts\cnki-search.exe`.

### Profile patch (`cordis.patch.yml`)

`$DSH_HOME/profiles/<name>/cordis.patch.yml` is a **patch layer**. A bare `- id: mcp-cnki` entry is treated as an overlay on an existing plugin and is **silently skipped** if that id is not already loaded. You must wrap with `insert`:

```yaml
- insert:
    - id: mcp-cnki
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: cnki
        transport: stdio
        command: /ABS/PATH/cnki-search/.venv/bin/cnki-search
        args: []
        toolCallTimeoutMs: 30000
        failOnStartupError: true
        reconnect:
          enabled: true
          initialDelayMs: 500
          maxDelayMs: 30000
          maxAttempts: 10
```

Ready-to-copy file: [`examples/dsh.patch.yml`](examples/dsh.patch.yml).

After discovery the model sees:

```text
mcp__cnki__search
mcp__cnki__get_record
```

Pair with a web-search plugin (`mcp__web__search`) when you need English or non-CNKI sources. Do not fold both into one `search` tool.

---

## Other MCP hosts

```json
{
  "mcpServers": {
    "cnki": {
      "command": "uv",
      "args": ["--directory", "/ABS/PATH/cnki-search", "run", "cnki-search"]
    }
  }
}
```

Works with any host that speaks MCP stdio (Claude Desktop / Claude Code, Cursor, Codex, Continue, …). The server writes protocol on stdout only.

---

## Library use

```python
from cnki_scholar import search_cnki, get_record

hits = search_cnki("影像组学 阿尔茨海默病", field="title", kind="thesis")
detail = get_record(hits.records[0].url)
```

HTTP I/O, HTML parse, and the MCP adapter are separate modules so parse is tested on saved 知网空间 HTML without mocking a second implementation.

---

## Tests

```bash
uv run pytest -m "not live"
RUN_LIVE_CNKI=1 uv run pytest -m live -s
```

Offline tests drive the shipped parser on captured listresult HTML (including the 彭林柳 / SCA3 dissertation record). Live tests hit 知网空间 and are skipped unless `RUN_LIVE_CNKI=1`.

---

## Status model

| `status` | Meaning |
|---|---|
| `ok` | Parsed one or more records, or a valid empty page |
| `blocked` | Challenge / 403 — do not treat as zero results |
| `error` | Transport, HTTP 4xx/5xx, or bad arguments |

---

## Limits

- Coverage is **知网空间**, not the full KNS catalog. Very new theses can be missing.
- `keyword` is a bag-of-words facet. Prefer `title` for a known dissertation name.
- Journal `Type=1` is applied server-side. Dissertation `kind` is applied after parse because other type codes on this surface are unreliable.
- Markup can change without notice. That is an adapter break, not a captcha problem.
- Respect CNKI terms and your institution’s rules. This client is for metadata discovery, not bulk full-text harvest.

---

## License

MIT. CNKI content remains with CNKI and the original authors.
