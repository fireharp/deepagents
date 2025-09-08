"""Jina search provider implementation using s.jina.ai and r.jina.ai."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, quote

try:
    import httpx
except ImportError:
    httpx = None


class JinaProvider:
    """Jina search provider using s.jina.ai for discovery and r.jina.ai for content."""

    def __init__(self, api_key: str | None = None):
        if httpx is None:
            raise ImportError("httpx package is required for JinaProvider")

        self.api_key = api_key or os.environ.get("JINA_API_KEY")
        self.fetch_concurrency = int(os.environ.get("SEARCH_FETCH_CONCURRENCY", "4"))
        self.connect_timeout = float(os.environ.get("SEARCH_HTTP_TIMEOUT_CONNECT", "5"))
        self.read_timeout = float(os.environ.get("SEARCH_HTTP_TIMEOUT_READ", "20"))

        # Create HTTP client with timeouts and retries
        self.client = httpx.Client(
            timeout=httpx.Timeout(
                connect=self.connect_timeout,
                read=self.read_timeout,
                write=None,
                pool=None,
            ),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, "client"):
            self.client.close()

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_raw_content: bool = False,
        include_domains: list[str] | None = None,
        topic: str | None = None,
    ) -> dict:
        """Search using Jina s.jina.ai and optionally fetch content with r.jina.ai."""
        try:
            # Step 1: Discovery via s.jina.ai
            search_results = self._discover_urls(query, max_results)

            # Step 2: Domain filtering if specified
            if include_domains:
                search_results = self._filter_by_domains(
                    search_results, include_domains
                )

            # Step 3: Fetch raw content if requested
            if include_raw_content:
                search_results = self._hydrate_with_content(search_results)

            # Add source metadata
            for result in search_results:
                result["source"] = "jina"

            return {"results": search_results}

        except Exception:
            # Return empty results on error to match spec
            return {"results": []}

    def _discover_urls(self, query: str, max_results: int) -> list[dict]:
        """Discover URLs using s.jina.ai search."""
        import os

        debug = os.environ.get("WINE_SEARCH_DEBUG") == "1"

        if debug:
            print(f"🔍 Jina discovery: query='{query}', max_results={max_results}")

        headers = {"Accept": "application/json", "User-Agent": "deepagents/1.0"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            if debug:
                print(f"🔑 Using API key: {self.api_key[:20]}...")

        try:
            encoded_query = quote(query)

            # Try structured API first: e.g., https://s.jina.ai/search?q=...&size=..
            structured_url = (
                f"https://s.jina.ai/search?q={encoded_query}&size={max_results}"
            )
            if debug:
                print(f"📡 Calling Jina API (structured): {structured_url}")
                print(f"   Headers: {headers}")

            response = self._make_request("GET", structured_url, headers=headers)

            if debug:
                print(f"📡 Response: {response.status_code}")

            if response.status_code == 200:
                # Prefer JSON; fall back gracefully if not JSON
                try:
                    data = response.json()
                    if debug:
                        print(f"📊 JSON response keys: {list(data.keys())}")
                    results = self._normalize_discovery_response(data, max_results)
                    if debug:
                        print(f"✅ API returned {len(results)} results")
                    if results:
                        return results
                except Exception as json_error:
                    if debug:
                        print(f"❌ JSON parsing failed: {json_error}")
                    # Try text fallback
                    try:
                        text = (response.text or "").strip()
                        if text and not text.startswith("<"):
                            results = [
                                {
                                    "url": f"https://search-result-for-{encoded_query}",
                                    "title": f"Search results for: {query}",
                                    "content": text[:200] + "..."
                                    if len(text) > 200
                                    else text,
                                }
                            ]
                            return results
                    except Exception:
                        pass

            # If the structured endpoint rejects the query (e.g., 422), try a sanitized version
            if response.status_code == 422:
                try:
                    sanitized_query = self._sanitize_query(query)
                    if sanitized_query and sanitized_query != query:
                        encoded_sanitized = quote(sanitized_query)
                        retry_url = f"https://s.jina.ai/search?q={encoded_sanitized}&size={max_results}"
                        if debug:
                            print(
                                f"🔁 Retrying with sanitized query: '{sanitized_query}'"
                            )
                            print(f"📡 Calling Jina API (sanitized): {retry_url}")
                        retry_resp = self._make_request(
                            "GET", retry_url, headers=headers
                        )
                        if retry_resp.status_code == 200:
                            try:
                                data = retry_resp.json()
                                results = self._normalize_discovery_response(
                                    data, max_results
                                )
                                if results:
                                    return results
                            except Exception:
                                pass
                except Exception:
                    pass

            # Fallback to simple URL if structured API failed (or produced no results)
            simple_url = f"https://s.jina.ai/{encoded_query}"
            if debug:
                print(f"↩️ Falling back to simple API: {simple_url}")

            response = self._make_request("GET", simple_url, headers=headers)

            if response.status_code == 200:
                try:
                    data = response.json()
                    results = self._normalize_discovery_response(data, max_results)
                    if results:
                        return results
                except Exception:
                    try:
                        text = (response.text or "").strip()
                        if text and not text.startswith("<"):
                            return [
                                {
                                    "url": f"https://search-result-for-{encoded_query}",
                                    "title": f"Search results for: {query}",
                                    "content": text[:200] + "..."
                                    if len(text) > 200
                                    else text,
                                }
                            ]
                    except Exception:
                        pass
            else:
                if debug:
                    snippet = ""
                    try:
                        snippet = (response.text or "")[:200]
                    except Exception:
                        pass
                    print(f"❌ API error {response.status_code}: {snippet}")

        except Exception as e:
            if debug:
                print(f"❌ API call failed: {e}")

        if debug:
            print("❌ No results found, returning empty")
        return []

    def _sanitize_query(self, query: str) -> str:
        """Make a strict query more acceptable to s.jina.ai when it returns 422.

        - Strip double/single quotes
        - Replace boolean operators like OR/AND with spaces
        - Collapse redundant whitespace
        """
        try:
            q = query.replace('"', " ").replace("'", " ")
            for op in [" OR ", " AND ", "(OR)", "(AND)", "OR", "AND", "|", "+"]:
                q = q.replace(op, " ")
            q = " ".join(q.split())
            return q
        except Exception:
            return query

    def _normalize_discovery_response(self, data: dict, max_results: int) -> list[dict]:
        """Normalize discovery response from various possible schemas."""
        results = []

        # Try different possible response formats
        items = data.get("results") or data.get("data") or data.get("items") or []

        for item in items[:max_results]:
            if isinstance(item, dict):
                result = {
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "content": item.get("snippet", "") or item.get("content", ""),
                }

                # Only add if we have a valid URL
                if result["url"]:
                    results.append(result)

        return results

    def _filter_by_domains(
        self, results: list[dict], include_domains: list[str]
    ) -> list[dict]:
        """Filter results by allowed domains."""
        filtered = []

        for result in results:
            url = result.get("url", "")
            if not url:
                continue

            try:
                hostname = urlparse(url).hostname
                if hostname and any(domain in hostname for domain in include_domains):
                    filtered.append(result)
            except Exception:
                continue

        return filtered

    def _hydrate_with_content(self, results: list[dict]) -> list[dict]:
        """Fetch raw content for URLs using r.jina.ai."""
        if not results:
            return results

        # Use ThreadPoolExecutor for concurrent fetching
        with ThreadPoolExecutor(max_workers=self.fetch_concurrency) as executor:
            # Submit all fetch tasks
            future_to_result = {
                executor.submit(self._fetch_content, result["url"]): result
                for result in results
            }

            # Collect results as they complete
            for future in as_completed(future_to_result):
                result = future_to_result[future]
                try:
                    content = future.result()
                    if content:
                        result["raw_content"] = content
                except Exception:
                    # Keep item without raw_content on fetch failure
                    pass

        return results

    def _fetch_content(self, url: str) -> str:
        """Fetch content for a single URL using r.jina.ai."""
        try:
            reader_url = f"https://r.jina.ai/{url}"
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = self._make_request("GET", reader_url, headers=headers)

            if response.status_code == 200:
                return response.text

        except Exception:
            pass

        return ""

    def _make_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with retries."""
        max_retries = 2

        for attempt in range(max_retries + 1):
            try:
                response = self.client.request(method, url, **kwargs)

                # Retry on 5xx errors
                if response.status_code >= 500 and attempt < max_retries:
                    continue

                return response

            except (httpx.TimeoutException, httpx.ConnectError):
                if attempt < max_retries:
                    continue
                raise

        # This shouldn't be reached, but just in case
        return self.client.request(method, url, **kwargs)
