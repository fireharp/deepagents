#!/usr/bin/env python3
"""Query script to view saved wine research runs in Neon PostgreSQL."""

import sys
from run_store import get_db_url, POSTGRES_AVAILABLE


def query_recent_runs(limit: int = 10):
    """Show recent wine research runs."""
    if not POSTGRES_AVAILABLE:
        print("❌ psycopg2 not available. Install with: pip install psycopg2-binary")
        return

    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        db_url = get_db_url()
        with psycopg2.connect(db_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as c:
                c.execute(
                    """
                    SELECT id, created_at, wine_slug, question, qdrant_collection, qdrant_found, notes
                    FROM runs 
                    ORDER BY created_at DESC 
                    LIMIT %s
                """,
                    (limit,),
                )

                runs = c.fetchall()

                if not runs:
                    print("No runs found in database.")
                    return

                print(f"=== Recent {len(runs)} Wine Research Runs ===\n")

                for run in runs:
                    print(f"🍷 Run ID: {run['id']}")
                    print(f"📅 Created: {run['created_at']}")
                    print(f"🏷️ Wine: {run['wine_slug'] or 'N/A'}")
                    print(f"❓ Question: {(run['question'] or 'N/A')[:60]}...")
                    print(
                        f"🔍 Qdrant: {run['qdrant_collection']} ({run['qdrant_found']} results)"
                    )
                    print(f"📝 Notes: {(run['notes'] or 'None')[:50]}...")
                    print("-" * 60)

    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback

        traceback.print_exc()


def query_run_details(run_id: str):
    """Show detailed information for a specific run."""
    if not POSTGRES_AVAILABLE:
        print("❌ psycopg2 not available")
        return

    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        db_url = get_db_url()
        with psycopg2.connect(db_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as c:
                # Get run info
                c.execute("SELECT * FROM runs WHERE id = %s", (run_id,))
                run = c.fetchone()

                if not run:
                    print(f"❌ Run {run_id} not found")
                    return

                print(f"=== Run Details: {run_id} ===\n")
                print(f"Created: {run['created_at']}")
                print(f"Wine: {run['wine_slug']}")
                print(f"Question: {run['question']}")
                print(f"Qdrant Collection: {run['qdrant_collection']}")
                print(f"Qdrant Results: {run['qdrant_found']}")
                print(f"Notes: {run['notes']}")

                # Get artifacts
                c.execute(
                    "SELECT name, content FROM artifacts WHERE run_id = %s", (run_id,)
                )
                artifacts = c.fetchall()

                print(f"\n📁 Artifacts ({len(artifacts)}):")
                for artifact in artifacts:
                    content_preview = (artifact["content"] or "")[:100].replace(
                        "\n", " "
                    )
                    print(f"  - {artifact['name']}: {content_preview}...")

                # Get sources count by field
                c.execute(
                    """
                    SELECT field, COUNT(*) as count 
                    FROM sources 
                    WHERE run_id = %s 
                    GROUP BY field 
                    ORDER BY field
                """,
                    (run_id,),
                )
                sources = c.fetchall()

                print("\n🔗 Sources by field:")
                for source in sources:
                    print(f"  - {source['field']}: {source['count']} sources")

    except Exception as e:
        print(f"❌ Query failed: {e}")


def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python query_runs.py recent [limit]")
        print("  python query_runs.py details <run_id>")
        return

    command = sys.argv[1]

    if command == "recent":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        query_recent_runs(limit)
    elif command == "details":
        if len(sys.argv) < 3:
            print("❌ Run ID required for details command")
            return
        run_id = sys.argv[2]
        query_run_details(run_id)
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
