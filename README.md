# WebCreeper: Crawl. Extract. Discover.

**WebCreeper** is an open-source framework designed to build customizable web crawlers. The project focuses on creating a range of "crawler agents," each specialized with unique abilities for specific tasks. Whether it's scraping content, monitoring trends, tracking prices, analyzing sentiment, and more, **WebCreeper** allows you to leverage these agents to perform targeted web crawling with precision.

## The Idea

At the heart of **WebCreeper** is the concept of "crawler agents", which are specialized crawlers each with a distinct set of capabilities. These agents are modular and designed to carry out specific tasks efficiently. You can mix and match these agents based on your needs, or even create new ones to tackle new challenges as the project evolves.

Each crawler agent is designed to perform its designated task, helping users gather valuable insights from the web in a streamlined, efficient manner.

## Current Agent

- **Atlas**: Crawls websites and builds a directed graph of page links.

## Quick Start

Install from GitHub:

```bash
pip install git+https://github.com/Y-Elsayed/WebCreeper.git
```

Minimal usage:

```python
from agents.atlas.atlas import Atlas

atlas = Atlas(
    settings={
        "allowed_domains": ["example.com"],
        "max_depth": 1,
    }
)

atlas.crawl("https://example.com")
graph = atlas.get_graph()
print(f"Crawled pages: {len(graph)}")
```

## Atlas Recipes

Depth-limited crawl:

```python
atlas = Atlas(settings={
    "allowed_domains": ["example.com"],
    "max_depth": 2,
    "crawl_entire_website": False,
})
atlas.crawl("https://example.com")
```

Full-site crawl:

```python
atlas = Atlas(settings={
    "allowed_domains": ["example.com"],
    "crawl_entire_website": True,
})
atlas.crawl("https://example.com")
```

Structured extraction callback:

```python
from bs4 import BeautifulSoup

def extract_title_and_text(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    text = soup.get_text(" ", strip=True)
    return {
        "url": url,
        "title": title,
        "text_length": len(text),
    }

atlas = Atlas(settings={
    "allowed_domains": ["example.com"],
    "results_filename": "results.jsonl",
    "save_results": True,
})
atlas.crawl("https://example.com", on_page_crawled=extract_title_and_text)
```

## Callback Contract (Atlas)

`on_page_crawled` supports:
- `fn(url, html)`
- `fn({"url": url, "html": html})`

Return value:
- If the callback returns a `dict` containing at least `"url"`, Atlas can save it to JSONL when `save_results=True`.
- If callback returns `None` (or non-dict), Atlas skips result persistence for that page.
