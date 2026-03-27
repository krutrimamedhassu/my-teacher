import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse
import time
import random
from pathlib import Path
import json

from app.logger.app_logger import app_logger


class WebScraper:
    """Class for scraping web content."""
    
    # Default headers to mimic a browser
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    # Rate limiting settings
    MIN_REQUEST_INTERVAL = 1.0  # Minimum time between requests in seconds
    
    # Cache settings
    CACHE_DIR = Path("cache/scraper")
    CACHE_ENABLED = True
    CACHE_EXPIRY = 86400  # 24 hours in seconds
    
    @classmethod
    def _get_cache_path(cls, url: str) -> Path:
        """
        Get cache file path for a URL.
        
        Args:
            url: URL to get cache path for
            
        Returns:
            Path: Cache file path
        """
        # Create a filename from the URL
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path.replace("/", "_")
        if not path:
            path = "_root"
        
        filename = f"{domain}{path}.json"
        return cls.CACHE_DIR / filename
    
    @classmethod
    def _save_to_cache(cls, url: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Save scraped content to cache.
        
        Args:
            url: URL of the content
            content: Scraped content
            metadata: Additional metadata to cache
        """
        if not cls.CACHE_ENABLED:
            return
        
        # Ensure cache directory exists
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        cache_path = cls._get_cache_path(url)
        cache_data = {
            "url": url,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            app_logger.log_info(f"Saved URL content to cache: {url}")
        except Exception as e:
            app_logger.log_warning(f"Failed to save URL content to cache: {e}")
    
    @classmethod
    def _load_from_cache(cls, url: str) -> Optional[Dict[str, Any]]:
        """
        Load scraped content from cache.
        
        Args:
            url: URL to load from cache
            
        Returns:
            Optional[Dict[str, Any]]: Cached data or None if not found or expired
        """
        if not cls.CACHE_ENABLED:
            return None
        
        cache_path = cls._get_cache_path(url)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            if time.time() - cache_data["timestamp"] > cls.CACHE_EXPIRY:
                app_logger.log_debug(f"Cache expired for URL: {url}")
                return None
            
            app_logger.log_debug(f"Loaded URL content from cache: {url}")
            return cache_data
        except Exception as e:
            app_logger.log_warning(f"Failed to load URL content from cache: {e}")
            return None
    
    @classmethod
    def scrape_url(
        cls,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        timeout: int = 30
    ) -> str:
        """
        Scrape content from a URL.
        
        Args:
            url: URL to scrape
            headers: HTTP headers to use
            params: URL parameters
            use_cache: Whether to use cache
            timeout: Request timeout in seconds
            
        Returns:
            str: Scraped HTML content
            
        Raises:
            requests.RequestException: If request fails
        """
        # Check cache first if enabled
        if use_cache and cls.CACHE_ENABLED:
            cached_data = cls._load_from_cache(url)
            if cached_data:
                return cached_data["content"]
        
        # Prepare request
        request_headers = headers or cls.DEFAULT_HEADERS
        
        # Add a small random delay for rate limiting
        time.sleep(cls.MIN_REQUEST_INTERVAL + random.random())
        
        # Make the request
        app_logger.log_info(f"Scraping URL: {url}")
        try:
            response = requests.get(
                url,
                headers=request_headers,
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Save to cache if enabled
            if cls.CACHE_ENABLED:
                cls._save_to_cache(
                    url,
                    response.text,
                    {"status_code": response.status_code, "headers": dict(response.headers)}
                )
            
            return response.text
        except requests.RequestException as e:
            app_logger.log_error(f"Failed to scrape URL {url}: {e}")
            raise
    
    @classmethod
    def extract_text_from_html(cls, html_content: str) -> str:
        """
        Extract main text content from HTML.
        
        Args:
            html_content: HTML content to extract text from
            
        Returns:
            str: Extracted text content
        """
        app_logger.log_info("Extracting text from HTML content")
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script, style, nav, footer, and other non-content tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        # Prefer main content containers if present
        main = soup.find("main") or soup.find("article") or soup.find(id="content") or soup.find(class_="content")
        target = main if main else soup.body if soup.body else soup

        text = target.get_text(separator="\n")
        # Collapse excessive blank lines
        lines = [line.strip() for line in text.splitlines()]
        cleaned = "\n".join(line for line in lines if line)
        return cleaned
    
    @classmethod
    def extract_metadata_from_html(cls, html_content: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML (title, description, etc.).
        
        Args:
            html_content: HTML content to extract metadata from
            
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        app_logger.log_info("Extracting metadata from HTML content")
        soup = BeautifulSoup(html_content, "html.parser")

        def meta(name: str, attr: str = "name") -> str:
            tag = soup.find("meta", attrs={attr: name})
            return tag["content"].strip() if tag and tag.get("content") else ""

        title = soup.title.string.strip() if soup.title and soup.title.string else meta("og:title", "property")
        description = meta("description") or meta("og:description", "property")
        keywords_raw = meta("keywords")
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()] if keywords_raw else []

        return {
            "title": title,
            "description": description,
            "keywords": keywords,
            "og_image": meta("og:image", "property"),
            "og_url": meta("og:url", "property"),
        }
    
    @classmethod
    def scrape_and_extract(cls, url: str) -> Dict[str, Any]:
        """
        Scrape a URL and extract text and metadata.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict[str, Any]: Dictionary with extracted text and metadata
        """
        html_content = cls.scrape_url(url)
        text_content = cls.extract_text_from_html(html_content)
        metadata = cls.extract_metadata_from_html(html_content)
        
        return {
            "url": url,
            "html": html_content,
            "text": text_content,
            "metadata": metadata
        }


# Example usage
if __name__ == "__main__":
    # This code will only run if the file is executed directly
    result = WebScraper.scrape_and_extract("https://example.com")
    app_logger.log_info(f"Title: {result['metadata']['title']}")
    app_logger.log_info(f"Text length: {len(result['text'])}")