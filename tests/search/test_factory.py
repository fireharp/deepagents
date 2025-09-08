"""Tests for search provider factory."""

import os
import pytest
from unittest.mock import patch

from deepagents.search.factory import get_search_provider_from_env
from deepagents.search.tavily_provider import TavilyProvider
from deepagents.search.jina_provider import JinaProvider


class TestSearchProviderFactory:
    """Test the search provider factory function."""

    def test_default_backend_is_tavily(self):
        """Test that default backend is Tavily when no env var is set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}):
                provider = get_search_provider_from_env()
                assert isinstance(provider, TavilyProvider)

    def test_tavily_backend_explicit(self):
        """Test explicit Tavily backend selection."""
        with patch.dict(
            os.environ, {"SEARCH_BACKEND": "tavily", "TAVILY_API_KEY": "test-key"}
        ):
            provider = get_search_provider_from_env()
            assert isinstance(provider, TavilyProvider)

    def test_jina_backend_explicit(self):
        """Test explicit Jina backend selection."""
        with patch.dict(os.environ, {"SEARCH_BACKEND": "jina"}):
            provider = get_search_provider_from_env()
            assert isinstance(provider, JinaProvider)

    def test_case_insensitive_backend(self):
        """Test that backend selection is case insensitive."""
        with patch.dict(
            os.environ, {"SEARCH_BACKEND": "TAVILY", "TAVILY_API_KEY": "test-key"}
        ):
            provider = get_search_provider_from_env()
            assert isinstance(provider, TavilyProvider)

        with patch.dict(os.environ, {"SEARCH_BACKEND": "JINA"}):
            provider = get_search_provider_from_env()
            assert isinstance(provider, JinaProvider)

    def test_unsupported_backend_raises_error(self):
        """Test that unsupported backend raises ValueError."""
        with patch.dict(os.environ, {"SEARCH_BACKEND": "unsupported"}):
            with pytest.raises(
                ValueError, match="Unsupported search backend: unsupported"
            ):
                get_search_provider_from_env()

    def test_tavily_missing_api_key_raises_error(self):
        """Test that missing Tavily API key raises error."""
        with patch.dict(os.environ, {"SEARCH_BACKEND": "tavily"}, clear=True):
            with pytest.raises(ValueError, match="TAVILY_API_KEY"):
                get_search_provider_from_env()





