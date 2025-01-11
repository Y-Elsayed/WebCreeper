from urllib.parse import urljoin
from bs4 import BeautifulSoup
from creeper_core.base_agent import BaseAgent
from json import dump
import os
class Atlas(BaseAgent):
    DEFAULT_SETTINGS = {
        "base_url": None,
        "timeout": 10,
        "user_agent": "AtlasCrawler",
        "max_depth": 3,
        "allowed_domains": [],
        "storage_path": "./data",
        "crawl_entire_website": False,
    }

    def __init__(self, settings: dict = {}):
        self.settings = {**self.DEFAULT_SETTINGS, **settings} # Merge default and passed settings

        # Initialize specific attributes
        self.graph = {}  # Dictionary to store the graph (key = page, value = list of linked pages)
        self.visited = set()  # Set to track visited pages
        self.max_depth = self.settings['max_depth']  # Use default or user-provided max_depth
        self.crawl_entire_website = self.settings['crawl_entire_website']  # Full site crawl flag

        # Call the parent constructor if any parent logic is needed
        super().__init__(self.settings)


    def crawl(self, start_url: str): # May add semantic crawling in the future
        """
        Start crawling from the given start URL.
        """
        if self.crawl_entire_website:
            self.logger.info("Crawling the entire website.")
            self._crawl_entire_site(start_url)
        else:
            self.logger.info(f"Crawling with depth limit: {self.max_depth}")
            self._crawl_page(start_url)

    def _crawl_page(self, url: str, depth: int = 0):
        """
        Recursively crawl a page and extract links.
        """
        if depth > self.max_depth:
            return  # Stop if the maximum depth is exceeded

        if url in self.visited:
            return  # Skip if the page has already been visited

        self.logger.info(f"Crawling page: {url} (Depth: {depth})")

        if not self.is_allowed_link(url):
            return
        
        # Fetch the page content
        content = self.fetch(url)
        self.visited.add(url)  # Mark the page as visited
        links = []
        # Process links
        if content is not None:
            links = self.extract_links(content, url)
        self.graph[url] = links

        # Recursively crawl each link (depth-first search)
        for link in links:
            if link not in self.visited:
                self._crawl_page(link, depth + 1)

    def _crawl_entire_site(self, start_url: str):
            """
            Crawl all pages within the same domain as the start URL.
            """
            domain = self.get_home_url(start_url)
            to_visit = [start_url]

            while to_visit:
                url = to_visit.pop(0)
                if url in self.visited:
                    continue

                self.logger.info(f"Crawling page: {url}")
                if not self.is_allowed_link(url):
                    continue

                # Fetch and process the page content
                content = self.fetch(url)
                self.visited.add(url)
                links = []
                if content is not None:
                    links = self.extract_links(content, url)
                self.graph[url] = links

                # Add new links to the queue if they are within the same domain
                for link in links:
                    if link not in self.visited and link.startswith(domain):
                        to_visit.append(link)

    def extract_links(self, page_content: str, base_url: str) -> list:
        """
        Extract links from the page content using BeautifulSoup.
        """
        soup = BeautifulSoup(page_content, 'html.parser')
        links = set()

        for anchor in soup.find_all('a', href=True):
            link = anchor['href']
            # Join the link with the base URL to make it absolute
            full_url = urljoin(base_url, link)
            # Ensure the link is within the allowed domain and allowed by robots.txt
            if self.is_allowed_link(full_url):
                links.add(full_url)

        return list(links)

    def process_data(self, data, file_path=None):
        # Set the default file_path if it's not provided
        if file_path is None:
            file_path = os.path.join(self.settings.get('storage_path', './data'), 'graph.json')
        
        # Create the directory if it does not exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save the graph data to a JSON file
        with open(file_path, 'w') as f:
            dump(data, f, indent=4)

    def get_graph(self):
        """
        Return the graph (nodes and edges).
        """
        return self.graph
