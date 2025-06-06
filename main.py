import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from urllib.parse import urljoin, urlparse
import logging
import sys

logging.basicConfig(level=logging.INFO)

class WebCrawler:
    def __init__(self):
        self.index = {}  # url -> text
        self.visited = set()

    def crawl(self, url, base_url=None, max_depth=3, depth=0):
        if url in self.visited or depth > max_depth:
            return
        self.visited.add(url)
        try:
            response = requests.get(url, timeout=5)
            if 'text/html' not in response.headers.get('Content-Type', ''):
                return  # Only index HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            self.index[url] = soup.get_text()
            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    href = urljoin(base_url or url, href)
                    # Avoid crawling external domains
                    if base_url:
                        if not href.startswith(base_url):
                            continue
                    else:
                        if urlparse(href).netloc != urlparse(url).netloc:
                            continue
                    self.crawl(href, base_url=base_url or url, max_depth=max_depth, depth=depth+1)
        except Exception as e:
            logging.error(f"Error crawling {url}: {e}")

    def search(self, keyword):
        if not isinstance(keyword, str) or not keyword:
            return []
        results = []
        for url, text in self.index.items():
            if keyword.lower() in text.lower():
                results.append(url)
        return results

    def print_results(self, results, file=sys.stdout):
        if results:
            print("Search results:", file=file)
            for result in results:
                print(f"- {result}", file=file)
        else:
            print("No results found.", file=file)

def main():
    crawler = WebCrawler()
    start_url = "https://example.com"
    crawler.crawl(start_url)

    keyword = "test"
    results = crawler.search(keyword)
    crawler.print_results(results)

import unittest
from unittest.mock import patch, MagicMock
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from urllib.parse import urljoin, urlparse

class WebCrawlerTests(unittest.TestCase):
    @patch('requests.get')
    def test_crawl_success(self, mock_get):
        sample_html = """
        <html><body>
            <h1>Welcome!</h1>
            <a href="/about">About Us</a>
            <a href="https://www.external.com">External Link</a>
        </body></html>
        """
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response
        crawler = WebCrawler()
        crawler.crawl("https://example.com")
        self.assertIn("https://example.com/about", crawler.visited)
        self.assertIn("https://example.com", crawler.index)
        self.assertNotIn("https://www.external.com", crawler.visited)

    @patch('requests.get')
    def test_crawl_non_html(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "not html"
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_get.return_value = mock_response
        crawler = WebCrawler()
        crawler.crawl("https://example.com/api")
        self.assertNotIn("https://example.com/api", crawler.index)

    @patch('requests.get')
    def test_crawl_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Test Error")
        crawler = WebCrawler()
        with self.assertLogs(level='ERROR') as log:
            crawler.crawl("https://example.com")
        self.assertTrue(any("Error crawling" in msg for msg in log.output))

    @patch('requests.get')
    def test_crawl_circular(self, mock_get):
        html1 = '<a href="/page2">Page2</a>'
        html2 = '<a href="/">Home</a>'
        def side_effect(url, *a, **kw):
            resp = MagicMock()
            resp.headers = {'Content-Type': 'text/html'}
            resp.text = html2 if url.endswith('page2') else html1
            return resp
        mock_get.side_effect = side_effect
        crawler = WebCrawler()
        crawler.crawl("https://example.com/")
        self.assertIn("https://example.com/page2", crawler.visited)
        self.assertIn("https://example.com/", crawler.visited)
        self.assertEqual(len(crawler.visited), 2)

    def test_search_empty(self):
        crawler = WebCrawler()
        crawler.index = {"page1": "No match here"}
        results = crawler.search("notfound")
        self.assertEqual(results, [])

    def test_search_case_insensitive(self):
        crawler = WebCrawler()
        crawler.index = {"page1": "KEYword here"}
        results = crawler.search("keyword")
        self.assertEqual(results, ["page1"])

    def test_search_invalid(self):
        crawler = WebCrawler()
        crawler.index = {"page1": "something"}
        self.assertEqual(crawler.search(None), [])
        self.assertEqual(crawler.search(""), [])

    def test_print_results_found(self):
        from io import StringIO
        crawler = WebCrawler()
        buf = StringIO()
        crawler.print_results(["https://test.com/result"], file=buf)
        output = buf.getvalue()
        self.assertIn("Search results:", output)
        self.assertIn("- https://test.com/result", output)

    def test_print_results_not_found(self):
        from io import StringIO
        crawler = WebCrawler()
        buf = StringIO()
        crawler.print_results([], file=buf)
        output = buf.getvalue()
        self.assertIn("No results found.", output)

    @patch('requests.get')
    def test_crawl_max_depth(self, mock_get):
        html = '<a href="/page2">Page2</a>'
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_get.return_value = mock_response
        crawler = WebCrawler()
        crawler.crawl("https://example.com", max_depth=0)
        self.assertEqual(len(crawler.visited), 1)

if __name__ == "__main__":
    unittest.main()  # Run unit tests
    main()  # Run your main application logic
