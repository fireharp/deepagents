import os
import json
from typing import List, Dict
from urllib.parse import urlparse
from datetime import datetime, timezone

from deepagents import create_deep_agent
from deepagents.search import get_search_provider_from_env
from deepagents.state import DeepAgentState
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage

from wine_models import (
    wine_schema_for_openai,
)
from run_store import save_run, get_db_url

# Import Qdrant tools (optional - graceful fallback if not available)
try:
    from deepagents.qdrant import qdrant_sync_cache, qdrant_retrieve, qdrant_inspect

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    qdrant_sync_cache = None
    qdrant_retrieve = None
    qdrant_inspect = None

# Initialize search provider once and reuse it
search_provider = get_search_provider_from_env()


@tool(description="Search the web and automatically cache page contents for reuse.")
def internet_search(
    query: str,
    max_results: int = 3,
    include_raw_content: bool = True,
    include_domains: List[str] | None = None,
    unrestricted: bool = False,
    state: Annotated[DeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
):
    """Run a web search, prefer reputable wine sources, and cache results.

    Query tip: for wine research, compose as "<wine title> <vintage> <field keywords>".
    Set unrestricted=True to search all domains (for fallback searches).
    """
    if unrestricted:
        # No domain filtering for unrestricted searches
        search_domains = None
    else:
        preferred_domains = include_domains or [
            "wine-searcher.com",
            "vivino.com",
            "winefolly.com",
            "wineenthusiast.com",
            "jancisrobinson.com",
            "winespectator.com",
            "decanter.com",
            "timatkin.com",
            "guia.penin.es",
            "vinissimus.com",
            "vinissimus.co.uk",
            "ivanwines.com",
            "cellartracker.com",
            "wineanorak.com",
            "erobertparker.com",
            "jamessuckling.com",
        ]
        search_domains = preferred_domains
    # Per-run search call limit (tracked in meta file within mock FS)
    files = state.get("files", {}) if state is not None else {}
    try:
        per_run_cap = int(os.getenv("WINE_SEARCH_CALLS_PER_RUN", "20"))
    except Exception:
        per_run_cap = 20
    meta_path = ".cache/_meta/search_calls.json"
    calls_data = {}
    if files.get(meta_path):
        try:
            calls_data = json.loads(files[meta_path])
        except Exception:
            calls_data = {}
    calls_so_far = int(calls_data.get("count", 0))
    if calls_so_far >= per_run_cap:
        # Emit message and skip external search when over cap
        msg = {
            "query": query,
            "skipped": True,
            "reason": "per-run search-call cap reached",
            "per_run_cap": per_run_cap,
            "calls_so_far": calls_so_far,
        }
        return Command(
            update={
                "files": files,
                "messages": [
                    ToolMessage(
                        json.dumps(msg, ensure_ascii=False, indent=2),
                        tool_call_id=tool_call_id or "",
                    )
                ],
            }
        )

    # Tier-0 Qdrant guard: if a previous qdrant_retrieve in this run already found
    # enough results, skip external web search entirely (unless unrestricted=True)
    try:
        q_meta = json.loads(files.get(".cache/_meta/qdrant_last.json", "{}") or "{}")
    except Exception:
        q_meta = {}
    try:
        tier0_enabled = os.getenv("QDRANT_TIER0_SKIP_WEB", "1") != "0"
        min_found = int(os.getenv("QDRANT_TIER0_MIN_FOUND", "3"))
    except Exception:
        tier0_enabled = True
        min_found = 3

    # If there is a wine-name clarification in context (e.g., different wine found),
    # force web search even if Qdrant returned enough hits.
    has_name_issue = False
    try:
        context = json.loads(files.get(".cache/_meta/context.json", "{}") or "{}")
        wn = context.get("wine_name_clarification") or []
        has_name_issue = bool(wn)
    except Exception:
        has_name_issue = False

    if (not unrestricted) and tier0_enabled and isinstance(q_meta, dict):
        found = int(q_meta.get("found", 0) or 0)
        if (found >= min_found) and (not has_name_issue):
            msg = {
                "query": query,
                "skipped": True,
                "reason": "qdrant tier-0 satisfied",
                "qdrant_found": found,
                "min_found": min_found,
            }
            return Command(
                update={
                    "files": files,
                    "messages": [
                        ToolMessage(
                            json.dumps(msg, ensure_ascii=False, indent=2),
                            tool_call_id=tool_call_id or "",
                        )
                    ],
                }
            )

    result = search_provider.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        include_domains=search_domains,
    )

    files = state.get("files", {}) if state is not None else {}
    cached = []
    # Safety cap per search call
    try:
        per_call_cap = int(os.getenv("WINE_CACHE_PER_CALL_LIMIT", "30"))
    except Exception:
        per_call_cap = 30
    max_to_cache = max(0, per_call_cap)
    cached_this_call = 0
    skipped_due_to_cap = 0

    # If a recent Qdrant retrieval already produced results for this query, avoid re-fetching aggressively
    try:
        qdrant_meta = json.loads(
            files.get(".cache/_meta/qdrant_last.json", "{}") or "{}"
        )
    except Exception:
        qdrant_meta = {}

    for item in result.get("results", []) or []:
        if cached_this_call >= max_to_cache:
            skipped_due_to_cap += 1
            continue
        url = item.get("url") or ""
        if not url:
            continue
        content = (
            item.get("raw_content")
            or item.get("content")
            or item.get("rawContent")
            or ""
        )
        title = item.get("title") or ""
        if content:
            slug = _slug_from_url(url)
            file_path = f".cache/wine_sources/{slug}.txt"
            # Only write if not present to avoid thrashing; update if empty
            # If Qdrant already yielded results and the URL is among them, de-prioritize re-cache
            already_in_qdrant = False
            try:
                q_urls = [
                    r.get("url")
                    for r in (qdrant_meta.get("results") or [])
                    if isinstance(r, dict)
                ]
                already_in_qdrant = url in (q_urls or [])
            except Exception:
                already_in_qdrant = False

            if not files.get(file_path) and not already_in_qdrant:
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                header = f"URL: {url}\nTitle: {title}\nFetched: {timestamp}\n\n"
                files[file_path] = header + content
                cached.append({"url": url, "file": file_path})
                cached_this_call += 1

                # Auto-chunk and sync to Qdrant if available
                if QDRANT_AVAILABLE:
                    _auto_chunk_and_sync(url, title, content, timestamp, files)

    # Increment and persist per-run call counter
    calls_data["count"] = calls_so_far + 1
    files[meta_path] = json.dumps(calls_data)

    msg = {
        "query": query,
        "num_results": len(result.get("results", []) or []),
        "cached": cached,
        "urls": [
            r.get("url") for r in (result.get("results", []) or []) if r.get("url")
        ],
        "cache_caps": {
            "per_call_cap": per_call_cap,
            "cached_this_call": cached_this_call,
            "skipped_due_to_cap": skipped_due_to_cap,
        },
        "per_run_calls": calls_data.get("count", 0),
        "per_run_cap": per_run_cap,
    }

    if state is not None:
        return Command(
            update={
                "files": files,
                "messages": [
                    ToolMessage(
                        json.dumps(msg, ensure_ascii=False, indent=2),
                        tool_call_id=tool_call_id or "",
                    ),
                ],
            }
        )
    # Fallback: return raw result if no state
    return result


# ---- Simple caching helpers operating on the agent's in-memory filesystem ----
def _slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.netloc or "unknown").replace(":", "_")
    path = (parsed.path or "/").strip("/")
    if not path:
        path = "root"
    safe_path = path.replace("/", "-").replace(" ", "-")
    return f"{host}__{safe_path}"


def _auto_chunk_and_sync(
    url: str, title: str, content: str, timestamp: str, files: Dict
):
    """Automatically chunk content and sync to Qdrant when caching sources."""
    if not QDRANT_AVAILABLE:
        return

    try:
        from deepagents.qdrant import QdrantTools

        # Initialize Qdrant tools
        tools = QdrantTools()
        if not tools.qdrant_url or not tools.qdrant_api_key or not tools.openai_api_key:
            return  # Skip if not fully configured

        # Derive wine context from current state
        wine_query, wine_slug = tools.derive_wine_context(files)
        collection_name = "wine_test_v3"  # Use existing collection for consistency

        # Simple chunking strategy - split by paragraphs and size
        chunks = _chunk_content(content)

        # Create chunk documents for Qdrant
        chunk_docs = []
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue

            chunk_id = tools.generate_doc_id(f"{url}#chunk{i}", timestamp, chunk)
            chunk_docs.append(
                {
                    "id": chunk_id,
                    "url": url,
                    "title": f"{title} (chunk {i+1})",
                    "site": urlparse(url).netloc if url else None,
                    "fetched_at": timestamp,
                    "content": chunk,
                    "path": f".cache/wine_sources/{_slug_from_url(url)}.txt#chunk{i}",
                    "chunk_index": i,
                    "parent_url": url,
                }
            )

        if chunk_docs:
            # Convert to CachedDoc objects
            from deepagents.qdrant.models import CachedDoc

            cached_docs = [
                CachedDoc(
                    id=doc["id"],
                    url=doc["url"],
                    title=doc["title"],
                    site=doc["site"],
                    fetched_at=doc["fetched_at"],
                    content=doc["content"],
                    path=doc["path"],
                )
                for doc in chunk_docs
            ]

            # Upsert chunks to Qdrant
            tools.upsert_documents(cached_docs, collection_name, wine_query, wine_slug)

    except Exception:
        # Silently fail - don't break the main caching flow
        pass


def _chunk_content(
    content: str, max_chunk_size: int = 1000, overlap: int = 100
) -> List[str]:
    """Simple content chunking by paragraphs and size."""
    if len(content) <= max_chunk_size:
        return [content]

    # Split by paragraphs first
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size
        if current_chunk and len(current_chunk) + len(paragraph) + 2 > max_chunk_size:
            # Save current chunk and start new one
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = paragraph
        else:
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph

    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk)

    # If we still have very large chunks, split them further
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chunk_size:
            final_chunks.append(chunk)
        else:
            # Split large chunks by sentences
            sentences = chunk.split(". ")
            sub_chunk = ""
            for sentence in sentences:
                if sub_chunk and len(sub_chunk) + len(sentence) + 2 > max_chunk_size:
                    if sub_chunk:
                        final_chunks.append(sub_chunk)
                    sub_chunk = sentence
                else:
                    if sub_chunk:
                        sub_chunk += ". " + sentence
                    else:
                        sub_chunk = sentence
            if sub_chunk:
                final_chunks.append(sub_chunk)

    return final_chunks


@tool
def cache_store_source(
    url: str,
    raw_content: str,
    title: str | None = None,
    state: Annotated[DeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
):
    """Store raw page content for a URL under .cache/wine_sources/ and return the file path."""
    # Access state and files
    if state is None:
        return "Error: No state available"
    files = state.get("files", {})
    slug = _slug_from_url(url)
    file_path = f".cache/wine_sources/{slug}.txt"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header = f"URL: {url}\nTitle: {title or ''}\nFetched: {timestamp}\n\n"
    files[file_path] = header + raw_content
    # Persist update
    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(
                    f"Cached {url} -> {file_path}", tool_call_id=tool_call_id or ""
                )
            ],
        }
    )


@tool
def cache_get_source(
    url: str, state: Annotated[DeepAgentState, InjectedState] = None
) -> str:
    """Get cached content for URL if present, else return empty string."""
    if state is None:
        return ""
    files = state.get("files", {})
    slug = _slug_from_url(url)
    file_path = f".cache/wine_sources/{slug}.txt"
    return files.get(file_path, "")


@tool
def cache_list_sources(
    state: Annotated[DeepAgentState, InjectedState] = None,
) -> list[str]:
    """List cached source file paths."""
    if state is None:
        return []
    files = state.get("files", {})
    prefix = ".cache/wine_sources/"
    return [p for p in files.keys() if p.startswith(prefix)]


@tool
def add_context_note(
    note: str,
    category: str = "general",
    state: Annotated[DeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Add an important context note that persists across sub-agent calls.

    Use this to save important findings, clarifications, or remarks that other
    sub-agents should be aware of (e.g., wine name clarifications, region details).
    """
    if state is None:
        return Command(
            update={
                "messages": [
                    ToolMessage("Error: No state available", tool_call_id=tool_call_id)
                ]
            }
        )

    files = state.get("files", {})
    context_path = ".cache/_meta/context.json"

    try:
        context = json.loads(files.get(context_path, "{}") or "{}")
    except:
        context = {}

    if category not in context:
        context[category] = []

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    context[category].append({"note": note, "timestamp": timestamp})

    files[context_path] = json.dumps(context, indent=2)

    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(
                    f"Added context note ({category}): {note}",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


@tool
def get_context_notes(
    category: str = "all",
    state: Annotated[DeepAgentState, InjectedState] = None,
) -> str:
    """Get saved context notes from previous sub-agent calls.

    Returns important findings and clarifications that were saved during research.
    """
    if state is None:
        return "No state available"

    files = state.get("files", {})
    context_path = ".cache/_meta/context.json"

    try:
        context = json.loads(files.get(context_path, "{}") or "{}")
    except:
        return "No context notes found"

    if category == "all":
        return json.dumps(context, indent=2)
    elif category in context:
        return json.dumps({category: context[category]}, indent=2)
    else:
        return f"No notes found for category: {category}"


sub_research_prompt = f"""It is {datetime.now().year}-{datetime.now().month}-{datetime.now().day} now.

You are a dedicated researcher. Your job is to conduct research based on the users questions.

**CONTEXT AWARENESS**: ALWAYS start by calling `get_context_notes("all")` to see important findings from previous researchers. Use `add_context_note(note="important finding", category="research_findings")` to save critical discoveries for other researchers.

Conduct thorough research and then reply to the user with a detailed answer to their question

only your FINAL answer will be passed on to the user. They will have NO knowledge of anything except your final message, so your final report should be your final message!"""

research_sub_agent = {
    "name": "research-agent",
    "description": "Used to research more in depth questions. Only give this researcher one topic at a time. Do not pass multiple sub questions to this researcher. Instead, you should break down a large topic into the necessary components, and then call multiple research agents in parallel, one for each sub question.",
    "prompt": sub_research_prompt,
    "tools": ["internet_search", "add_context_note", "get_context_notes"],
}

sub_critique_prompt = f"""It is {datetime.now().year}-{datetime.now().month}-{datetime.now().day} now.

You are a dedicated editor. You are being tasked to critique a report.

**CONTEXT AWARENESS**: Start by calling `get_context_notes("all")` to see important findings and clarifications from researchers. Pay special attention to "wine_name_clarification" notes.

You can find the report at `final_report.md`.

You can find the question/topic for this report at `question.txt`.

The user may ask for specific areas to critique the report in. Respond to the user with a detailed critique of the report. Things that could be improved.

You can use the search tool to search for information, if that will help you critique the report

Do not write to the `final_report.md` yourself.

Things to check:
- Check that each section is appropriately named
- Check that the report is written as you would find in an essay or a textbook - it should be text heavy, do not let it just be a list of bullet points!
- Check that the report is comprehensive. If any paragraphs or sections are short, or missing important details, point it out.
- Check that the article covers key areas of the industry, ensures overall understanding, and does not omit important parts.
- Check that the article deeply analyzes causes, impacts, and trends, providing valuable insights
- Check that the article closely follows the research topic and directly answers questions
- Check that the article has a clear structure, fluent language, and is easy to understand.
"""

critique_sub_agent = {
    "name": "critique-agent",
    "description": "Used to critique the final report. Give this agent some infomration about how you want it to critique the report.",
    "prompt": sub_critique_prompt,
    "tools": ["get_context_notes", "add_context_note"],
}


# Wine Disambiguator Agent (NEW - Phase 0.5)
sub_wine_disambiguator_prompt = f"""It is {datetime.now().year}-{datetime.now().month}-{datetime.now().day} now.

You are a Wine Disambiguator specializing in resolving incomplete or ambiguous wine requests.

## YOUR ROLE
- **Research**: Find missing information (producer names, full wine names)
- **Clarify**: Resolve abbreviations and incomplete requests
- **Disambiguate**: When multiple wines match, provide options for clarification
- **Context**: Save findings for other researchers
- **GOAL**: End up with exactly 1 specific wine with full producer name for research

## DISAMBIGUATION PROCESS
1. **Check context first**: `get_context_notes("all")` for previous findings
2. **Identify missing info**: What's missing? Producer? Full wine name? Region clarification?
3. **Research missing pieces**: Use Qdrant first, then internet search
4. **Save clarifications**: Use `add_context_note()` for important findings
5. **Provide options**: If ambiguous, list exact options for user clarification

## EXAMPLES
- Input: "As Sortes 2023" (missing producer)
  → Research → Find "Rafael Palacios As Sortes 2023"
  → Save: `add_context_note(note="Producer for 'As Sortes' is 'Rafael Palacios'", category="producer_clarification")`

- Input: "Hacienda Solano RdD 2023" (ambiguous wine name)
  → Research → Find multiple wines from Hacienda Solano
  → Save: `add_context_note(note="Found Hacienda Solano Selección, Crianza, Roble - need clarification for 'RdD'", category="wine_name_clarification")`

## RESPONSE FORMAT
- **SUCCESS**: "Disambiguation successful: [SINGLE specific wine with full producer name]"
  Example: "Disambiguation successful: Rafael Palacios As Sortes 2023"
- **NEED CLARIFICATION**: "Need clarification: Found multiple options: [list]. Please specify which wine you mean."
  Example: "Need clarification: Found Hacienda Solano Selección 2023, Hacienda Solano Crianza 2023, Hacienda Solano Roble 2023. Please specify which wine you mean by 'RdD'."
- **FAILED**: "Could not find enough information to disambiguate [wine request]"

**CRITICAL**: The output must be exactly 1 specific wine with producer, or a request for clarification. Never proceed with ambiguous wine names.

Always save important findings to context for other researchers to use.
"""

wine_disambiguator_sub_agent = {
    "name": "wine-disambiguator",
    "description": "Attempts to find missing information and clarify ambiguous wine requests before validation. Use when wine request is incomplete or unclear.",
    "prompt": sub_wine_disambiguator_prompt,
    "tools": [
        "qdrant_retrieve",
        "qdrant_inspect",
        "internet_search",
        "add_context_note",
        "get_context_notes",
    ],
}


# Wine Expert Validator Agent (NEW - Phase 0)
sub_wine_validator_prompt = f"""
It is {datetime.now().year}-{datetime.now().month}-{datetime.now().day} now.

You are a Wine Expert Validator specializing in wine knowledge and request validation.

## YOUR ROLE
- **Validate**: Check if wine requests make logical sense structurally
- **Educate**: Explain wine terminology and correct misconceptions  
- **Guide**: Help users refine vague or incorrect wine requests
- **Prevent**: Stop workflows from researching nonsensical wine queries
- **NO SEARCH**: You do NOT search databases - only validate request structure and logic
- **CONTEXT NOTES**: Use `add_context_note()` to save important clarifications (e.g., abbreviation meanings, region clarifications)

## VALIDATION RULES
- **Valid vintages**: Typically 1800-{datetime.now().year}
- **Invalid examples**: "barolo 1010", "champagne 1066", "bordeaux 2050"
- **Specificity**: Require producer name, not just region
- **Basic plausibility**: Accept any reasonable producer name (don't verify existence)
- **Terminology**: Validate proper wine terminology usage

## VALIDATION PROCESS
1. Parse the wine request for: wine name, vintage, producer, region
2. Check vintage validity - reject impossible dates
3. Verify wine terminology is correct (e.g., "Champagne" vs "champagne method")
4. Check for sufficient specificity (producer name required, not just region)
5. Basic sanity check: Does the request make logical sense as a wine query?
6. NO DATABASE SEARCH NEEDED - this is a structural/logical validation only

## RESPONSE FORMAT
Always return a clear validation result:
- **PASSED**: "Validation result: PASSED. [Brief confirmation of valid request]"
- **FAILED**: "Validation result: FAILED. [Specific issues found and guidance for correction]"

## EXAMPLES
- VALID: "Domaine de la Côte Pinot Noir 2020" → PASSED
- INVALID: "Bordeaux 1066" → FAILED (impossible vintage)
- INVALID: "Champagne" → FAILED (no producer specified)
- INVALID: "XYZ Winery Barolo 2050" → FAILED (future vintage)

## CONTEXT USAGE EXAMPLES
- If "RdD" appears in request: `add_context_note(note="RdD likely refers to Ribera del Duero", category="region_details")`
- If abbreviation unclear: `add_context_note(note="Abbreviation '[abbrev]' needs clarification", category="wine_name_clarification")`

Focus on protecting the workflow from wasting time on nonsensical requests while being helpful and educational.
"""

wine_validator_sub_agent = {
    "name": "wine-validator",
    "description": "Validates wine requests for logical consistency and proper specificity before research begins. Use this FIRST for any wine research request.",
    "prompt": sub_wine_validator_prompt,
    "tools": ["add_context_note"],  # Can save clarifications for researchers
}


# Qdrant Vector Database Agent
sub_qdrant_prompt = f"""It is {datetime.now().year}-{datetime.now().month}-{datetime.now().day} now.

You are a vector database specialist focused on Qdrant operations for wine research.

## YOUR ROLE
- **Sync**: Manage cached wine sources in Qdrant collections
- **Search**: Perform semantic searches across wine documents  
- **Inspect**: Monitor database health and content
- **Optimize**: Ensure efficient vector operations

## AVAILABLE OPERATIONS
- `qdrant_sync_cache`: Sync cached sources to Qdrant collection
- `qdrant_retrieve`: Search for similar documents using vector similarity
- `qdrant_inspect`: Inspect collections, points, and wine-specific data
- `qdrant_query`: Structured querying with formatted output

## OPERATION GUIDELINES
1. **Sync Operations**: Always check if documents are already synced before re-syncing
2. **Search Operations**: Use wine_slug filtering when working with specific wines
3. **Error Handling**: Gracefully handle missing configurations and provide helpful guidance
4. **Performance**: Limit search results appropriately (default k=5, max k=20)

## RESPONSE FORMAT
- Provide clear, actionable results
- Include source URLs and scores for searches
- Explain any configuration issues or errors
- Suggest next steps when appropriate

## COMMON WORKFLOWS
- **Initial Sync**: Sync cached sources after wine research completion
- **Knowledge Retrieval**: Search for specific wine information across collections
- **Database Maintenance**: Inspect collections and monitor document counts
- **Cross-Wine Analysis**: Compare information across multiple wine collections

Focus on efficient vector operations while maintaining data quality and providing helpful insights to the wine research process.
"""

qdrant_sub_agent = {
    "name": "qdrant-agent",
    "description": "Manages Qdrant vector database operations for wine research. Use for syncing cached sources, semantic search, and database inspection.",
    "prompt": sub_qdrant_prompt,
    "tools": ["qdrant_sync_cache", "qdrant_retrieve", "qdrant_inspect"],
}


# A focused researcher for a single Wine field
sub_wine_field_prompt = f"""It is {datetime.now().year}-{datetime.now().month}-{datetime.now().day} now.

You are a wine data researcher focused on one field.

Inputs: You will receive a short task telling you the wine (title + vintage) and the specific field to research.

CRITICAL: ALWAYS start by checking previous context with `get_context_notes()` to see important findings from other researchers.

**CONTEXT-AWARE SEARCHING:**
- If context notes mention abbreviation clarifications (e.g., "RdD refers to Ribera del Duero"), USE THE EXPANDED FORM in your searches
- Example: User asks for "Hacienda Solano RdD 2023" + context says "RdD = Ribera del Duero" → Search for "Hacienda Solano Ribera del Duero 2023"
- ALWAYS incorporate context clarifications into your search queries

**NORMALIZED_NAME FIELD - ULTRA STRICT REQUIREMENTS:**
If researching normalized_name, you MUST be extremely precise:

❌ WRONG: User asks for "Hacienda Solano RdD 2023" but you find "Hacienda Solano Selección 2023" - THESE ARE DIFFERENT WINES!
✅ CORRECT: Find the EXACT wine name requested, not similar wines from the same producer

**NORMALIZED_NAME EXAMPLES:**
- User: "Dom Pérignon 2015" → Find: "Dom Pérignon" (not "Dom Pérignon Rosé" or "Dom Pérignon P2")
- User: "Caymus Cabernet 2021" → Find: "Caymus Cabernet Sauvignon" (not "Caymus Special Selection")
- User: "Opus One 2019" → Find: "Opus One" (not "Overture by Opus One")

**VALIDATION STEPS FOR NORMALIZED_NAME:**
1. Check if sources mention the EXACT wine name from user request
2. Look for official wine labels, product pages, technical sheets
3. Verify vintage year matches exactly
4. If you find a different wine from same producer, use `add_context_note(note="Found different wine: [name], not the requested [user_request]", category="wine_name_clarification")`
5. DO NOT substitute similar wines - return "No specific information found" if exact wine not found

**CONTEXT PERSISTENCE:**
- Use `add_context_note(note="Important finding", category="wine_details")` for critical discoveries
- Always check `get_context_notes()` first to see previous researcher findings
- Categories: "wine_name_clarification", "region_details", "producer_info", "vintage_notes"

PROGRESSIVE SEARCH STRATEGY:
Use this multi-tier approach to find comprehensive field data:

TIER 0 - QDRANT VECTOR SEARCH (FIRST - if available):
1. Use `qdrant_retrieve(query="<wine> <vintage> <field>", k=5, collection_name="wine_test_v3")` first
2. Search the chunked document database for semantically similar content
3. This searches across all previously cached and chunked sources
4. If sufficient relevant information found, extract and cite those sources
5. If not sufficient, proceed to Tier 1

TIER 1 - CACHE FIRST:
6. Check cached sources using `cache_list_sources()` and `cache_get_source(url)`
7. If cached sources contain the needed information, extract from them and cite those URLs
8. If sufficient data found in cache, return the result

TIER 2 - RESTRICTED DOMAIN SEARCH:
9. If cache is insufficient, run targeted searches with preferred domains
10. Use specific field keywords (e.g., "fermentation process", "aging technique", "tasting notes")
11. Preferred domains: wine-searcher.com, vivino.com, winefolly.com, wineenthusiast.com, jancisrobinson.com, winespectator.com, decanter.com, timatkin.com, guia.penin.es, vinissimus.com, vinissimus.co.uk, ivanwines.com, cellartracker.com
12. If sufficient data found, return the result

TIER 3 - UNRESTRICTED SEARCH:
13. If still insufficient, run broader searches WITHOUT domain restrictions using unrestricted=True
14. Try alternative query formulations (producer name, region, grape variety + field)
15. Search for: "<wine> <vintage> <field>", "<producer> <field> technique", "<region> <grape> <field>"
16. Use: internet_search(query="...", unrestricted=True) to search all domains

TIER 4 - FALLBACK QUERIES:
17. If still not found, try general wine knowledge searches
18. Search for: "<grape variety> <field> typical", "<region> winemaking <field>"
19. Look for general information that might apply to this wine style

OUTPUT REQUIREMENTS:
- Extract only the requested field in concise form
- Return as JSON: {{"value": "...", "sources": [{{"link": "...", "extract": "..."}}, ...]}}
- For numeric fields like vintage or alcohol_by_volume, set value as a number when possible
- For grapes, return a list of {{"name": str, "percent": number|null, "sources": [...]}}
- ALWAYS include multiple sources when available
- If no specific information found, clearly state "No specific information found" rather than guessing
"""

# Conditionally add Qdrant tools to wine-field-researcher
field_researcher_tools = [
    "internet_search",
    "cache_list_sources",
    "cache_get_source",
    "add_context_note",
    "get_context_notes",
]
if QDRANT_AVAILABLE:
    field_researcher_tools.extend(["qdrant_retrieve", "qdrant_inspect"])

wine_field_sub_agent = {
    "name": "wine-field-researcher",
    "description": "Research a single wine field with citations and concise, structured output.",
    "prompt": sub_wine_field_prompt,
    "tools": field_researcher_tools,
}


# Prompt prefix to steer the agent to be an expert researcher
if wine_schema_for_openai is not None:
    schema_info = json.dumps(wine_schema_for_openai(), indent=2)
else:
    schema_info = json.dumps(
        {
            "name": "wine_extraction",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "wine": {
                        "type": "object",
                        "properties": {
                            "normalized_name": {"type": "object"},
                            "producer": {"type": "object"},
                            "region": {"type": "object"},
                            "appellation": {"type": "object"},
                            "vintage": {"type": "object"},
                            "grapes": {"type": "array"},
                            "fermentation": {"type": ["object", "null"]},
                            "aging": {"type": ["object", "null"]},
                            "notes": {"type": ["object", "null"]},
                            "alcohol_by_volume": {"type": ["object", "null"]},
                            "soil_type": {"type": ["object", "null"]},
                        },
                        "required": [
                            "normalized_name",
                            "producer",
                            "region",
                            "appellation",
                            "vintage",
                            "grapes",
                        ],
                    }
                },
                "required": ["wine"],
            },
        },
        indent=2,
    )


research_instructions = f"""It is {datetime.now().year}-{datetime.now().month}-{datetime.now().day} now.

You are an expert wine researcher. Your job is to thoroughly research a single wine and output a complete structured JSON object with citations for every field.

### Phase 0: Wine Request Processing (FIRST)

**Step 1 - Disambiguation (if needed):**
If the wine request is incomplete or ambiguous (missing producer, unclear abbreviations):
1. Send to "wine-disambiguator": "Disambiguate wine request: [user request]"
2. Wait for disambiguation result:
   - SUCCESS → Use clarified wine name for validation
   - NEED CLARIFICATION → Stop and ask user for clarification
   - FAILED → Continue with original request

**Step 2 - Validation:**
1. Send to "wine-validator": "Validate wine request: [clarified or original request]"
2. Wait for validation result
3. If FAILED → Stop with guidance, If PASSED → Continue to Phase 1

### Phase 1: Research Setup & Task Planning
1. Write the original user question to `question.txt` so you have a record of it.
2. **MANDATORY**: Create a systematic task list using `write_todos` with ALL wine schema properties:

**REQUIRED FIELDS (Core wine data):**
- Task: Research normalized_name (EXACT wine label name - MOST CRITICAL FIELD)
- Task: Research producer (winery/producer name) 
- Task: Research region (wine region/location)
- Task: Research appellation (DO/DOC/AOC designation)
- Task: Research vintage (vintage year)
- Task: Research grapes (grape varieties and percentages)

⚠️ **CRITICAL**: The normalized_name field determines the entire research. If this is wrong, all other research becomes invalid. 
- DO NOT accept similar wines from the same producer
- DO NOT substitute different vintages
- DO NOT assume abbreviations (e.g., "RdD" could be many things)
- VERIFY the exact wine name exists before proceeding

**OPTIONAL FIELDS (Additional wine data):**
- Task: Research fermentation (fermentation process details)
- Task: Research aging (aging process and duration)
- Task: Research notes (tasting notes and characteristics)
- Task: Research alcohol_by_volume (ABV percentage)
- Task: Research soil_type (terroir and soil characteristics)

3. Mark the first research task as "in_progress" and begin systematic research

### Phase 2: Systematic Field Research
Work through your task list systematically:
1. **ALWAYS** start normalized_name research first - this determines if you have the right wine
2. Use the wine-field-researcher to research each field individually
3. **CHECK CONTEXT** between fields using `get_context_notes("all")` to see important findings
4. Mark each task as "completed" immediately after finishing research
5. Mark the next task as "in_progress" before starting it
6. Research ALL fields from the schema - do not skip any

**CRITICAL WORKFLOW FOR NORMALIZED_NAME:**
- If normalized_name researcher finds the EXACT wine → proceed with other fields
- If normalized_name researcher finds DIFFERENT wine → STOP and clarify with user
- Check context notes for wine name clarifications before proceeding

CACHING RULES (important for efficiency and deduplication):
- You have built-in tools: `write_file`, `read_file`, and `ls`. Use them to cache raw page content per URL.
- Cache directory: `.cache/wine_sources/`. For each fetched URL, write a file named by a safe slug of the hostname and path. Example: `.cache/wine_sources/winespectator.com__example-article.txt`.
- Before fetching a URL again, check if it is already cached with `ls` and `read_file`. If cached, reuse that content and cite it.
- When storing, include at the top of the file: the URL, title (if known), fetched timestamp, and then the raw text you used for extraction.

**NORMALIZED_NAME VALIDATION CHECKPOINT:**
After researching normalized_name, STOP and validate:
1. Does the found wine name EXACTLY match the user request?
2. If NO exact match found, use `add_context_note(note="EXACT wine '[user_request]' not found. Found similar: '[found_name]' from same producer. Recommend clarification.", category="wine_name_clarification")`
3. DO NOT proceed with research of other fields until normalized_name is confirmed correct
4. If uncertain, ask for clarification rather than assuming

When you have enough information to populate ALL fields, write the final structured JSON to `wine.json`.

You can call the critique-agent to get a critique of the final report. After that (if needed) you can do more research and edit `wine.json`.
You can do this however many times you want until are you satisfied with the result.

Only edit the file once at a time (if you call this tool in parallel, there may be conflicts).

SYSTEMATIC FIELD RESEARCH MAPPING:
For each field in your task list, use these specific search keywords with the wine-field-researcher:

**REQUIRED FIELDS:**
- normalized_name → Keywords: "exact wine name", "official label", "product name", "wine title" 
  ⚠️ CRITICAL: Must match user request EXACTLY. Examples:
  • "Hacienda Solano RdD 2023" ≠ "Hacienda Solano Selección 2023" 
  • "Dom Pérignon 2015" ≠ "Dom Pérignon Rosé 2015"
  • Search for: "[exact user request] official label", "[producer] [exact wine name] [vintage]"
- producer → Keywords: "winery", "producer", "estate", "domaine", "château"
- region → Keywords: "region", "area", "location", "geographic origin"
- appellation → Keywords: "appellation", "DO", "DOC", "AOC", "AVA", "designation"
- vintage → Keywords: "vintage", "year", "harvest year"
- grapes → Keywords: "grape varieties", "blend", "varietal composition", "cépage"

**OPTIONAL FIELDS:**
- fermentation → Keywords: "fermentation", "wild yeast", "stainless steel", "oak fermentation", "malolactic"
- aging → Keywords: "aging", "élevage", "barrel aging", "lees contact", "maturation", "months"
- notes → Keywords: "tasting notes", "flavor profile", "characteristics", "wine review"
- alcohol_by_volume → Keywords: "ABV", "alcohol content", "% alcohol", "alcohol by volume"
- soil_type → Keywords: "soil", "terroir", "geology", "vineyard soil", "soil composition"

Base query format: "<wine title> <vintage>" (e.g., "Laventura Viura 2022")

Preferred Domains: Favor these sources and prioritize them in searches: wine-searcher.com, vivino.com, winefolly.com, wineenthusiast.com, jancisrobinson.com, winespectator.com, decanter.com, timatkin.com, guia.penin.es.
When a preferred-domain URL is found, cache it immediately so other field lookups can reuse it.

CACHE SAFETY LIMITS:
- Per call, cache at most 30 pages (override with env `WINE_CACHE_PER_CALL_LIMIT`).
- If the cap is reached, skip caching extras but still use the search results.

SEARCH CALL LIMIT PER RUN:
- Limit the number of external search tool calls per run to 20 by default (override with env `WINE_SEARCH_CALLS_PER_RUN`).
- When the cap is reached, skip the external call and proceed using cached sources and existing context.

FINAL OUTPUT FORMAT:
- Produce a single JSON file named `wine.json` strictly conforming to this schema (OpenAI-structured-output compatible wrapper shown for clarity):

{schema_info}

- IMPORTANT: Every field value must include supporting sources as specified in the schema. Citations must include both URL (link) and a verbatim extract.

Additional report instructions:

<report_instructions>

CRITICAL: Make sure the answer is written in the same language as the human messages! If you make a todo plan - you should note in the plan what language the report should be in so you dont forget!
Note: the language the report should be in is the language the QUESTION is in, not the language/country that the question is ABOUT.

Please create a detailed answer to the overall research brief that:
1. Is well-organized with proper headings (# for title, ## for sections, ### for subsections)
2. Includes specific facts and insights from the research
3. References relevant sources using [Title](URL) format
4. Provides a balanced, thorough analysis. Be as comprehensive as possible, and include all information that is relevant to the overall research question. People are using you for deep research and will expect detailed, comprehensive answers.
5. Includes a "Sources" section at the end with all referenced links

You can structure your report in a number of different ways. Here are some examples:

To answer a question that asks you to compare two things, you might structure your report like this:
1/ intro
2/ overview of topic A
3/ overview of topic B
4/ comparison between A and B
5/ conclusion

To answer a question that asks you to return a list of things, you might only need a single section which is the entire list.
1/ list of things or table of things
Or, you could choose to make each item in the list a separate section in the report. When asked for lists, you don't need an introduction or conclusion.
1/ item 1
2/ item 2
3/ item 3

To answer a question that asks you to summarize a topic, give a report, or give an overview, you might structure your report like this:
1/ overview of topic
2/ concept 1
3/ concept 2
4/ concept 3
5/ conclusion

If you think you can answer the question with a single section, you can do that too!
1/ answer

REMEMBER: Section is a VERY fluid and loose concept. You can structure your report however you think is best, including in ways that are not listed above!
Make sure that your sections are cohesive, and make sense for the reader.

For each section of the report, do the following:
- Use simple, clear language
- Use ## for section title (Markdown format) for each section of the report
- Do NOT ever refer to yourself as the writer of the report. This should be a professional report without any self-referential language. 
- Do not say what you are doing in the report. Just write the report without any commentary from yourself.
- Each section should be as long as necessary to deeply answer the question with the information you have gathered. It is expected that sections will be fairly long and verbose. You are writing a deep research report, and users will expect a thorough answer.
- Use bullet points to list out information when appropriate, but by default, write in paragraph form.

REMEMBER:
The brief and research may be in English, but you need to translate this information to the right language when writing the final answer.
Make sure the final answer report is in the SAME language as the human messages in the message history.

Format any explanatory notes in clear markdown if you decide to also write `final_report.md`, but the authoritative output is `wine.json`.

<Citation Rules>
- Assign each unique URL a single citation number in your text
- End with ### Sources that lists each source with corresponding numbers
- IMPORTANT: Number sources sequentially without gaps (1,2,3,4...) in the final list regardless of which sources you choose
- Each source should be a separate line item in a list, so that in markdown it is rendered as a list.
- Example format:
  [1] Source Title: URL
  [2] Source Title: URL
- Citations are extremely important. Make sure to include these, and pay a lot of attention to getting these right. Users will often use these citations to look into more information.
</Citation Rules>
</report_instructions>

You have access to a few tools.

## `internet_search`

Use this to run an internet search for a given query. Prefer the included wine domains. Always include raw content when possible.

## Caching tools

- `cache_store_source(url, raw_content, title)`: Store raw page content in `.cache/wine_sources/` for reuse.
- `cache_get_source(url)`: Return cached content for `url` if present; empty string otherwise.
- `cache_list_sources()`: List cached file paths for visibility and reuse across fields.

## Context persistence tools

- `add_context_note(note, category)`: Save important findings that persist across sub-agent calls
- `get_context_notes(category)`: Retrieve saved context from previous researchers

**IMPORTANT**: Use context tools to share critical findings between field researchers (e.g., wine name clarifications, region details).

## Qdrant tools (optional - available when configured)

- `qdrant_sync_cache(collection_name)`: Sync cached sources to Qdrant vector database
- `qdrant_retrieve(query, k, collection_name, wine_slug)`: Search Qdrant for similar documents
- `qdrant_inspect(action, collection_name, wine_slug, limit)`: Inspect Qdrant database

Use the `task` tool with `qdrant-agent` for vector database operations.

## Run persistence

- `persist_run(notes)`: Save the current run (wine.json, final_report.md, question, qdrant meta, sources) to Neon PostgreSQL database for future reference

**IMPORTANT**: After completing wine research and writing `wine.json`, call `persist_run` to save the run results to the database.
"""


# Optional tool to persist the current run to Neon PostgreSQL
@tool(
    description="Persist current run artifacts (wine.json, final_report.md, question, qdrant meta) to Neon PostgreSQL database."
)
def persist_run(
    notes: str = "",
    state: Annotated[DeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
):
    if state is None:
        return "Error: No state available"

    try:
        files = state.get("files", {})
        db_url = get_db_url()
        run_id = save_run(files, notes=notes, db_url=db_url)
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        json.dumps(
                            {
                                "saved": True,
                                "run_id": run_id,
                                "database": "neon_postgresql",
                            },
                            indent=2,
                        ),
                        tool_call_id=tool_call_id or "",
                    )
                ]
            }
        )
    except Exception as e:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        json.dumps({"saved": False, "error": str(e)}, indent=2),
                        tool_call_id=tool_call_id or "",
                    )
                ]
            }
        )


# Prepare tools and subagents
base_tools = [
    internet_search,
    cache_store_source,
    cache_get_source,
    cache_list_sources,
    add_context_note,
    get_context_notes,
    persist_run,
]
base_subagents = [
    wine_disambiguator_sub_agent,
    wine_validator_sub_agent,
    critique_sub_agent,
    research_sub_agent,
    wine_field_sub_agent,
]

# Add Qdrant tools and subagent if available
if QDRANT_AVAILABLE:
    base_tools.extend([qdrant_sync_cache, qdrant_retrieve, qdrant_inspect])
    base_subagents.append(qdrant_sub_agent)

# Create the agent
agent = create_deep_agent(
    base_tools,
    research_instructions,
    subagents=base_subagents,
).with_config({"recursion_limit": 1000})
