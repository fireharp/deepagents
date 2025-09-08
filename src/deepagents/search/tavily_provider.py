"""Tavily search provider implementation."""

import os

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None


class TavilyProvider:
    """Tavily search provider that wraps TavilyClient."""

    def __init__(self, api_key: str | None = None):
        if TavilyClient is None:
            raise ImportError("tavily-python package is required for TavilyProvider")

        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "TAVILY_API_KEY environment variable or api_key parameter is required"
            )

        self.client = TavilyClient(api_key=self.api_key)

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_raw_content: bool = False,
        include_domains: list[str] | None = None,
        topic: str | None = None,
    ) -> dict:
        """Search using Tavily and normalize results."""
        try:
            result = self.client.search(
                query=query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                include_domains=include_domains,
                topic=topic,
            )

            # Normalize the results to ensure consistent format
            normalized_results = []
            for item in result.get("results", []):
                normalized_item = {
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "source": "tavily",
                }

                # Add raw_content if available and requested
                if include_raw_content and "raw_content" in item:
                    normalized_item["raw_content"] = item["raw_content"]
                elif include_raw_content and "rawContent" in item:
                    normalized_item["raw_content"] = item["rawContent"]

                # Add score if available
                if "score" in item:
                    normalized_item["score"] = item["score"]

                normalized_results.append(normalized_item)

            return {"results": normalized_results}

        except Exception:
            # Return empty results on error to match spec
            return {"results": []}





