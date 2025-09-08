"""Factory function for creating search providers based on environment configuration."""

import os

from .base import SearchProvider
from .tavily_provider import TavilyProvider
from .jina_provider import JinaProvider


def get_search_provider_from_env() -> SearchProvider:
    """Create and return a search provider based on environment configuration.

    Uses SEARCH_BACKEND environment variable to determine provider:
    - "tavily" (default): Use TavilyProvider
    - "jina": Use JinaProvider

    Returns:
        SearchProvider instance configured from environment

    Raises:
        ValueError: If backend is unsupported or required API keys are missing
        ImportError: If required packages are not installed
    """
    backend = os.environ.get("SEARCH_BACKEND", "tavily").lower()

    if backend == "tavily":
        return TavilyProvider()
    elif backend == "jina":
        return JinaProvider()
    else:
        raise ValueError(
            f"Unsupported search backend: {backend}. Supported: tavily, jina"
        )





