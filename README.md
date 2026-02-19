# WebCreeper: Crawl. Extract. Discover.

WebCreeper is an open-source crawling framework built around **agents**.
Each agent is a crawler specialized for a specific task, and all agents share core crawling primitives from `creeper_core`.

## Agent Model

- Agents are modular crawler units with clear responsibilities.
- Each agent can expose its own settings and extraction behavior.
- Shared infrastructure (robots handling, retries, rate limits, hooks, policies) lives in the core.

This makes it easy to:
- Start simple with one agent.
- Add new agents without rewriting crawl infrastructure.
- Compose custom extraction logic through callbacks and hooks.

## Installed Agents

- `Atlas`: website crawler that builds a link graph and supports custom extraction callbacks/hooks.

See full agent docs:
- `docs/agents/README.md`

## Quick Start

Install from GitHub:

```bash
pip install git+https://github.com/Y-Elsayed/WebCreeper.git
```

Minimal crawl:

```python
from agents.atlas.atlas import Atlas

atlas = Atlas(settings={"max_depth": 1})
atlas.crawl("https://example.com")

graph = atlas.get_graph()
print(f"Crawled pages: {len(graph)}")
```

Extract page content with a callback:

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

## Documentation

- Agent docs index: `docs/agents/README.md`
- Atlas full guide: `docs/agents/atlas.md`

## License

MIT. See `LICENSE`.
