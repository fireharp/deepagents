#!/usr/bin/env python3
"""Deduplicate Qdrant points by payload.path within a collection.

Non-interactive. Default is --dry-run (reports only). Use --apply to delete.

Environment:
  QDRANT_URL, QDRANT_API_KEY (required)

Usage examples:
  python cleanup_qdrant_dups.py --collection wine_test_v3           # dry run
  python cleanup_qdrant_dups.py --collection wine_test_v3 --apply   # perform deletion
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Tuple, List, Any

from qdrant_client import QdrantClient
from qdrant_client.models import PointIdsList


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Deduplicate Qdrant points by payload.path")
    p.add_argument("--collection", required=True, help="Collection name")
    p.add_argument("--batch", type=int, default=1000, help="Scroll batch size")
    p.add_argument(
        "--apply", action="store_true", help="Apply deletions (otherwise dry-run)"
    )
    return p.parse_args()


def _parse_dt(val: str | None) -> datetime | None:
    if not val:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(val, fmt)
        except Exception:
            continue
    return None


def main() -> int:
    args = parse_args()
    qdrant_url = os.getenv("QDRANT_URL") or os.getenv("QDRANT_API_ENDPOINT")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    if not qdrant_url or not qdrant_api_key:
        print(json.dumps({"error": "Missing QDRANT_URL or QDRANT_API_KEY"}))
        return 2

    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

    keep_by_path: Dict[str, Tuple[str, datetime | None]] = {}
    dup_ids: List[str] = []
    total = 0

    next_offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name=args.collection,
            with_payload=True,
            limit=args.batch,
            offset=next_offset,
        )
        if not points:
            break
        for pt in points:
            total += 1
            payload: Dict[str, Any] = pt.payload or {}
            path = payload.get("path")
            if not isinstance(path, str) or not path:
                continue
            fetched_at = (
                _parse_dt(payload.get("fetched_at"))
                if isinstance(payload.get("fetched_at"), str)
                else None
            )
            existing = keep_by_path.get(path)
            if existing is None:
                keep_by_path[path] = (str(pt.id), fetched_at)
            else:
                keep_id, keep_dt = existing
                # Keep the most recent fetched_at if available, else keep first
                replace = False
                if keep_dt and fetched_at:
                    replace = fetched_at > keep_dt
                elif not keep_dt and fetched_at:
                    replace = True
                else:
                    replace = False
                if replace:
                    dup_ids.append(keep_id)
                    keep_by_path[path] = (str(pt.id), fetched_at)
                else:
                    dup_ids.append(str(pt.id))

        if next_offset is None:
            break

    summary = {
        "collection": args.collection,
        "total_scanned": total,
        "unique_paths": len(keep_by_path),
        "duplicates_found": len(dup_ids),
        "mode": "apply" if args.apply else "dry-run",
    }

    if not args.apply or not dup_ids:
        print(json.dumps(summary, indent=2))
        return 0

    # Delete in chunks
    deleted = 0
    for i in range(0, len(dup_ids), 256):
        chunk = dup_ids[i : i + 256]
        client.delete(
            collection_name=args.collection, points_selector=PointIdsList(points=chunk)
        )
        deleted += len(chunk)

    summary["deleted"] = deleted
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
