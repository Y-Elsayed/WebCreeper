# Atlas Agent

## Overview

Atlas crawls websites and builds a directed link graph where:
- Nodes = crawled pages
- Edges = discovered links between pages

It also supports extracting structured data per page via callbacks or reusable hooks.

## What Atlas Does Well

- Depth-limited crawling
- Full-site crawling
- Seeded crawling from specific URLs
- Domain/path/pattern filtering
- Robots.txt-aware crawling
- Structured extraction via callback or hooks

## Install

```bash
pip install git+https://github.com/Y-Elsayed/WebCreeper.git
```

## Minimal Example

```python
from agents.atlas.atlas import Atlas

atlas = Atlas(settings={"max_depth": 1})
atlas.crawl("https://example.com")

graph = atlas.get_graph()
print(f"Crawled pages: {len(graph)}")
```

## Common Settings

```python
settings = {
    "max_depth": 2,
    "crawl_entire_website": False,
    "allowed_domains": ["example.com"],  # optional: auto-derived from start_url when omitted
    "allowed_paths": [],
    "blocked_paths": [],
    "allow_url_patterns": [],
    "save_results": True,
    "results_filename": "results.jsonl",
    "storage_path": "./data",
}
```

## Crawl Modes

Depth-limited crawl:

```python
atlas = Atlas(settings={"max_depth": 2, "crawl_entire_website": False})
atlas.crawl("https://example.com")
```

Full-site crawl:

```python
atlas = Atlas(settings={"crawl_entire_website": True})
atlas.crawl("https://example.com")
```

Seeded crawl:

```python
atlas = Atlas(settings={
    "seed_urls": [
        "https://example.com/docs",
        "https://example.com/blog",
    ],
    "max_depth": 1,
})
atlas.crawl("https://example.com")
```

## Extract Content with Callback

```python
from bs4 import BeautifulSoup

rows = []

def collect(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    row = {"url": url, "content": text[:1000]}
    rows.append(row)
    return row

atlas = Atlas(settings={"save_results": False, "max_depth": 1})
atlas.crawl("https://example.com", on_page_crawled=collect)
print(rows[:2])
```

## Callback Contract

`on_page_crawled` supports either signature:
- `fn(url, html)`
- `fn({"url": url, "html": html})`

Return behavior:
- If callback returns a `dict` with at least `"url"`, Atlas can persist it when `save_results=True`.
- If callback returns `None` (or non-dict), Atlas skips persistence for that page.

## Hooks Pipeline

Atlas accepts `hooks=[...]` in `crawl()` for reusable processing.

```python
from creeper_core.hooks import CrawlHook

class TitleHook(CrawlHook):
    def on_page(self, url, html, context):
        start = html.find("<title>")
        end = html.find("</title>")
        title = html[start + 7 : end].strip() if start != -1 and end != -1 else ""
        return {"url": url, "title": title}

atlas = Atlas(settings={"save_results": True})
atlas.crawl("https://example.com", hooks=[TitleHook()])
```

Supported hook lifecycle methods:
- `on_start(context)`
- `on_page(url, html, context)`
- `on_link_discovered(source_url, target_url, anchor_text, context)`
- `on_page_error(url, error, context)`
- `on_page_skipped(url, reason, context)`
- `on_finish(summary, context)`

## Outputs

- Graph: `atlas.get_graph()` or `atlas.process_data(graph, file_path)`
- Extracted JSONL (if enabled): `./data/results.jsonl` by default
