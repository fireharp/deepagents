#!/usr/bin/env python3
"""Inspect Qdrant collections and documents for debugging/monitoring."""

import os
import sys
import json
from typing import List

try:
    from deepagents.qdrant import QdrantTools
except ImportError:
    # Fallback for development
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    from deepagents.qdrant import QdrantTools


def inspect_collections(tools: QdrantTools) -> dict:
    """List all collections and their info."""
    if not tools.qdrant_url or not tools.qdrant_api_key:
        return {"error": "Qdrant env not set"}

    try:
        from qdrant_client import QdrantClient  # type: ignore
    except ImportError as e:
        return {"error": f"qdrant-client not available: {e}"}

    try:
        client = QdrantClient(url=tools.qdrant_url, api_key=tools.qdrant_api_key)
        collections = client.get_collections().collections or []

        result = {"collections": []}
        for coll in collections:
            name = getattr(coll, "name", "unknown")

            # Get collection info
            try:
                info = client.get_collection(collection_name=name)
                point_count = getattr(info, "points_count", 0)
                vector_size = 0
                if hasattr(info, "config") and hasattr(info.config, "params"):
                    if hasattr(info.config.params, "vectors"):
                        vectors_config = info.config.params.vectors
                        if hasattr(vectors_config, "size"):
                            vector_size = vectors_config.size

                result["collections"].append(
                    {
                        "name": name,
                        "points_count": point_count,
                        "vector_size": vector_size,
                    }
                )
            except Exception as e:
                result["collections"].append(
                    {
                        "name": name,
                        "error": str(e),
                    }
                )

        return result
    except Exception as e:
        return {"error": f"Failed to list collections: {e}"}


def inspect_collection_points(
    tools: QdrantTools, collection: str, limit: int = 10
) -> dict:
    """Show sample points from a collection."""
    if not tools.qdrant_url or not tools.qdrant_api_key:
        return {"error": "Qdrant env not set"}

    try:
        from qdrant_client import QdrantClient  # type: ignore
    except ImportError as e:
        return {"error": f"qdrant-client not available: {e}"}

    try:
        client = QdrantClient(url=tools.qdrant_url, api_key=tools.qdrant_api_key)

        # Get sample points
        points = client.scroll(
            collection_name=collection,
            limit=limit,
            with_payload=True,
            with_vectors=False,  # Don't fetch vectors to save bandwidth
        )

        result = {
            "collection": collection,
            "sample_points": [],
        }

        if points and len(points) > 0:
            records = points[0] if isinstance(points, tuple) else points
            for point in records or []:
                point_data = {
                    "id": str(getattr(point, "id", "")),
                    "payload": getattr(point, "payload", {}),
                }
                result["sample_points"].append(point_data)

        return result
    except Exception as e:
        return {"error": f"Failed to inspect collection '{collection}': {e}"}


def search_by_wine_slug(tools: QdrantTools, collection: str, wine_slug: str) -> dict:
    """Find all documents for a specific wine."""
    if not tools.qdrant_url or not tools.qdrant_api_key:
        return {"error": "Qdrant env not set"}

    try:
        from qdrant_client import QdrantClient  # type: ignore
        from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore
    except ImportError as e:
        return {"error": f"qdrant-client not available: {e}"}

    try:
        client = QdrantClient(url=tools.qdrant_url, api_key=tools.qdrant_api_key)

        # Filter by wine_slug
        query_filter = Filter(
            must=[FieldCondition(key="wine_slug", match=MatchValue(value=wine_slug))]
        )

        points = client.scroll(
            collection_name=collection,
            scroll_filter=query_filter,
            limit=100,  # Get all points for this wine
            with_payload=True,
            with_vectors=False,
        )

        result = {
            "collection": collection,
            "wine_slug": wine_slug,
            "documents": [],
        }

        if points and len(points) > 0:
            records = points[0] if isinstance(points, tuple) else points
            for point in records or []:
                payload = getattr(point, "payload", {})
                doc_data = {
                    "id": str(getattr(point, "id", "")),
                    "url": payload.get("url"),
                    "title": payload.get("title"),
                    "site": payload.get("site"),
                    "path": payload.get("path"),
                    "wine_query": payload.get("wine_query"),
                }
                result["documents"].append(doc_data)

        return result
    except Exception as e:
        return {"error": f"Failed to search wine_slug '{wine_slug}': {e}"}


def main(argv: List[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Inspect Qdrant collections and documents."
    )
    parser.add_argument(
        "--action",
        choices=["collections", "points", "wine"],
        default="collections",
        help="What to inspect: collections (list all), points (sample docs), wine (docs for specific wine)",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("QDRANT_COLLECTION", "tavily_cache"),
        help="Collection name for points/wine actions",
    )
    parser.add_argument(
        "--wine", default=None, help="Wine slug to search for (used with --action wine)"
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Max points to show (for points action)"
    )
    args = parser.parse_args(argv)

    tools = QdrantTools()

    if args.action == "collections":
        result = inspect_collections(tools)
    elif args.action == "points":
        result = inspect_collection_points(tools, args.collection, args.limit)
    elif args.action == "wine":
        if not args.wine:
            print("Error: --wine parameter required for wine action", file=sys.stderr)
            return 1
        result = search_by_wine_slug(tools, args.collection, args.wine)
    else:
        print("Error: Invalid action", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
