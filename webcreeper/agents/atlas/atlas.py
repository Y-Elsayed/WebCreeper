import hashlib
import inspect
import os
import re
import asyncio
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from webcreeper.creeper_core.base_agent import BaseAgent
from webcreeper.creeper_core.storage import save_json, save_jsonl_line


class Atlas(BaseAgent):
    DEFAULT_SETTINGS = {
        "base_url": None,
        "timeout": 10,
        "user_agent": "AtlasCrawler",
        "max_depth": 3,
        "allowed_domains": [],
        "allowed_paths": [],
        "allow_url_patterns": [],  # regex patterns (optional allow-list)
        "blocked_paths": [],
        "storage_path": "./data",
        "crawl_entire_website": False,
        "save_results": True,
        "results_filename": "results.jsonl",
        "heuristic_skip_long_urls": True,
        "heuristic_skip_state_param": True,
        "deduplicate_content": True,
        "allow_subdomains": False,  # exact host by default
        "seed_urls": [],  # crawl only these pages when not full-site
        "max_concurrency": 10,
        "batch_delay": 0.0,
    }

    def __init__(self, settings: dict = {}):
        self.settings = {**self.DEFAULT_SETTINGS, **settings}
        self.graph = {}
        self.max_depth = self.settings["max_depth"]
        self.crawl_entire_website = self.settings["crawl_entire_website"]

        self.results_path = os.path.join(self.settings["storage_path"], self.settings["results_filename"])
        os.makedirs(self.settings["storage_path"], exist_ok=True)

        # Track seen content hashes
        self.content_hashes = set()

        # Visited set / frontier de-dup (BaseAgent may have it; ensure present)
        if not hasattr(self, "visited"):
            self.visited = set()

        super().__init__(self.settings)

    # --------------------------- helpers ---------------------------

    def _host_matches(self, host: str, allowed: str) -> bool:
        """Exact or subdomain match: foo.bar.com matches bar.com."""
        host = self._norm_host(host)
        allowed = self._norm_host(allowed)
        if not host or not allowed:
            return False
        return host == allowed or host.endswith("." + allowed)

    def _is_http(self, url: str) -> bool:
        scheme = urlparse(url).scheme.lower()
        return scheme in ("http", "https")

    def _should_skip_heuristics(self, url: str) -> bool:
        if self.settings.get("heuristic_skip_long_urls", True) and len(url) > 2000:
            return True
        if self.settings.get("heuristic_skip_state_param", True):
            if re.search(r"[?&](state|session|token|sid|phpsessid)=", url, re.I):
                return True
        return False

    def _effective_allowed_domains(self, start_url: str) -> list:
        """
        Build an expanded allow-list:
          - If allowed_domains is empty, derive from start_url.
          - Always include both apex and 'www.' variant for each entry.
        """
        given = self.settings.get("allowed_domains") or []
        out = set()

        if not given:
            start_host = self._norm_host(urlparse(start_url).netloc)
            if start_host:
                given = [start_host]

        for d in given:
            base = self._norm_host(d)
            if not base:
                continue
            out.add(base)
            out.add(f"www.{base}")

        return sorted(out)

    def _is_duplicate_content(self, html: str, url: str) -> bool:
        """Check if content is duplicate based on hash of extracted text."""
        if not self.settings.get("deduplicate_content", True):
            return False

        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        if not text:
            return False

        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        if h in self.content_hashes:
            self.logger.info(f"Skipping {url} (duplicate content hash)")
            return True

        self.content_hashes.add(h)
        return False

    # ------------------------ policy checks ------------------------

    def should_visit(self, url: str) -> bool:
        """
        Normalize domain checks, optionally allow subdomains, skip bad schemes,
        and apply simple heuristics. Function name/signature preserved.
        """
        if not url:
            return False

        url = self._strip_fragment(url)

        if not self._is_http(url):
            return False

        if self._should_skip_heuristics(url):
            return False

        host = urlparse(url).netloc
        allowed_domains = self._effective_allowed_domains(self.settings.get("base_url") or url)
        allow_sub = self.settings.get("allow_subdomains", False)
        norm_host = self._norm_host(host)
        norms = [self._norm_host(d) for d in allowed_domains]
        ok = True

        # If there is an allow-list, enforce it
        if allowed_domains:
            if allow_sub:
                ok = any(norm_host == d or norm_host.endswith("." + d) for d in norms)
            else:
                ok = norm_host in norms

        if not ok:
            self.logger.info(
                f"Disallowed {url} -> Disallowed domain "
                f"(host={norm_host}, allowed={norms}, allow_subdomains={allow_sub})"
            )
            return False

        # Respect robots.txt if enabled
        if not self.is_allowed_by_robots(url):
            self.logger.info(f"Disallowed {url} -> Blocked by robots.txt")
            return False

        # Respect allow/block URL patterns if provided
        if not self.is_allowed_by_patterns(url):
            self.logger.info(f"Disallowed {url} -> Blocked by allow/block patterns")
            return False

        return True

    def is_allowed_path(self, url: str) -> bool:
        path = urlparse(url).path or "/"
        allowed_paths = self.settings.get("allowed_paths", []) or []
        blocked_paths = self.settings.get("blocked_paths", []) or []
        allow_url_patterns = self.settings.get("allow_url_patterns", []) or []

        # Path allow-list (prefix)
        if allowed_paths and not any(path.startswith(p) for p in allowed_paths):
            return False

        # Regex allow-list (any must match)
        if allow_url_patterns:
            if not any(re.search(p, url) for p in allow_url_patterns):
                return False

        # Block-list (prefix)
        if any(path.startswith(p) for p in blocked_paths):
            return False

        return True

    # ------------------------- main crawling -----------------------

    def crawl(self, start_url: str, on_page_crawled=None, on_all_done=None, hooks=None):
        asyncio.run(self.crawl_async(start_url, on_page_crawled=on_page_crawled, on_all_done=on_all_done, hooks=hooks))

    async def crawl_async(self, start_url: str, on_page_crawled=None, on_all_done=None, hooks=None):
        self.on_page_crawled = on_page_crawled
        self.on_all_done = on_all_done
        self.hooks = self._normalize_hooks(hooks)
        self.settings["base_url"] = start_url
        await self._run_hook_event_async("on_start", self._hook_context(start_url=start_url))

        if self.settings.get("save_results", True) and os.path.exists(self.results_path):
            open(self.results_path, "w").close()

        self.visited = set()
        if hasattr(self, "content_hashes"):
            self.content_hashes.clear()

        raw_seeds = self.settings.get("seed_urls") or []
        seeds = [u.strip() for u in raw_seeds if isinstance(u, str) and u.strip()]
        if not seeds:
            seeds = [start_url]

        if self.crawl_entire_website or self.max_depth is None or self.max_depth < 0:
            depth_limit = None
        else:
            depth_limit = self.max_depth
        await self._crawl_bfs_async(seeds, depth_limit=depth_limit)

        if self.on_all_done:
            try:
                out = self.on_all_done(self.graph)
                if inspect.isawaitable(out):
                    await out
            except Exception as e:
                self.logger.warning(f"on_all_done callback raised: {e}")

        summary = {
            "crawled_pages": len(self.graph),
            "visited_urls": len(self.visited),
            "results_path": self.results_path if self.settings.get("save_results", True) else None,
        }
        await self._run_hook_event_async("on_finish", summary, self._hook_context(start_url=start_url))

    async def _crawl_bfs_async(self, seed_urls: list[str], depth_limit=None):
        frontier = []
        seen_frontier = set()
        for u in seed_urls:
            u = self._strip_fragment(u)
            if not u or u in seen_frontier:
                continue
            seen_frontier.add(u)
            frontier.append(u)

        depth = 0
        max_concurrency = max(1, int(self.settings.get("max_concurrency", 10)))
        sem = asyncio.Semaphore(max_concurrency)
        batch_delay = float(self.settings.get("batch_delay", 0.0))

        while frontier:
            if depth_limit is not None and depth > depth_limit:
                break

            tasks = [self._process_url_async(url, depth, sem) for url in frontier]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            next_frontier = []
            for item in results:
                if isinstance(item, Exception):
                    self.logger.warning(f"Async crawl task failed: {item}")
                    continue
                for target in item:
                    target = self._strip_fragment(target)
                    if target not in seen_frontier:
                        seen_frontier.add(target)
                        next_frontier.append(target)

            if batch_delay > 0 and next_frontier:
                await asyncio.sleep(batch_delay)

            frontier = next_frontier
            depth += 1

    async def _process_url_async(self, url: str, depth: int, sem: asyncio.Semaphore) -> list[str]:
        async with sem:
            if url in self.visited:
                return []

            url = self._strip_fragment(url)
            page_ctx = self._hook_context(url=url, depth=depth)

            if not self.should_visit(url):
                await self._run_hook_event_async("on_page_skipped", url, "blocked_by_policy", page_ctx)
                return []
            if not self.is_allowed_path(url):
                await self._run_hook_event_async("on_page_skipped", url, "blocked_by_path_policy", page_ctx)
                return []

            self.visited.add(url)
            self.logger.info(f"Crawling page async: {url} (Depth: {depth})")

            fetched = await self.fetch_async(url)
            if not fetched:
                self.logger.info(f"Skipping {url} - failed to fetch.")
                await self._run_hook_event_async("on_page_error", url, "fetch_failed", page_ctx)
                return []
            content, content_type = fetched

            if not content or "text/html" not in (content_type or ""):
                self.logger.info(f"Skipping non-HTML content: {url} [{content_type}]")
                await self._run_hook_event_async("on_page_skipped", url, f"non_html:{content_type}", page_ctx)
                return []

            if self._is_duplicate_content(content, url):
                await self._run_hook_event_async("on_page_skipped", url, "duplicate_content", page_ctx)
                return []

            links = await self.extract_links_async(content, url)

            for result in await self._collect_page_results_async(url, content, page_ctx):
                self._save_result(result)

            self.graph[url] = links
            return [link["target"] for link in links]

    def extract_links(self, page_content: str, base_url: str, page_id=None) -> list:
        soup = BeautifulSoup(page_content, "html.parser")
        links = []
        seen = set()

        i = 0
        for anchor in soup.find_all("a", href=True):
            full_url = urljoin(base_url, anchor["href"])
            full_url = self._strip_fragment(full_url)
            if not self._is_http(full_url):
                continue
            if full_url in seen:
                continue
            seen.add(full_url)

            anchor_text = anchor.get_text(strip=True)
            if not self._allow_discovered_link(base_url, full_url, anchor_text):
                continue

            links.append(
                {
                    "target": full_url,
                    "anchor_text": anchor_text,
                    "source_chunk": f"{page_id}_chunk_{i}" if page_id is not None else f"chunk_{i}",
                }
            )
            i += 1

        return links

    async def extract_links_async(self, page_content: str, base_url: str, page_id=None) -> list:
        soup = BeautifulSoup(page_content, "html.parser")
        links = []
        seen = set()

        i = 0
        for anchor in soup.find_all("a", href=True):
            full_url = urljoin(base_url, anchor["href"])
            full_url = self._strip_fragment(full_url)
            if not self._is_http(full_url):
                continue
            if full_url in seen:
                continue
            seen.add(full_url)

            anchor_text = anchor.get_text(strip=True)
            if not await self._allow_discovered_link_async(base_url, full_url, anchor_text):
                continue

            links.append(
                {
                    "target": full_url,
                    "anchor_text": anchor_text,
                    "source_chunk": f"{page_id}_chunk_{i}" if page_id is not None else f"chunk_{i}",
                }
            )
            i += 1

        return links

    def _save_result(self, result: dict):
        if not isinstance(result, dict):
            return
        if "url" not in result:
            self.logger.debug(f"Skipping result due to missing fields: {result}")
            return
        if self.settings["save_results"]:
            save_jsonl_line(self.results_path, result)

    def process_data(self, data, file_path=None):
        if file_path is None:
            file_path = os.path.join(self.settings["storage_path"], "graph.json")
        save_json(file_path, data)

    def get_graph(self):
        return self.graph
