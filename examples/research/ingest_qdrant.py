#!/usr/bin/env python3
"""Ingest cached wine sources into Qdrant collection."""

import os
import sys
import json
from typing import List

try:
    from deepagents.qdrant import QdrantTools, CachedDoc
except ImportError:
    # Fallback for development
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    from deepagents.qdrant import QdrantTools, CachedDoc


def _collect_docs_from_fs(root: str = ".cache/wine_sources") -> List[CachedDoc]:
    """Collect documents from filesystem (fallback when no state file)."""
    docs: List[CachedDoc] = []
    if not os.path.isdir(root):
        return docs

    tools = QdrantTools()
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if not fname.endswith(".txt"):
                continue
            p = os.path.join(dirpath, fname)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except Exception:
                continue

            url, title, site, fetched, body = tools.parse_cached_file(text)
            if not body:
                continue

            doc_id = tools.generate_doc_id(url, fetched, body)
            rel_path = os.path.relpath(p)
            docs.append(
                CachedDoc(
                    id=doc_id,
                    url=url,
                    title=title,
                    site=site,
                    fetched_at=fetched,
                    content=body,
                    path=rel_path,
                )
            )
    return docs


def main(argv: List[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest cached wine sources into Qdrant (or dry-run)."
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="Path to JSON state file that contains a mapping of files.",
    )
    parser.add_argument(
        "--ingest-dir",
        default=os.getenv("INGEST_DIR", ".cache/wine_sources"),
        help="Directory to read cached files from if no state-file is provided.",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("QDRANT_COLLECTION", "tavily_cache"),
        help="Qdrant collection name.",
    )
    args = parser.parse_args(argv)

    tools = QdrantTools()
    wine_query = None
    wine_slug = None

    if args.state_file:
        with open(args.state_file, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        try:
            state = json.loads(raw)
        except json.JSONDecodeError:
            # Some state files may wrap JSON in markdown fences; try to strip
            raw_stripped = raw.strip()
            if raw_stripped.startswith("```"):
                raw_stripped = raw_stripped.strip("`\n ")
            state = json.loads(raw_stripped)
        if not isinstance(state, dict):
            print(
                "[error] state-file JSON must be an object mapping file paths to contents",
                file=sys.stderr,
            )
            return 2
        wine_query, wine_slug = tools.derive_wine_context(state)
        docs = tools.collect_docs_from_state(state)
    else:
        docs = _collect_docs_from_fs(args.ingest_dir)

    print(
        json.dumps(
            {
                "ingest_plan": {
                    "num_docs": len(docs),
                    "collection": args.collection,
                    "wine_context": {
                        "wine_query": wine_query,
                        "wine_slug": wine_slug,
                    },
                    "sources": [
                        {"id": d.id, "path": d.path, "url": d.url, "title": d.title}
                        for d in docs
                    ],
                }
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    # Try Qdrant upsert if env & deps available
    upserted, warn = tools.upsert_documents(
        docs, args.collection, wine_query, wine_slug
    )
    result = {
        "upserted": upserted,
        "collection": args.collection,
    }
    if warn:
        result["warning"] = warn
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
