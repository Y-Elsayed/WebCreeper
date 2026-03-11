class CrawlHook:
    """
    Base hook contract for crawler agents.
    Subclasses can override any event they need.
    """

    def on_start(self, context: dict):
        pass

    def on_page(self, url: str, html: str, context: dict):
        return None

    def on_link_discovered(self, source_url: str, target_url: str, anchor_text: str, context: dict):
        return None

    def on_page_error(self, url: str, error, context: dict):
        pass

    def on_page_skipped(self, url: str, reason: str, context: dict):
        pass

    def on_finish(self, summary: dict, context: dict):
        pass
