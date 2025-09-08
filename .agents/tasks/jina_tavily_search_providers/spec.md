## Jina/Tavily search providers – single entry point, swappable backends

### Goal

- Provide the same interface/behavior currently used with Tavily, but allow choosing between two providers: Tavily (existing) and Jina (s.jina.ai + r.jina.ai).
- Keep `examples/research/wine_agent.py` caching and per-run caps unchanged; only replace the search call with a provider call.

### Public interface (drop-in parity)

```python
class SearchProvider:
    def search(
        self,
        query: str,
        max_results: int = 5,
        include_raw_content: bool = False,
        include_domains: list[str] | None = None,
        topic: str | None = None,
    ) -> dict:  # {"results": [{"url","title","content","raw_content"?}]}
        ...
```

- Input params match current Tavily usage in `internet_search`.
- Output must be a dict with key `results` (list of items). Each item normalized to:
  - `url: str`
  - `title: str` ("" if unknown)
  - `content: str` (short snippet/summary if available, else "")
  - `raw_content: str` (only if `include_raw_content=True` and retrievable)
  - Optional: `score: float`, `source: Literal["tavily","jina"]`

### Provider selection (single entry point)

- Factory function resolves backend once at process start:
  - `SEARCH_BACKEND=tavily|jina` (default: `tavily` to avoid breaking examples)
  - Keys read lazily when needed:
    - `TAVILY_API_KEY`
    - `JINA_API_KEY` (optional for s/r.jina.ai; include if required by rate limits)

### Files and structure

- `src/deepagents/search/__init__.py`
  - exports: `SearchProvider`, `get_search_provider_from_env()`
- `src/deepagents/search/base.py`
  - `class SearchProvider(Protocol/ABC)` – method signature above
- `src/deepagents/search/factory.py`
  - `get_search_provider_from_env()` -> instance of TavilyProvider or JinaProvider
- `src/deepagents/search/tavily_provider.py`
  - Thin wrapper around `tavily.TavilyClient.search(...)`
  - Maps response to normalized result items
- `src/deepagents/search/jina_provider.py`
  - Discovery via `s.jina.ai` (SERP)
  - Content via `r.jina.ai` (reader proxy)
  - Normalization + domain filtering + optional hydration

### Jina provider behavior

- Discovery (initial search):
  - Endpoint: `https://s.jina.ai/search?q=<query>&topn=<max_results>` (fallback: `https://s.jina.ai/<url-encoded-query>`, slice locally)
  - Headers: include `Authorization: Bearer <JINA_API_KEY>` if present
  - Response handling: tolerate schema variants (`results`/`data`/`items`). Extract `{url, title, snippet}`
- Domain filtering:
  - If `include_domains` specified: post-filter by `urlparse(url).hostname` containment (strict). As an optional optimization, prefix query with `site:` operators; but do not rely on operator support.
- Raw content hydration:
  - If `include_raw_content=True`: for each URL, fetch `https://r.jina.ai/<original-url>`
  - Treat response as text; attach to `raw_content`
  - Title fallback: keep discovery title; do not attempt to parse from reader response
- Timeouts/retries:
  - Use `httpx` (sync) with short timeouts (e.g., connect=5s, read=20s), retry up to 2 times on 5xx/timeouts
- Concurrency:
  - Optional limited parallelism for reader fetches (e.g., ThreadPool with cap `SEARCH_FETCH_CONCURRENCY`, default 4)
- Errors:
  - On discovery failure: return `{"results": []}`
  - On per-URL reader failure: keep item without `raw_content`

### Tavily provider behavior (reference)

- Call `tavily_client.search(query, max_results, include_raw_content, include_domains, topic)`
- Map to normalized result shape; ensure keys: `url`, `title`, `content or raw_content`

### Integration point (examples)

- In `examples/research/wine_agent.py`, swap direct Tavily usage with provider:
  - Initialize once: `provider = get_search_provider_from_env()`
  - Replace the single `tavily_client.search(...)` call with `provider.search(...)`
  - Keep all caps/caching logic and message formatting unchanged

### Configuration (env)

- `SEARCH_BACKEND` = `tavily` | `jina` (default `tavily`)
- `TAVILY_API_KEY` (if using Tavily)
- `JINA_API_KEY` (optional; add header if present)
- `SEARCH_FETCH_CONCURRENCY` (default `4`)
- `SEARCH_HTTP_TIMEOUT_CONNECT` (default `5`), `SEARCH_HTTP_TIMEOUT_READ` (default `20`)

### Testing plan

- Unit tests (HTTP mocked):
  - Jina discovery mapping -> normalized items
  - Domain filtering correctness
  - Reader hydration populates `raw_content`
  - Parity contract: provider output consumed by `wine_agent.internet_search` caching path (no code changes needed beyond call site)
- E2E smoke with recorded fixtures to validate identical downstream behavior (URLs cached, caps obeyed)

### Security and telemetry

- Never log API keys; surface minimal debug lines gated by `WINE_SEARCH_DEBUG`
- Respect robots via r.jina.ai proxy; avoid aggressive concurrency

### Minimal usage example

```python
from deepagents.search import get_search_provider_from_env

provider = get_search_provider_from_env()
docs = provider.search(
    query="site:wine-searcher.com Viura 2022 tasting notes",
    max_results=5,
    include_raw_content=True,
    include_domains=["wine-searcher.com", "winefolly.com"],
)
```

### Migration notes

- No change to cache file format or paths in `wine_agent.py`
- README: add a short snippet noting `SEARCH_BACKEND=jina` option
