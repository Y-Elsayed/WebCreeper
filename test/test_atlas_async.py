import unittest

from agents.atlas.atlas import Atlas
from creeper_core.hooks import CrawlHook


class AsyncTrackingHook(CrawlHook):
    def __init__(self):
        self.started = False
        self.finished = False
        self.pages = []

    async def on_start(self, context: dict):
        self.started = True

    async def on_page(self, url: str, html: str, context: dict):
        self.pages.append(url)
        return {"url": url, "kind": "hook"}

    async def on_finish(self, summary: dict, context: dict):
        self.finished = True


class TestAtlasAsync(unittest.IsolatedAsyncioTestCase):
    async def test_crawl_async_bfs_layering_and_results(self):
        atlas = Atlas(
            settings={
                "save_results": False,
                "max_depth": 1,
                "crawl_entire_website": False,
                "max_concurrency": 4,
            }
        )

        async def fake_fetch(url: str):
            if url == "https://example.com":
                return (
                    '<a href="/a">A</a><a href="/b">B</a>',
                    "text/html",
                )
            if url == "https://example.com/a":
                return ('<a href="/c">C</a>', "text/html")
            if url == "https://example.com/b":
                return ('<a href="/d">D</a>', "text/html")
            return ("", "text/html")

        atlas.fetch_async = fake_fetch
        atlas.should_visit = lambda url: True
        atlas.is_allowed_path = lambda url: True
        hook = AsyncTrackingHook()

        async def async_callback(url: str, html: str):
            return {"url": url, "kind": "callback"}

        await atlas.crawl_async("https://example.com", on_page_crawled=async_callback, hooks=[hook])

        # max_depth=1 means start page + one layer children are crawled
        self.assertIn("https://example.com", atlas.graph)
        self.assertIn("https://example.com/a", atlas.graph)
        self.assertIn("https://example.com/b", atlas.graph)
        self.assertNotIn("https://example.com/c", atlas.graph)
        self.assertNotIn("https://example.com/d", atlas.graph)
        self.assertTrue(hook.started)
        self.assertTrue(hook.finished)
        self.assertEqual(set(hook.pages), {"https://example.com", "https://example.com/a", "https://example.com/b"})


if __name__ == "__main__":
    unittest.main()
