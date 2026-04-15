from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from claw_agent.tools.web_tools import web_search


class WebToolsTests(unittest.TestCase):
    @patch("claw_agent.tools.web_tools.httpx.Client")
    def test_web_search_prioritizes_trusted_sources(self, client_cls: Mock) -> None:
        html = """
        <html><body>
        <a rel="nofollow" class="result__a" href="https://example.com/story">Example Story</a>
        <a class="result__snippet">Example snippet</a>
        <a rel="nofollow" class="result__a" href="https://www.reuters.com/world/story">Reuters Story</a>
        <a class="result__snippet">Reuters snippet</a>
        </body></html>
        """

        response = Mock()
        response.text = html
        response.raise_for_status.return_value = None

        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=None)
        client.get.return_value = response
        client_cls.return_value = client

        result = web_search("test query", num_results=2)

        first_reuters = result.find("Reuters Story")
        first_example = result.find("Example Story")
        self.assertNotEqual(first_reuters, -1)
        self.assertNotEqual(first_example, -1)
        self.assertLess(first_reuters, first_example)
        self.assertIn("Source: reuters.com", result)
        self.assertIn("Use web_fetch on the most relevant and trustworthy sources", result)

    @patch("claw_agent.tools.web_tools.httpx.Client")
    def test_web_search_falls_back_to_duckduckgo_lite_parser(self, client_cls: Mock) -> None:
        html_response = Mock()
        html_response.text = "<html><body>No usable results</body></html>"
        html_response.raise_for_status.return_value = None

        lite_response = Mock()
        lite_response.text = """
        <html><body>
        <a class="result-link" href="https://www.state.gov/example">State Department</a>
        <td class="result-snippet">Official update</td>
        </body></html>
        """
        lite_response.raise_for_status.return_value = None

        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=None)
        client.get.side_effect = [html_response, lite_response]
        client_cls.return_value = client

        result = web_search("official update", num_results=1)

        self.assertIn("State Department", result)
        self.assertIn("state.gov", result)


if __name__ == "__main__":
    unittest.main()
