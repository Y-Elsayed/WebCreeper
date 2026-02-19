import unittest

from agents.atlas.atlas import Atlas
from creeper_core.hooks import CrawlHook


class TrackingHook(CrawlHook):
    def __init__(self):
        self.started = False
        self.finished = False
        self.pages = []

    def on_start(self, context: dict):
        self.started = True

    def on_page(self, url: str, html: str, context: dict):
        self.pages.append(url)
        return {"url": url, "title": "ok"}

    def on_link_discovered(self, source_url: str, target_url: str, anchor_text: str, context: dict):
        # Block one link to verify hook-based filtering.
        if target_url.endswith("/blocked"):
            return False
        return True

    def on_finish(self, summary: dict, context: dict):
        self.finished = True


class TestAtlasHooks(unittest.TestCase):
    def test_hooks_pipeline_without_network(self):
        hook = TrackingHook()
        atlas = Atlas(
            settings={
                "save_results": False,
                "max_depth": 0,
            }
        )

        html = """
        <html><body>
          <a href="/allowed">Allowed</a>
          <a href="/blocked">Blocked</a>
        </body></html>
        """

        # Keep test deterministic and offline.
        atlas.should_visit = lambda url: True
        atlas.is_allowed_path = lambda url: True
        atlas.fetch = lambda url: (html, "text/html")

        atlas.crawl("https://example.com", hooks=[hook])

        self.assertTrue(hook.started, "on_start hook should run")
        self.assertTrue(hook.finished, "on_finish hook should run")
        self.assertEqual(hook.pages, ["https://example.com"])

        graph = atlas.get_graph()
        self.assertIn("https://example.com", graph)
        targets = [link["target"] for link in graph["https://example.com"]]
        self.assertIn("https://example.com/allowed", targets)
        self.assertNotIn("https://example.com/blocked", targets)


if __name__ == "__main__":
    unittest.main()
