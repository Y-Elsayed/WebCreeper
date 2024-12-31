# creeper_core/base_creeper.py
from abc import ABC, abstractmethod
from creeper_core.utils import configure_logging
import requests

class BaseCreeper(ABC):
    DEFAULT_SETTINGS = {
        "base_url": None,
        "timeout": 10,
        "user_agent": "",
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
                'User-Agent': self.settings.get('user_agent', 'DefaultCrawler')  # Using the user agent from settings
            }
            response = requests.get(url, headers=headers, timeout=self.settings.get('timeout', 10))  # Using timeout from settings
            response.raise_for_status() 
            return response.text  # Returning the HTML content of the page
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            raise
