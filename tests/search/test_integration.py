"""Integration tests for search providers."""

import os
from unittest.mock import patch, Mock

from deepagents.search import get_search_provider_from_env
from deepagents.search.base import SearchProvider


class TestSearchIntegration:
    """Test integration between search providers and wine agent."""

    def test_provider_interface_compliance(self):
        """Test that all providers implement the SearchProvider protocol."""
        # Test Tavily provider
        with patch.dict(
            os.environ, {"SEARCH_BACKEND": "tavily", "TAVILY_API_KEY": "test-key"}
        ):
            provider = get_search_provider_from_env()
            assert isinstance(provider, SearchProvider)
            assert hasattr(provider, "search")

        # Test Jina provider
        with patch.dict(os.environ, {"SEARCH_BACKEND": "jina"}):
            provider = get_search_provider_from_env()
            assert isinstance(provider, SearchProvider)
            assert hasattr(provider, "search")

    def test_wine_agent_compatibility(self):
        """Test that provider output is compatible with wine_agent caching logic."""
        # Mock a provider response that matches wine_agent expectations
        mock_result = {
            "results": [
                {
                    "url": "https://wine-searcher.com/test",
                    "title": "Test Wine Review",
                    "content": "Short snippet",
                    "raw_content": "Full page content for caching",
                    "source": "tavily",
                }
            ]
        }

        # Test with Tavily provider
        with patch(
            "deepagents.search.tavily_provider.TavilyClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.search.return_value = {
                "results": [
                    {
                        "url": "https://wine-searcher.com/test",
                        "title": "Test Wine Review",
                        "content": "Short snippet",
                        "raw_content": "Full page content for caching",
                    }
                ]
            }
            mock_client_class.return_value = mock_client

            with patch.dict(
                os.environ, {"SEARCH_BACKEND": "tavily", "TAVILY_API_KEY": "test-key"}
            ):
                provider = get_search_provider_from_env()
                result = provider.search(
                    query="test wine",
                    max_results=3,
                    include_raw_content=True,
                    include_domains=["wine-searcher.com"],
                )

        # Verify result structure matches wine_agent expectations
        assert "results" in result
        assert isinstance(result["results"], list)

        if result["results"]:
            item = result["results"][0]
            assert "url" in item
            assert "title" in item
            assert "content" in item or "raw_content" in item
            assert item["url"] == "https://wine-searcher.com/test"

    def test_caching_compatibility(self):
        """Test that provider results work with wine_agent caching logic."""

        # Simulate the wine_agent caching logic
        def extract_cache_data(result_item):
            """Simulate wine_agent's caching extraction logic."""
            url = result_item.get("url") or ""
            content = (
                result_item.get("raw_content")
                or result_item.get("content")
                or result_item.get("rawContent")
                or ""
            )
            title = result_item.get("title") or ""
            return url, content, title

        # Test with mock provider result
        mock_result = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Title",
                    "content": "Test content",
                    "raw_content": "Full content",
                    "source": "jina",
                }
            ]
        }

        # Extract data as wine_agent would
        for item in mock_result["results"]:
            url, content, title = extract_cache_data(item)

            assert url == "https://example.com"
            assert content == "Full content"  # Should prefer raw_content
            assert title == "Test Title"

    def test_domain_filtering_wine_domains(self):
        """Test domain filtering with wine-specific domains."""
        wine_domains = [
            "wine-searcher.com",
            "vivino.com",
            "winefolly.com",
            "wineenthusiast.com",
            "jancisrobinson.com",
            "winespectator.com",
            "decanter.com",
        ]

        # Mock Jina provider with mixed domains
        mock_discovery_response = Mock()
        mock_discovery_response.status_code = 200
        mock_discovery_response.json.return_value = {
            "results": [
                {
                    "url": "https://wine-searcher.com/article",
                    "title": "Wine Article",
                    "snippet": "Wine content",
                },
                {
                    "url": "https://random-site.com/article",
                    "title": "Random Article",
                    "snippet": "Random content",
                },
                {
                    "url": "https://vivino.com/review",
                    "title": "Wine Review",
                    "snippet": "Review content",
                },
            ]
        }

        mock_client = Mock()
        mock_client.request.return_value = mock_discovery_response

        with patch(
            "deepagents.search.jina_provider.httpx.Client", return_value=mock_client
        ):
            with patch.dict(os.environ, {"SEARCH_BACKEND": "jina"}):
                provider = get_search_provider_from_env()
                result = provider.search("wine review", include_domains=wine_domains)

        # Should only include wine domain results
        assert len(result["results"]) == 2
        urls = [item["url"] for item in result["results"]]
        assert "https://wine-searcher.com/article" in urls
        assert "https://vivino.com/review" in urls
        assert "https://random-site.com/article" not in urls

    def test_error_handling_returns_empty_results(self):
        """Test that both providers return empty results on errors."""
        # Test Tavily provider error handling
        with patch(
            "deepagents.search.tavily_provider.TavilyClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.search.side_effect = Exception("API Error")
            mock_client_class.return_value = mock_client

            with patch.dict(
                os.environ, {"SEARCH_BACKEND": "tavily", "TAVILY_API_KEY": "test-key"}
            ):
                provider = get_search_provider_from_env()
                result = provider.search("test query")
                assert result == {"results": []}

        # Test Jina provider error handling
        mock_client = Mock()
        mock_client.request.side_effect = Exception("Network Error")

        with patch(
            "deepagents.search.jina_provider.httpx.Client", return_value=mock_client
        ):
            with patch.dict(os.environ, {"SEARCH_BACKEND": "jina"}):
                provider = get_search_provider_from_env()
                result = provider.search("test query")
                assert result == {"results": []}





