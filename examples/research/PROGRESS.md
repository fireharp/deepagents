## TS: 2025-08-24 15:35:00 UTC

## PROBLEM: langgraph dev failed with ModuleNotFoundError for deepagents/examples

## WHAT WAS DONE: Created root uv venv; installed package editable and example deps; fixed import in wine_agent.py to use local module path (from wine_models import ...); started dev server from examples/research with .env

MEMO: Run from repo root venv; examples use langgraph.json in examples/research; ensure TAVILY_API_KEY in .env

## TS: [2025-08-24 17:50:26 CEST]

## PROBLEM: Pydantic json schema error for InjectedState in tools

## WHAT WAS DONE: Switched tool params in wine_agent.py to Annotated[DeepAgentState, InjectedState] and Annotated[str, InjectedToolCallId]. Import test for research_agent.py and wine_agent.py passes; dev server starts.

MEMO: If shell prompts about .env, set AUTOENV_ASSUME_YES=1 when running.

## TS: [$(date "+%Y-%m-%d %H:%M:%S %Z")]

## PROBLEM: Duplicate InjectedState annotation in internet_search

## WHAT WAS DONE: Corrected signature to use Annotated[DeepAgentState, InjectedState] and Annotated[str, InjectedToolCallId]; re-import tests pass and dev server starts.

MEMO: Prefer running from repo root venv; use `uv run langgraph dev` from examples/research.

## PROBLEM: Implement wine-specific agent to research and populate all fields with citations

## WHAT WAS DONE: Added preferred-domain search, per-field research subagent, schema guidance, JSON output target, prompt-level caching via write_file/read_file/ls, and auto-caching of Tavily search results in `internet_search` into `.cache/wine_sources/`

MEMO: Use `wine.json` as authoritative output; prioritize wine-searcher, vivino, winefolly, wineenthusiast, jancisrobinson, winespectator, decanter, timatkin, guia.penin.es

## TS: [2025-08-25 00:15:11 CEST]

## PROBLEM: Cache size grew too large across runs

## WHAT WAS DONE: Added per-call (30) cache cap with env override; removed global cap; prompt updated; search tool emits cap stats

## TS: [2025-08-25 00:42:13 CEST]

## PROBLEM: Need a limit on number of external search calls per run

## WHAT WAS DONE: Implemented per-run cap tracked in `.cache/_meta/search_calls.json` with env `WINE_SEARCH_CALLS_PER_RUN` (default 20); prompt updated

## TS: [2025-08-25 01:12:04 CEST]

## PROBLEM: wine-field-researcher hits search cap and fails instead of using cached sources

## WHAT WAS DONE: Updated wine-field-researcher prompt to check cache first with `cache_list_sources()` and `cache_get_source(url)` before external searches; added cache tools to subagent

## TS: [2025-08-25 15:12:02 CEST]

## PROBLEM: Need swappable search providers - single interface for Tavily and Jina (s.jina.ai + r.jina.ai)

## WHAT WAS DONE: Implemented complete search provider system with:

- `src/deepagents/search/` module with unified SearchProvider protocol
- TavilyProvider wrapper maintaining existing functionality
- JinaProvider with s.jina.ai discovery + r.jina.ai content fetching
- Factory function with `SEARCH_BACKEND=tavily|jina` env var (default: tavily)
- Updated wine_agent.py to use provider interface (drop-in replacement)
- Comprehensive test suite (34 tests) covering unit, integration, and error handling
- Added httpx and tavily-python dependencies to pyproject.toml

MEMO: Use `SEARCH_BACKEND=jina` to switch providers. All caching/caps logic unchanged. Jina provider supports concurrent content fetching, domain filtering, and graceful fallbacks.

## TS: [2025-09-07 20:56:53 CEST]

## PROBLEM: Need validation step to prevent wasting time on nonsensical wine requests

## WHAT WAS DONE: Implemented Phase 0 wine validation system with:

- **Wine Validator Subagent**: Created `wine-validator` subagent with comprehensive validation logic
- **Validation Rules**: Checks vintage validity (1800-2024), requires producer specificity, validates terminology
- **Phase 0 Integration**: Added validation as mandatory first step in wine research workflow
- **Updated Instructions**: Modified main research instructions to include validation phase before research begins
- **Testing**: Created and ran validation tests confirming proper rejection of invalid requests (future vintages, impossible dates, missing producers)

MEMO: Validation prevents workflow from researching impossible wines like "Bordeaux 1066" or vague requests like "Champagne". Validator provides educational feedback to help users refine requests.

## TS: [2025-09-07 22:22:05 CEST]

## PROBLEM: Wine research workflow was not systematic - agent decided which fields to research rather than following strict schema-based approach

## WHAT WAS DONE: Implemented systematic task-based wine research workflow:

- **Mandatory Task Lists**: Phase 1 now requires creating systematic `write_todos` with ALL wine schema properties (11 fields total)
- **Strict Field Coverage**: Updated instructions to research every field from wine schema without exception
- **Required vs Optional Fields**: Clear categorization of core fields (normalized_name, producer, region, appellation, vintage, grapes) vs additional fields (fermentation, aging, notes, alcohol_by_volume, soil_type)
- **Field Research Mapping**: Detailed keyword mapping for each field to ensure consistent and thorough research
- **Task Management Integration**: Proper use of todo system with in_progress/completed status tracking
- **Systematic Workflow**: Phase 2 now works through task list systematically rather than ad-hoc field selection

MEMO: Workflow now guarantees complete coverage of all wine properties. No more missed fields or inconsistent research depth. Agent must create and follow task list for every wine research request.

## TS: [2025-08-26 16:30:26 CEST]

## PROBLEM: Agent only finding one source despite Jina returning multiple results; domain filtering too restrictive for fermentation details

## WHAT WAS DONE:

- **Root cause analysis**: Domain filtering excluded vinissimus.co.uk which contained detailed fermentation info ("fermented in small vats with 30% full clusters and indigenous yeasts and matured in concrete egg for 14 months")
- **Expanded domain list**: Added vinissimus.com/co.uk, ivanwines.com, cellartracker.com, wineanorak.com, erobertparker.com, jamessuckling.com
- **Implemented progressive search strategy**: 4-tier approach in wine-field-researcher:
  - TIER 1: Cache-first (existing sources)
  - TIER 2: Restricted domain search (preferred wine sources)
  - TIER 3: Unrestricted search (unrestricted=True parameter)
  - TIER 4: Fallback queries (general wine knowledge)
- **Enhanced internet_search tool**: Added unrestricted=True parameter to bypass domain filtering
- **Verified functionality**: Restricted search (0 results) vs unrestricted (3 results including Vinissimus with fermentation data)

MEMO: Progressive search ensures comprehensive coverage - starts with quality sources, falls back to broader search when needed. Jina provider working perfectly; issue was search strategy, not provider.

## TS: 2025-09-07 21:07:02 CEST

## PROBLEM: Need to extract cache files from LangGraph Docker container for testing

## WHAT WAS DONE: Investigated Docker container (faa9ff7601b7) and found that "cache files" are actually real-time Jina AI HTTP requests, not persistent disk files. Created test_data directory with documentation of findings and wine URLs being processed.

MEMO: The wine data is fetched live via Jina AI APIs (r.jina.ai and s.jina.ai). For tests, consider intercepting responses or using the same endpoints to fetch fresh data.

## TS: 2025-09-07 21:35:03 CEST

## PROBLEM: Test Qdrant integration with example state data for chunking and retrieval validation

## WHAT WAS DONE: Added headless Qdrant test scripts with graceful error handling:

- **Created `ingest_qdrant.py`**: Parses `.cache/wine_sources/*.txt` from state files or filesystem; computes deterministic IDs; embeds with OpenAI; upserts to Qdrant collection
- **Created `query_qdrant.py`**: Semantic search with OpenAI embeddings; returns structured JSON with scores and metadata
- **Updated `requirements.txt`**: Added qdrant-client, langchain-openai, tiktoken; installed via uv
- **Enhanced error handling**: Scripts gracefully handle missing env vars, connection failures, and API errors without crashes
- **Tested with example state**: Successfully parsed 11 cached docs from `.agents/docs/files_state_example/state.md`; graceful failure on Qdrant 404 (endpoint issue, not code issue)

MEMO: Scripts support both `QDRANT_URL` and `QDRANT_API_ENDPOINT` env vars. Ready for real Qdrant testing when endpoint is available. Test queries: "alcohol", "fermentation", "tasting notes"

**UPDATE**: Integration now fully working and modularized:

- **Created `src/deepagents/qdrant/` module**: Proper separation with QdrantTools class, CachedDoc model
- **Added wine context filtering**: Auto-derives wine_slug from question.txt; stores in payload; supports --wine filter
- **Updated pyproject.toml**: Added optional `qdrant` dependency group with required libs
- **Refactored examples**: Clean scripts using new module; `requirements.txt` now uses `deepagents[qdrant]`
- **Verified end-to-end**: Successfully ingested 11 docs and retrieved filtered results with wine context

MEMO: Use `pip install deepagents[qdrant]` for Qdrant support. Wine filtering prevents cross-wine confusion in shared collections.

## TS: 2025-09-07 22:43:50 CEST

## PROBLEM: Integrate Qdrant tools with existing queue-run (task) system for seamless vector database operations

## WHAT WAS DONE: Fully integrated Qdrant with DeepAgents task system:

- **Moved tools to proper location**: Created `src/deepagents/qdrant/tools.py` with LangGraph-compatible tools following same patterns as core tools
- **Integrated with wine agent**: Added conditional Qdrant import with graceful fallback; tools available when `deepagents[qdrant]` installed
- **Created Qdrant sub-agent**: Added `qdrant-agent` subagent for specialized vector database operations via task system
- **Updated agent creation**: Conditionally adds Qdrant tools and subagent based on availability
- **Added proper Command returns**: Tools return LangGraph Command objects with ToolMessage updates for proper agent integration
- **Created integration test**: `test_qdrant_integration.py` verifies imports, agent integration, and configuration detection
- **Updated documentation**: Added Qdrant tools to research instructions and usage examples

**Key Integration Points:**

- Use `task` tool with `qdrant-agent` for vector operations
- Direct tool access: `qdrant_sync_cache`, `qdrant_retrieve`, `qdrant_inspect`
- Graceful degradation when Qdrant not configured
- Follows existing DeepAgents patterns for tool integration

MEMO: Qdrant now fully integrated with queue-run system. Use either direct tools or `task` with `qdrant-agent` subagent for vector database operations. Tools handle missing configuration gracefully.

## TS: 2025-09-07 23:06:54 CEST

## PROBLEM: Qdrant not being used as first search option; need automatic chunking during caching for better vector retrieval

## WHAT WAS DONE: Implemented Qdrant-first search strategy with automatic chunking:

- **Added Tier 0 Qdrant Search**: Modified wine-field-researcher to use `qdrant_retrieve()` as first search tier before cache/internet search
- **Automatic Chunking Integration**: Built chunking directly into the caching mechanism in `internet_search` tool
- **Smart Chunking Strategy**: Implemented `_chunk_content()` with paragraph-first splitting, then sentence-level for large chunks (1000 char max, 100 char overlap)
- **Auto-sync to Qdrant**: Added `_auto_chunk_and_sync()` function that automatically chunks and stores content in "wine_chunks" collection when caching sources
- **Enhanced Search Workflow**: Updated progressive search strategy from 4 tiers to 5 tiers with Qdrant vector search as priority
- **Conditional Tool Integration**: Added Qdrant tools to wine-field-researcher subagent when available
- **Silent Failure**: Chunking/sync failures don't break main caching flow - graceful degradation

**New Search Flow:**

1. **Tier 0**: Qdrant vector search across chunked documents (`wine_chunks` collection)
2. **Tier 1**: Local cache search
3. **Tier 2**: Restricted domain internet search
4. **Tier 3**: Unrestricted internet search
5. **Tier 4**: Fallback general queries

**Chunking Details:**

- Splits by paragraphs first, then by sentences if needed
- 1000 character chunks with 100 character overlap
- Stores chunks with metadata: parent_url, chunk_index, wine context
- Uses deterministic IDs for deduplication

MEMO: Every cached source is now automatically chunked and stored in Qdrant for semantic search. Wine research starts with vector search across all previously cached content, making subsequent research much more efficient.

## TS: 2025-09-07 23:31:08 CEST

## PROBLEM: Jina provider tests failing (empty results, missing fallback, incorrect call counts)

## WHAT WAS DONE: Updated `JinaProvider._discover_urls` to try structured API first and fall back to simple URL; relaxed content-type reliance; added text parsing fallback. Re-ran tests: all search and export tests pass.

MEMO: Provider now robust to schema/content-type variants; domain filtering and raw content hydration covered by tests.
