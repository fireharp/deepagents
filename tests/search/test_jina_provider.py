"""Tests for Jina search provider."""

import pytest
from unittest.mock import Mock, patch

from deepagents.search.jina_provider import JinaProvider


class TestJinaProvider:
    """Test the Jina search provider."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        with patch("deepagents.search.jina_provider.httpx"):
            provider = JinaProvider(api_key="test-key")
            assert provider.api_key == "test-key"

    def test_init_with_env_var(self):
        """Test initialization with API key from environment."""
        with patch("deepagents.search.jina_provider.httpx"):
            with patch.dict("os.environ", {"JINA_API_KEY": "env-key"}):
                provider = JinaProvider()
                assert provider.api_key == "env-key"

    def test_init_without_api_key(self):
        """Test initialization without API key (should work)."""
        with patch("deepagents.search.jina_provider.httpx"):
            with patch.dict("os.environ", {}, clear=True):
                provider = JinaProvider()
                assert provider.api_key is None

    def test_init_missing_httpx_raises_error(self):
        """Test that missing httpx package raises ImportError."""
        with patch("deepagents.search.jina_provider.httpx", None):
            with pytest.raises(ImportError, match="httpx package is required"):
                JinaProvider()

    def test_init_with_env_config(self):
        """Test initialization with environment configuration."""
        env_vars = {
            "SEARCH_FETCH_CONCURRENCY": "8",
            "SEARCH_HTTP_TIMEOUT_CONNECT": "10",
            "SEARCH_HTTP_TIMEOUT_READ": "30",
        }

        with patch("deepagents.search.jina_provider.httpx") as mock_httpx:
            with patch.dict("os.environ", env_vars):
                provider = JinaProvider()

                assert provider.fetch_concurrency == 8
                assert provider.connect_timeout == 10.0
                assert provider.read_timeout == 30.0

    def test_search_basic_discovery(self):
        """Test basic search with discovery only."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Title",
                    "snippet": "Test snippet",
                }
            ]
        }

        mock_client = Mock()
        mock_client.request.return_value = mock_response

        with patch(
            "deepagents.search.jina_provider.httpx.Client", return_value=mock_client
        ):
            provider = JinaProvider()
            result = provider.search("test query")

        expected = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Title",
                    "content": "Test snippet",
                    "source": "jina",
                }
            ]
        }
        assert result == expected

    def test_search_with_domain_filtering(self):
        """Test search with domain filtering."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "url": "https://wine.com/article",
                    "title": "Wine Article",
                    "snippet": "Wine content",
                },
                {
                    "url": "https://other.com/article",
                    "title": "Other Article",
                    "snippet": "Other content",
                },
            ]
        }

        mock_client = Mock()
        mock_client.request.return_value = mock_response

        with patch(
            "deepagents.search.jina_provider.httpx.Client", return_value=mock_client
        ):
            provider = JinaProvider()
            result = provider.search("test query", include_domains=["wine.com"])

        # Should only include wine.com result
        assert len(result["results"]) == 1
        assert result["results"][0]["url"] == "https://wine.com/article"

    def test_search_with_raw_content(self):
        """Test search with raw content fetching."""
        # Mock discovery response
        discovery_response = Mock()
        discovery_response.status_code = 200
        discovery_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Title",
                    "snippet": "Test snippet",
                }
            ]
        }

        # Mock content response
        content_response = Mock()
        content_response.status_code = 200
        content_response.text = "Full page content here"

        mock_client = Mock()
        mock_client.request.side_effect = [discovery_response, content_response]

        with patch(
            "deepagents.search.jina_provider.httpx.Client", return_value=mock_client
        ):
            provider = JinaProvider()
            result = provider.search("test query", include_raw_content=True)

        # Verify both discovery and content calls were made
        assert mock_client.request.call_count == 2

        # Verify result includes raw_content
        assert result["results"][0]["raw_content"] == "Full page content here"

    def test_search_handles_discovery_error(self):
        """Test search handles discovery API errors gracefully."""
        mock_client = Mock()
        mock_client.request.side_effect = Exception("API Error")

        with patch(
            "deepagents.search.jina_provider.httpx.Client", return_value=mock_client
        ):
            provider = JinaProvider()
            result = provider.search("test query")

        assert result == {"results": []}

    def test_search_handles_content_fetch_error(self):
        """Test search handles content fetch errors gracefully."""
        # Mock successful discovery
        discovery_response = Mock()
        discovery_response.status_code = 200
        discovery_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Title",
                    "snippet": "Test snippet",
                }
            ]
        }

        mock_client = Mock()
        # First call succeeds (discovery), second fails (content)
        mock_client.request.side_effect = [
            discovery_response,
            Exception("Content fetch error"),
        ]

        with patch(
            "deepagents.search.jina_provider.httpx.Client", return_value=mock_client
        ):
            provider = JinaProvider()
            result = provider.search("test query", include_raw_content=True)

        # Should still return result without raw_content
        assert len(result["results"]) == 1
        assert "raw_content" not in result["results"][0]

    def test_normalize_discovery_response_variants(self):
        """Test normalization handles different response schemas."""
        mock_client = Mock()

        with patch(
            "deepagents.search.jina_provider.httpx.Client", return_value=mock_client
        ):
            provider = JinaProvider()

            # Test "data" key variant
            data_variant = {
                "data": [
                    {
                        "url": "https://example.com",
                        "title": "Test Title",
                        "content": "Test content",
                    }
                ]
            }

            normalized = provider._normalize_discovery_response(data_variant, 5)
            assert len(normalized) == 1
            assert normalized[0]["url"] == "https://example.com"

            # Test "items" key variant
            items_variant = {
                "items": [
                    {
                        "url": "https://example2.com",
                        "title": "Test Title 2",
                        "snippet": "Test snippet",
                    }
                ]
            }

            normalized = provider._normalize_discovery_response(items_variant, 5)
            assert len(normalized) == 1
            assert normalized[0]["content"] == "Test snippet"

    def test_make_request_with_retries(self):
        """Test HTTP request retry logic."""
        mock_client = Mock()

        # First call returns 500, second succeeds
        error_response = Mock()
        error_response.status_code = 500

        success_response = Mock()
        success_response.status_code = 200

        mock_client.request.side_effect = [error_response, success_response]

        with patch(
            "deepagents.search.jina_provider.httpx.Client", return_value=mock_client
        ):
            provider = JinaProvider()
            response = provider._make_request("GET", "https://example.com")

        # Should have made 2 calls due to retry
        assert mock_client.request.call_count == 2
        assert response == success_response

    def test_search_fallback_to_simple_url(self):
        """Test fallback to simple URL encoding when structured API fails."""
        # First call (structured API) fails
        error_response = Mock()
        error_response.status_code = 404

        # Second call (simple URL) succeeds
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Test Title",
                    "snippet": "Test snippet",
                }
            ]
        }

        mock_client = Mock()
        mock_client.request.side_effect = [error_response, success_response]

        with patch(
            "deepagents.search.jina_provider.httpx.Client", return_value=mock_client
        ):
            provider = JinaProvider()
            result = provider.search("test query")

        # Should have made 2 calls (structured API + fallback)
        assert mock_client.request.call_count == 2
        assert len(result["results"]) == 1





