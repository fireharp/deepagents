"""Base protocol for search providers."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SearchProvider(Protocol):
    """Protocol for search providers with normalized interface."""

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_raw_content: bool = False,
        include_domains: list[str] | None = None,
        topic: str | None = None,
    ) -> dict:
        """Search for content and return normalized results.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            include_raw_content: Whether to include raw page content
            include_domains: List of domains to restrict search to
            topic: Optional topic hint for search providers that support it

        Returns:
            Dict with "results" key containing list of normalized result items.
            Each item has: url, title, content, and optionally raw_content, score, source.
        """
        ...





