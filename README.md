<p align="center">
  <img src="docs/assets/logo.png" width="160" alt="cnki-search" />
</p>

<h1 align="center">cnki-search</h1>

<p align="center">
  从<a href="https://search.cnki.com.cn/">知网空间</a>检索中文文献题录，通过 MCP 提供给各类 Agent。<br/>
  返回题名、作者、年份、文献类型和详情页链接；不提供全文下载。
</p>

<p align="center">
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-stdio-555?labelColor=111" alt="MCP" /></a>
  <a href="https://github.com/deepseek-ai/deepseek-harness"><img src="https://img.shields.io/badge/DSH-plugin-1a73e8?labelColor=111" alt="DSH plugin" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12%2B-3776ab?labelColor=111" alt="Python 3.12+" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2ea44f?labelColor=111" alt="MIT" /></a>
</p>

数据来自 `search.cnki.com.cn` 的公开检索接口，无需知网账号。检索范围是知网空间，不是 KNS 全部馆藏。

## 功能

| 工具 | 作用 |
|---|---|
| `search` | 按主题、篇名、关键词、全文或摘要检索；可限定作者、导师、年份、文献类型 |
| `get_record` | 根据检索得到的知网 / CDMD 链接读取摘要与学位信息 |

`search` 参数：

| 参数 | 取值 | 说明 |
|---|---|---|
| `query` | 字符串 | 检索词。仅查作者或导师时可为空 |
| `field` | `theme` / `title` / `keyword` / `content` / `summary` | 主题 / 篇名 / 关键词 / 全文 / 摘要 |
| `page` | 1–50 | 页码 |
| `author` | 字符串 | 作者 |
| `advisor` | 字符串 | 导师 |
| `year` | 如 `2023` | 年份 |
| `kind` | `all` / `journal` / `thesis` / `phd` / `master` | 全部 / 期刊 / 博硕 / 博士 / 硕士 |
| `sort` | `relevance` / `date` / `downloads` / `cites` | 相关度 / 发表时间 / 下载 / 被引 |

已知题名时用 `field=title`。`keyword` 按词拆分，容易混入不相关结果。

返回 `status`：`ok` 为正常；`blocked` 为接口拒绝或校验页；`error` 为参数或网络错误。不要把 `blocked` 当成零结果。

## 安装

需要本机已安装 [uv](https://github.com/astral-sh/uv)（Python 3.12+）。不必先 clone。

Agent 或本机直接启动：

```bash
uvx --from git+https://github.com/Biogod2020/cnki-search.git cnki-search
```

进程在 stdio 上等待 MCP 宿主，没有交互提示。

开发与测试：

```bash
git clone https://github.com/Biogod2020/cnki-search.git
cd cnki-search
uv sync --extra dev
uv run pytest -m "not live"
```

联网回归：`RUN_LIVE_CNKI=1 uv run pytest -m live -s`

## 接入 MCP

把下面配置交给 Agent，或写入宿主的 MCP 配置。宿主会自行通过 `uvx` 拉取并运行，无需预先克隆。

```json
{
  "mcpServers": {
    "cnki": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Biogod2020/cnki-search.git",
        "cnki-search"
      ]
    }
  }
}
```

适用于 Claude、Cursor、Codex 及其他 MCP stdio 宿主。工具名：`search`、`get_record`。

## 接入 DeepSeek Harness

与 [dsh-bing-search](https://github.com/Biogod2020/dsh-bing-search) 相同：由 `@deepseek-ai/dsh-mcp-client` 拉起本仓库的 stdio 服务。发现后的工具名为：

```text
mcp__cnki__search
mcp__cnki__get_record
```

写入 `cordis.yml` 可用 [`examples/dsh.cordis.yml`](examples/dsh.cordis.yml)。写入 `$DSH_HOME/profiles/<name>/cordis.patch.yml` 时必须用 `insert`，否则 id 不存在会被静默跳过。见 [`examples/dsh.patch.yml`](examples/dsh.patch.yml)：

```yaml
- insert:
    - id: mcp-cnki
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: cnki
        transport: stdio
        command: uvx
        args:
          - --from
          - git+https://github.com/Biogod2020/cnki-search.git
          - cnki-search
        toolCallTimeoutMs: 30000
        failOnStartupError: true
        reconnect:
          enabled: true
          initialDelayMs: 500
          maxDelayMs: 30000
          maxAttempts: 10
```

## 调用示例

```json
{
  "query": "SCA3发病年龄的临床预测模型构建与罕见变异关联研究",
  "field": "title"
}
```

```json
{
  "status": "ok",
  "provider": "cnki",
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

```json
{
  "query": "空间转录组",
  "field": "title",
  "kind": "thesis",
  "sort": "date"
}
```

Python：

```python
from cnki_scholar import search_cnki, get_record

hits = search_cnki("影像组学 阿尔茨海默病", field="title", kind="thesis")
detail = get_record(hits.records[0].url)
```

## 说明

- 覆盖范围为知网空间，新入库学位论文可能检索不到。
- 期刊可用接口的文献类型参数；博硕类型在解析后过滤。
- 列表页结构若变更，解析会失效。
- 文献版权归知网及原作者。请遵守知网使用条款与所在机构规定。

## 许可

MIT
