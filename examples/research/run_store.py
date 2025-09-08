import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Default connection string - override with NEON_DATABASE_URL env var
DEFAULT_NEON_URL = "postgresql://neondb_owner:npg_pgQuPyD4f9zl@ep-falling-glade-adt0yiz6-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"


def get_db_url() -> str:
    """Get database URL from env or default."""
    return os.getenv("NEON_DATABASE_URL", DEFAULT_NEON_URL)


def init_db(db_url: str = None) -> None:
    """Initialize PostgreSQL tables."""
    if not POSTGRES_AVAILABLE:
        raise ImportError(
            "psycopg2 not available. Install with: pip install psycopg2-binary"
        )

    if db_url is None:
        db_url = get_db_url()

    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                  id TEXT PRIMARY KEY,
                  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                  wine_slug TEXT,
                  question TEXT,
                  qdrant_collection TEXT,
                  qdrant_found INTEGER,
                  notes TEXT
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                  id SERIAL PRIMARY KEY,
                  run_id TEXT NOT NULL,
                  name TEXT NOT NULL,
                  content TEXT,
                  FOREIGN KEY(run_id) REFERENCES runs(id)
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS sources (
                  id SERIAL PRIMARY KEY,
                  run_id TEXT NOT NULL,
                  link TEXT,
                  extract TEXT,
                  field TEXT,
                  FOREIGN KEY(run_id) REFERENCES runs(id)
                )
                """
            )
            conn.commit()


def _derive_wine_slug(files: Dict[str, str]) -> str:
    # Prefer question.txt if present, else from wine.json
    question = (files.get("question.txt") or "").strip()
    if question:
        slug_chars = []
        for ch in question.lower():
            if ch.isalnum():
                slug_chars.append(ch)
            elif ch in {" ", "-", "_", "/"}:
                slug_chars.append("-")
        slug = "".join(slug_chars).strip("-")
        while "--" in slug:
            slug = slug.replace("--", "-")
        return slug

    wine_json_raw = files.get("wine.json")
    if not wine_json_raw:
        return ""
    try:
        data = json.loads(wine_json_raw)
        name = data.get("wine", {}).get("normalized_name", {}).get("value") or ""
        vintage = data.get("wine", {}).get("vintage", {}).get("value")
        base = f"{name} {vintage}" if vintage else name
        slug = base.lower().replace(" ", "-")
        return slug
    except Exception:
        return ""


def _extract_sources_from_wine(data: Dict[str, Any]) -> Tuple[list, list]:
    sources_rows = []
    artifact_rows = []

    def handle_field(field_name: str, node: Any):
        if not isinstance(node, dict):
            return
        srcs = node.get("sources") or []
        if isinstance(srcs, list):
            for s in srcs:
                link = s.get("link") if isinstance(s, dict) else None
                extract = s.get("extract") if isinstance(s, dict) else None
                if link or extract:
                    sources_rows.append((link, extract, field_name))

    wine = data.get("wine", {}) if isinstance(data, dict) else {}
    for key, node in wine.items():
        if key == "grapes" and isinstance(node, list):
            for g in node:
                srcs = g.get("sources") or []
                for s in srcs:
                    link = s.get("link") if isinstance(s, dict) else None
                    extract = s.get("extract") if isinstance(s, dict) else None
                    if link or extract:
                        sources_rows.append((link, extract, "grapes"))
        else:
            handle_field(key, node)

    return sources_rows, artifact_rows


def save_run(
    files: Dict[str, str],
    notes: str = "",
    db_url: str = None,
) -> str:
    """Persist current run files and derived metadata to Neon PostgreSQL.

    Returns the run_id (uuid4 string).
    """
    if db_url is None:
        db_url = get_db_url()

    init_db(db_url)

    run_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    wine_slug = _derive_wine_slug(files)
    question = (files.get("question.txt") or "").strip()

    # Qdrant meta if present
    q_meta_raw = files.get(".cache/_meta/qdrant_last.json")
    q_collection = None
    q_found = None
    if q_meta_raw:
        try:
            q_meta = json.loads(q_meta_raw)
            q_collection = q_meta.get("collection")
            q_found = int(q_meta.get("found") or 0)
        except Exception:
            pass

    # Parse wine.json to collect sources
    wine_json_raw = files.get("wine.json")
    sources_rows = []
    if wine_json_raw:
        try:
            wine_data = json.loads(wine_json_raw)
            sources_rows, _ = _extract_sources_from_wine(wine_data)
        except Exception:
            pass

    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO runs (id, created_at, wine_slug, question, qdrant_collection, qdrant_found, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (run_id, created_at, wine_slug, question, q_collection, q_found, notes),
            )

            # Persist key artifacts if present
            for name in [
                "wine.json",
                "final_report.md",
                "question.txt",
                ".cache/_meta/qdrant_last.json",
            ]:
                content = files.get(name)
                if content:
                    c.execute(
                        "INSERT INTO artifacts (run_id, name, content) VALUES (%s, %s, %s)",
                        (run_id, name, content),
                    )

            # Persist sources
            for link, extract, field in sources_rows:
                c.execute(
                    "INSERT INTO sources (run_id, link, extract, field) VALUES (%s, %s, %s, %s)",
                    (run_id, link, extract, field),
                )

            conn.commit()

    return run_id
