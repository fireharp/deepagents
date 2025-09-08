## Qdrant integration spec (examples/research)

### Goals

- **Persist cached sources**: Push `.cache/wine_sources/*.txt` into a Qdrant collection for cross-run reuse.
- **Retrieve**: Provide a tool to query Qdrant for top-k semantically similar snippets.
- **Non-invasive**: Confine changes to `examples/research/*`; no core package API changes.
- **Non-interactive**: All commands and tools work headless (CI-friendly).

### Non-goals

- Document splitting, chunking strategies beyond whole-file body.
- Hybrid BM25 or rerankers.
- Changing default example agent behavior if Qdrant env is not configured.

### Data model

- Cached file format (first lines are headers written by the agent):
  - `URL: <url>`
  - `Title: <title>`
  - `Fetched: <ISO-8601 UTC>`
  - blank line, then raw page text used for extraction.
- Parse into a document with:
  - `id`: `sha1(url + fetched)` if both exist, else `sha1(content)`
  - `url`, `title`, `site` (from `urlparse(url).netloc`), `fetched_at`, `content`
  - Store `content` as the vectorized text; remaining as metadata, plus `path`.

### Collection

- Default: `tavily_cache` (configurable per call).
- One vector per cached file; no explicit payload schema enforcement.

### Embeddings

- OpenAI embeddings via `langchain_openai.OpenAIEmbeddings`.
- Default model: `text-embedding-3-small` (override with `OPENAI_EMBED_MODEL`).

### Env vars (required if using Qdrant)

- `QDRANT_URL` (e.g., `https://<cluster>.qdrant.io:6333`)
- `QDRANT_API_KEY`
- `OPENAI_API_KEY` (for embeddings)
- `OPENAI_EMBED_MODEL` (optional; default as above)

### Dependencies (examples only)

- Add to `examples/research/requirements.txt`:
  - `qdrant-client`
  - `langchain-community`
  - `tiktoken`

### Tools API (added to examples/research/wine_agent.py)

```python
def qdrant_sync_cache(collection_name: str = "tavily_cache") -> str
"""Upsert all in-memory `.cache/wine_sources/*.txt` docs into Qdrant.
Returns a short summary string (e.g., count and collection name).
If Qdrant env/deps missing, return an explanatory message; do not throw."""

def qdrant_retrieve(query: str, k: int = 5, collection_name: str = "tavily_cache") -> list[dict]
"""Similarity search in Qdrant. Returns list of dicts with
url, title, site, fetched_at, doc_id, score, content. On error, returns
[{"error": <message>}], not exceptions."""
```

### Ingestion script (examples/research/ingest_qdrant.py)

- Non-interactive CLI to ingest from disk (default `INGEST_DIR=.cache/wine_sources`).
- Reads files, parses headers, computes `id`, upserts into `QDRANT_COLLECTION` (default `tavily_cache`).
- Uses `QDRANT_URL`, `QDRANT_API_KEY`, `OPENAI_API_KEY`, `OPENAI_EMBED_MODEL`.

### Integration points

- Keep existing Tavily search and in-memory caching as-is.
- Expose two new tools to the agent: `qdrant_sync_cache`, `qdrant_retrieve`.
- Mention these tools in `research_instructions` under tools section (optional, not blocking).

### Error handling

- If Qdrant env vars or deps are missing, tools should return a clear message and not raise.
- Upsert should be idempotent via deterministic doc `id`.
- Retrieval should never crash the agent; bounded `k` with default 5.

### Observability

- For sync: return count of upserted docs; emit a short `ToolMessage` in agent logs if helpful.
- For retrieve: return scores; the agent can choose whether to log or cite.

### Security

- No secrets in code; rely on env vars.
- Do not print API keys. Keep logs minimal.

### Testing strategy

- Unit (no Qdrant):
  - Parser correctness for header extraction and id generation.
  - `_slug_from_url` behavior used by cache.
- Smoke (requires Qdrant creds; optional):
  - Ingest 1-2 docs, retrieve with a simple query, validate non-empty results.
- All tests must be non-interactive.

### Commands (non-interactive)

```bash
# Install example deps
uv pip install -r examples/research/requirements.txt

# Optional: verify Qdrant connectivity
QDRANT_URL=... QDRANT_API_KEY=... \
uv run python -c "from qdrant_client import QdrantClient; import os; c=QdrantClient(url=os.environ['QDRANT_URL'], api_key=os.environ['QDRANT_API_KEY']); print(c.get_collections())"

# Ingest from disk (if you persist cache to FS)
QDRANT_URL=... QDRANT_API_KEY=... OPENAI_API_KEY=... \
uv run python examples/research/ingest_qdrant.py
```

### Rollout

- Add-only changes to examples; safe to merge without Qdrant env.
- Feature is dormant unless env vars are present or tools are called.

### Risks / follow-ups

- Embedding costs and rate limits; consider batching, caching embeddings.
- Consider document splitting and hybrid search if recall is insufficient.
- Per-collection cleanup/TTL policy (not in scope here).

### Acceptance criteria

- Tools import and are callable without raising when env not set (graceful no-op with message).
- With env set and deps installed, sync pushes cached docs; retrieve returns scored results.
- Ingestion script ingests files and reports count.
