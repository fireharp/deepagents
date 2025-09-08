#!/usr/bin/env python3
"""Query Qdrant for similar wine documents."""

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


def main(argv: List[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Query Qdrant for similar cached docs."
    )
    parser.add_argument("--query", required=True, help="Search text")
    parser.add_argument("--k", type=int, default=5, help="Top-k results")
    parser.add_argument(
        "--collection", default=os.getenv("QDRANT_COLLECTION", "tavily_cache")
    )
    parser.add_argument(
        "--wine",
        default=None,
        help="Optional wine slug to filter results (e.g., nivarius-tempranillo-blanco-2023)",
    )
    args = parser.parse_args(argv)

    tools = QdrantTools()
    result = tools.search_documents(args.query, args.k, args.collection, args.wine)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
