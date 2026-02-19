# Atlas

## Overview
Atlas is a powerful agent designed to crawl the web or a specific website and construct a graph representation of its structure. In this graph, webpages are represented as nodes, and the links between these webpages are represented as edges. 

## Key Features
- **Web Graph Construction**: Crawl a website and build a graph that visualizes its structure.
- **Scalability**: Capable of handling websites of varying sizes and complexities.
- **Customizable Settings**: Configure settings such as crawling depth, allowed domains, and user-agent.

## Future Enhancements
- **Graph Visualization**: Plan to include tools to visualize the constructed graphs for easier understanding and analysis.
- **Querying Routes**: Enable queries to determine specific routes to reach sections within a website.
- **Structural Insights**: Allow users to ask questions about the website's structure and receive meaningful insights.

## Usage

To use the **Atlas** agent, follow these steps.

### 1. Install the necessary dependencies
Core install:

```bash
pip install git+https://github.com/Y-Elsayed/WebCreeper.git
```

### 2. Import the Atlas agent
Import the Atlas agent into your script from the appropriate path.
```python
from agents.atlas.atlas import Atlas
```
### 3. Define the settings
Create a settings dictionary to configure the Atlas agent. This dictionary can include parameters like the allowed domains, maximum crawl depth, storage path, and user agent. For more settings check the ```creeper_core/base_agent.py```
```python
settings = {
    'allowed_domains': ['example.com'],  # Optional: if omitted, Atlas derives from start_url
    'max_depth': 2,  # Crawl up to depth 2
    'storage_path': './data',  # Path where the graph will be saved
    'user_agent': 'WebCreeper'  # Custom User-Agent (default is AtlasCrawler)
}
```

### 4. Create an instance of the Atlas agent
Instantiate the Atlas agent with the settings you defined earlier.
```python
atlas = Atlas(settings=settings)
```
### 5. Start the crawling process
Provide a starting URL (e.g., the homepage of the website) and call the crawl() method to begin crawling.
```python
start_url = "https://example.com"
atlas.crawl(start_url)
```
### 6. Access the crawled graph data
Once the crawl is complete, you can retrieve the constructed graph, which represents the website structure as a dictionary of nodes and edges.
```python
graph = atlas.get_graph() #You'll also find it saved in the data directory
```

## Common Recipes

### Full-site crawl mode

```python
atlas = Atlas(settings={
    "allowed_domains": ["example.com"],
    "crawl_entire_website": True,
})
atlas.crawl("https://example.com")
```

### Seeded crawl mode

```python
atlas = Atlas(settings={
    "allowed_domains": ["example.com"],
    "crawl_entire_website": False,
    "seed_urls": [
        "https://example.com/docs",
        "https://example.com/blog",
    ],
})
atlas.crawl("https://example.com")
```

### Save custom extraction results

```python
from bs4 import BeautifulSoup

def on_page(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    return {"url": url, "title": title}

atlas = Atlas(settings={
    "allowed_domains": ["example.com"],
    "save_results": True,
    "results_filename": "results.jsonl",
})
atlas.crawl("https://example.com", on_page_crawled=on_page)
```

### Crawl and get page content immediately (in memory)

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

### Read persisted extraction output (JSONL)

```python
import json

with open("./data/results.jsonl", "r", encoding="utf-8") as f:
    results = [json.loads(line) for line in f]
print(f"Saved rows: {len(results)}")
```

## Callback Contract

`on_page_crawled` supports either signature:
- `fn(url, html)`
- `fn({"url": url, "html": html})`

If callback returns a `dict` with at least `"url"`, Atlas can persist it in JSONL when `save_results=True`.

## Hooks Pipeline (New)

Atlas also accepts `hooks=[...]` in `crawl()` for reusable processors:

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

## Contribution
Contributions to enhance Atlas or implement planned features are welcome.
