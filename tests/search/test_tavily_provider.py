"""Tests for Tavily search provider."""

import pytest
from unittest.mock import Mock, patch

from deepagents.search.tavily_provider import TavilyProvider


class TestTavilyProvider:
    """Test the Tavily search provider."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        with patch(
            "deepagents.search.tavily_provider.TavilyClient"
        ) as mock_client_class:
            provider = TavilyProvider(api_key="test-key")
            mock_client_class.assert_called_once_with(api_key="test-key")

    def test_init_with_env_var(self):
        """Test initialization with API key from environment."""
        with patch(
            "deepagents.search.tavily_provider.TavilyClient"
        ) as mock_client_class:
            with patch.dict("os.environ", {"TAVILY_API_KEY": "env-key"}):
                provider = TavilyProvider()
                mock_client_class.assert_called_once_with(api_key="env-key")

    def test_init_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with patch("deepagents.search.tavily_provider.TavilyClient"):
            with patch.dict("os.environ", {}, clear=True):
                with pytest.raises(ValueError, match="TAVILY_API_KEY"):
                    TavilyProvider()

    def test_init_missing_tavily_package_raises_error(self):
        """Test that missing tavily package raises ImportError."""
        with patch("deepagents.search.tavily_provider.TavilyClient", None):
            with pytest.raises(ImportError, match="tavily-python package is required"):
                TavilyProvider(api_key="test-key")

    def test_search_basic(self):
        """Test basic search functionality."""
        mock_client = Mock()
        mock_client.search.return_value = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Title",
                    "content": "Test content",
                    "score": 0.9,
                }
            ]
        }

        with patch(
            "deepagents.search.tavily_provider.TavilyClient", return_value=mock_client
        ):
            provider = TavilyProvider(api_key="test-key")
            result = provider.search("test query")

        # Verify client was called correctly
        mock_client.search.assert_called_once_with(
            query="test query",
            max_results=5,
            include_raw_content=False,
            include_domains=None,
            topic=None,
        )

        # Verify normalized result
        expected = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Title",
                    "content": "Test content",
                    "source": "tavily",
                    "score": 0.9,
                }
            ]
        }
        assert result == expected

    def test_search_with_raw_content(self):
        """Test search with raw content included."""
        mock_client = Mock()
        mock_client.search.return_value = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Title",
                    "content": "Test content",
                    "raw_content": "Raw content here",
                }
            ]
        }

        with patch(
            "deepagents.search.tavily_provider.TavilyClient", return_value=mock_client
        ):
            provider = TavilyProvider(api_key="test-key")
            result = provider.search("test query", include_raw_content=True)

        # Verify raw_content is included
        assert result["results"][0]["raw_content"] == "Raw content here"

    def test_search_with_raw_content_alternate_key(self):
        """Test search with rawContent key (alternate format)."""
        mock_client = Mock()
        mock_client.search.return_value = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Title",
                    "content": "Test content",
                    "rawContent": "Raw content here",
                }
            ]
        }

        with patch(
            "deepagents.search.tavily_provider.TavilyClient", return_value=mock_client
        ):
            provider = TavilyProvider(api_key="test-key")
            result = provider.search("test query", include_raw_content=True)

        # Verify rawContent is mapped to raw_content
        assert result["results"][0]["raw_content"] == "Raw content here"

    def test_search_with_all_parameters(self):
        """Test search with all parameters."""
        mock_client = Mock()
        mock_client.search.return_value = {"results": []}

        with patch(
            "deepagents.search.tavily_provider.TavilyClient", return_value=mock_client
        ):
            provider = TavilyProvider(api_key="test-key")
            provider.search(
                query="wine review",
                max_results=10,
                include_raw_content=True,
                include_domains=["wine.com", "vivino.com"],
                topic="wine",
            )

        mock_client.search.assert_called_once_with(
            query="wine review",
            max_results=10,
            include_raw_content=True,
            include_domains=["wine.com", "vivino.com"],
            topic="wine",
        )

    def test_search_handles_missing_fields(self):
        """Test search handles missing fields gracefully."""
        mock_client = Mock()
        mock_client.search.return_value = {
            "results": [
                {
                    "url": "https://example.com",
                    # Missing title and content
                }
            ]
        }

        with patch(
            "deepagents.search.tavily_provider.TavilyClient", return_value=mock_client
        ):
            provider = TavilyProvider(api_key="test-key")
            result = provider.search("test query")

        expected = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "",
                    "content": "",
                    "source": "tavily",
                }
            ]
        }
        assert result == expected

    def test_search_error_returns_empty_results(self):
        """Test that search errors return empty results."""
        mock_client = Mock()
        mock_client.search.side_effect = Exception("API Error")

        with patch(
            "deepagents.search.tavily_provider.TavilyClient", return_value=mock_client
        ):
            provider = TavilyProvider(api_key="test-key")
            result = provider.search("test query")

        assert result == {"results": []}





