import unittest
import os
from agents.atlas.atlas import Atlas
from bs4 import BeautifulSoup

class TestAtlasCallBack(unittest.TestCase):

    def setUp(self):
        # Create test output directory
        self.test_storage_path = 'test_data'
        os.makedirs(self.test_storage_path, exist_ok=True)

    def simple_callback(self, url: str, html: str) -> dict:
        # Simple callback to validate structure
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else "No Title"
        text = soup.get_text(separator=' ', strip=True)
        return {
            "url": url,
            "title": title,
            "length": len(text)
        }

    def test_crawl_with_callback(self):
        settings = {
            'storage_path': self.test_storage_path,
            'allowed_domains': ['www.startyourline.com'],
            'crawl_entire_website': False,  # Shallow test for faster execution
            'max_depth': 1,
            'results_filename': 'test_results.jsonl'
        }

        atlas = Atlas(settings=settings)
        start_url = "https://www.startyourline.com/index.html"

        # Run the crawler with the test callback
        atlas.crawl(start_url, on_page_crawled=self.simple_callback)

        # Save the graph after crawl
        atlas.process_data(atlas.get_graph())

        # Check graph is not empty
        graph = atlas.get_graph()
        self.assertTrue(len(graph) > 0, "Graph should not be empty after crawling.")

        # Check that results file was created
        results_path = os.path.join(settings['storage_path'], settings['results_filename'])
        self.assertTrue(os.path.exists(results_path), "Results file should be created.")

        # Check that results file has content
        with open(results_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.assertTrue(len(lines) > 0, "Results file should contain at least one entry.")

        # Check that graph.json was created
        graph_path = os.path.join(settings['storage_path'], 'graph.json')
        self.assertTrue(os.path.exists(graph_path), "Graph file should be created.")

        # Optional: Check graph.json is valid JSON and has the correct keys
        import json
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
            self.assertIsInstance(graph_data, dict, "Graph data should be a dictionary.")

    def tearDown(self): # clean up after testing
        import shutil
        shutil.rmtree(self.test_storage_path, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
