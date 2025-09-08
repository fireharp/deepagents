"""Qdrant integration tools for DeepAgents."""

import json
from typing import Optional, Annotated

from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.prebuilt import InjectedState

from deepagents.state import DeepAgentState
from .client import QdrantTools


@tool(
    description="Sync cached wine sources to Qdrant vector database for persistent storage and retrieval."
)
def qdrant_sync_cache(
    collection_name: str = "tavily_cache",
    state: Annotated[DeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Upsert all cached sources from .cache/wine_sources/ into Qdrant collection.

    Args:
        collection_name: Name of Qdrant collection to use

    Returns:
        Command with sync operation results
    """
    if state is None:
        return Command(
            update={
                "messages": [
                    ToolMessage("Error: No state available", tool_call_id=tool_call_id)
                ]
            }
        )

    try:
        tools = QdrantTools()
        files = state.get("files", {})

        # Check if Qdrant is configured
        if not tools.qdrant_url or not tools.qdrant_api_key:
            result_msg = "Qdrant not configured. Set QDRANT_URL and QDRANT_API_KEY environment variables."
            return Command(
                update={
                    "messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)]
                }
            )

        if not tools.openai_api_key:
            result_msg = "OpenAI not configured. Set OPENAI_API_KEY for embeddings."
            return Command(
                update={
                    "messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)]
                }
            )

        # Derive wine context from state
        wine_query, wine_slug = tools.derive_wine_context(files)

        # Collect documents from cached sources
        docs = tools.collect_docs_from_state(files)

        if not docs:
            result_msg = f"No cached sources found in .cache/wine_sources/ to sync to {collection_name}"
            return Command(
                update={
                    "messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)]
                }
            )

        # Upsert documents to Qdrant
        upserted, error = tools.upsert_documents(
            docs, collection_name, wine_query, wine_slug
        )

        if error:
            result_msg = f"Sync failed: {error}"
        else:
            result_msg = f"Successfully synced {upserted} documents to collection '{collection_name}'"
            if wine_query:
                result_msg += f" for wine: {wine_query}"

        return Command(
            update={"messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)]}
        )

    except Exception as e:
        result_msg = f"Sync error: {str(e)}"
        return Command(
            update={"messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)]}
        )


@tool(description="Search Qdrant vector database for similar wine documents.")
def qdrant_retrieve(
    query: str,
    k: int = 5,
    collection_name: str = "tavily_cache",
    wine_slug: Optional[str] = None,
    state: Annotated[DeepAgentState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Retrieve similar documents from Qdrant using semantic search.

    Args:
        query: Search query text
        k: Number of results to return (max 20)
        collection_name: Qdrant collection to search
        wine_slug: Optional wine slug to filter results

    Returns:
        Command with search results
    """
    if state is None:
        error_msg = json.dumps([{"error": "No state available"}], indent=2)
        return Command(
            update={"messages": [ToolMessage(error_msg, tool_call_id=tool_call_id)]}
        )

    try:
        tools = QdrantTools()

        # Check if Qdrant is configured
        if not tools.qdrant_url or not tools.qdrant_api_key:
            error_msg = json.dumps(
                [
                    {
                        "error": "Qdrant not configured. Set QDRANT_URL and QDRANT_API_KEY environment variables."
                    }
                ],
                indent=2,
            )
            return Command(
                update={"messages": [ToolMessage(error_msg, tool_call_id=tool_call_id)]}
            )

        if not tools.openai_api_key:
            error_msg = json.dumps(
                [
                    {
                        "error": "OpenAI not configured. Set OPENAI_API_KEY for embeddings."
                    }
                ],
                indent=2,
            )
            return Command(
                update={"messages": [ToolMessage(error_msg, tool_call_id=tool_call_id)]}
            )

        # If no wine_slug provided, try to derive from state
        if not wine_slug:
            files = state.get("files", {})
            _, wine_slug = tools.derive_wine_context(files)

        # Perform search
        result = tools.search_documents(query, min(k, 20), collection_name, wine_slug)

        if "error" in result:
            error_msg = json.dumps([{"error": result["error"]}], indent=2)
            return Command(
                update={"messages": [ToolMessage(error_msg, tool_call_id=tool_call_id)]}
            )

        results = result.get("results", [])
        result_payload = {
            "query": query,
            "collection": collection_name,
            "wine_slug": wine_slug,
            "found": len(results),
            "results": results,
        }
        result_msg = json.dumps(result_payload, indent=2)

        # Also write a lightweight meta flag into the agent state so other tools can react
        # This enables internet_search to skip when Qdrant already returned useful results
        meta_path = ".cache/_meta/qdrant_last.json"
        files = state.get("files", {}) if state is not None else {}
        files[meta_path] = json.dumps(result_payload)

        return Command(
            update={
                "files": files,
                "messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)],
            }
        )

    except Exception as e:
        error_msg = json.dumps([{"error": f"Search error: {str(e)}"}], indent=2)
        return Command(
            update={"messages": [ToolMessage(error_msg, tool_call_id=tool_call_id)]}
        )


@tool(description="Inspect Qdrant database collections and documents.")
def qdrant_inspect(
    action: str = "collections",
    collection_name: str = "tavily_cache",
    wine_slug: Optional[str] = None,
    limit: int = 10,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """Inspect Qdrant database for debugging and monitoring.

    Args:
        action: Type of inspection ('collections', 'points', 'wine')
        collection_name: Collection to inspect (for 'points' and 'wine' actions)
        wine_slug: Wine slug filter (for 'wine' action)
        limit: Max results to return

    Returns:
        Command with inspection results
    """
    try:
        tools = QdrantTools()

        # Check if Qdrant is configured
        if not tools.qdrant_url or not tools.qdrant_api_key:
            error_result = {
                "error": "Qdrant not configured. Set QDRANT_URL and QDRANT_API_KEY environment variables."
            }
            result_msg = json.dumps(error_result, indent=2)
            return Command(
                update={
                    "messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)]
                }
            )

        if action == "collections":
            result = tools.inspect_collections()
        elif action == "points":
            result = tools.inspect_points(collection_name, limit)
        elif action == "wine":
            if not wine_slug:
                error_result = {"error": "wine_slug required for wine inspection"}
                result_msg = json.dumps(error_result, indent=2)
                return Command(
                    update={
                        "messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)]
                    }
                )
            result = tools.get_wine_documents(collection_name, wine_slug)
        else:
            error_result = {
                "error": f"Unknown action: {action}. Use 'collections', 'points', or 'wine'"
            }
            result_msg = json.dumps(error_result, indent=2)
            return Command(
                update={
                    "messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)]
                }
            )

        result_msg = json.dumps(result, indent=2)
        return Command(
            update={"messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)]}
        )

    except Exception as e:
        error_result = {"error": f"Inspection error: {str(e)}"}
        result_msg = json.dumps(error_result, indent=2)
        return Command(
            update={"messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)]}
        )
