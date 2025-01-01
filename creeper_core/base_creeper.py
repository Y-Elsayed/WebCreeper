# creeper_core/base_creeper.py
from abc import ABC, abstractmethod
from creeper_core.utils import configure_logging
import requests
from urllib.parse import urlparse

class BaseCreeper(ABC):
    # Default settings for the crawler
    DEFAULT_SETTINGS = {
        "base_url": None,
        "timeout": 10,
        "user_agent": "DefaultCrawler",
        "max_depth": 1,
        "allowed_domains": [],
        "storage_path": "../data",
    }

    def __init__(self, settings: dict = {}):
        self.settings = {**self.DEFAULT_SETTINGS, **settings}  # Merging default and passed settings
        self.logger = configure_logging(self.__class__.__name__)

    @abstractmethod
    def crawl(self):
        """
        Abstract method to be implemented by all crawlers.
        Defines the main crawling logic.
        """
        pass

    @abstractmethod
    def process_data(self, data):
        """
        Abstract method to process raw data.
        """
        pass

    def fetch(self, url: str):
        """
        Fetches content from the given URL using settings from self.settings.
        """
        try:
            self.logger.info(f"Fetching: {url}")
            headers = {
                'User-Agent': self.settings.get('user_agent', 'DefaultCrawler')  # Using the user agent from settings and defaulting to 'DefaultCrawler'
            }
            response = requests.get(url, headers=headers, timeout=self.settings.get('timeout', 10))  # Using timeout from settings and defaulting to 10 seconds
            response.raise_for_status() 
            return response.text  # Returning the HTML content of the page
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            raise


    def get_home_url(self, url: str) -> str:
        """
        Extracts the home URL from a given URL.
        """
        self.logger.info(f"Extracting home URL from: {url}")
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    #Should be used in each crawler to check if the URL is allowed to be crawled
    def fetch_robots_txt(self, url: str) -> str:
        """
        Fetches the robots.txt file from the home of the website.
        """
        home_url = self.get_home_url(url)
        robots_url = f"{home_url}/robots.txt"
        try:
            self.logger.info(f"Fetching robots.txt from: {home_url}")
            headers = {
                'User-Agent': self.settings.get('user_agent', 'DefaultCrawler')
            }
            response = requests.get(robots_url, headers=headers, timeout=self.settings.get('timeout', 10)) # Using timeout from settings and defaulting to 10 seconds
            if response.status_code == 200:
                self.logger.info("Successfully fetched robots.txt")
                return response.text
            else:
                self.logger.warning(f"No robots.txt found at {robots_url}") # Logging a warning if no robots.txt is found
                return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error accessing robots.txt: {e}") # Logging an error if there is an exception
            return None
