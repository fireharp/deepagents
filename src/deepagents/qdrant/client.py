"""Qdrant client tools for document ingestion and retrieval."""

import os
import hashlib
from typing import List, Optional, Dict, Tuple
from urllib.parse import urlparse

from .models import CachedDoc


class QdrantTools:
    """Encapsulates Qdrant operations for wine document management."""

    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL") or os.getenv("QDRANT_API_ENDPOINT")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.embed_model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    @staticmethod
    def parse_cached_file(
        text: str,
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], str]:
        """Parse cached file content with headers."""
        lines = text.splitlines()
        url = None
        title = None
        fetched = None
        body_start = 0

        for i, line in enumerate(lines[:10]):
            low = line.lower()
            if low.startswith("url:"):
                url = line.split(":", 1)[1].strip() or None
            elif low.startswith("title:"):
                title = line.split(":", 1)[1].strip() or None
            elif low.startswith("fetched:"):
                fetched = line.split(":", 1)[1].strip() or None
            elif line.strip() == "" and i >= 2:
                body_start = i + 1
                break

        body = "\n".join(lines[body_start:]) if body_start < len(lines) else ""
        site = None
        if url:
            try:
                site = urlparse(url).netloc
            except Exception:
                site = None

        return url, title, site, fetched, body

    @staticmethod
    def generate_doc_id(
        url: Optional[str], fetched: Optional[str], content: str
    ) -> str:
        """Generate stable document ID."""
        base = None
        if url and fetched:
            base = f"{url}|{fetched}"
        if base is None or base.strip() == "|":
            base = content
        return hashlib.sha1(base.encode("utf-8", errors="ignore")).hexdigest()

    @staticmethod
    def derive_wine_context(
        files: Dict[str, str],
    ) -> Tuple[Optional[str], Optional[str]]:
        """Extract wine context from state files."""
        question = None
        for key in ("question.txt", "question", ".question.txt"):
            if key in files and isinstance(files[key], str) and files[key].strip():
                question = files[key].strip()
                break

        if not question:
            return None, None

        # Normalize to slug
        slug_chars = []
        for ch in question.lower():
            if ch.isalnum():
                slug_chars.append(ch)
            elif ch in {" ", "-", "_", "/"}:
                slug_chars.append("-")
            else:
                slug_chars.append("-")

        wine_slug = "".join(slug_chars)
        while "--" in wine_slug:
            wine_slug = wine_slug.replace("--", "-")
        wine_slug = wine_slug.strip("-")

        return question, wine_slug

    def collect_docs_from_state(self, files: Dict[str, str]) -> List[CachedDoc]:
        """Extract documents from state dictionary."""
        docs: List[CachedDoc] = []

        for path, text in files.items():
            if not path.startswith(".cache/wine_sources/") or not path.endswith(".txt"):
                continue

            url, title, site, fetched, body = self.parse_cached_file(text)
            if not body:
                continue

            doc_id = self.generate_doc_id(url, fetched, body)
            docs.append(
                CachedDoc(
                    id=doc_id,
                    url=url,
                    title=title,
                    site=site,
                    fetched_at=fetched,
                    content=body,
                    path=path,
                )
            )

        return docs

    def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Generate embeddings for text list."""
        if not self.openai_api_key:
            return None

        try:
            from langchain_openai import OpenAIEmbeddings  # type: ignore
        except ImportError as e:
            raise ImportError(f"langchain-openai not available: {e}")

        embeddings = OpenAIEmbeddings(model=self.embed_model)
        return embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single query."""
        if not self.openai_api_key:
            return None

        try:
            from langchain_openai import OpenAIEmbeddings  # type: ignore
        except ImportError as e:
            raise ImportError(f"langchain-openai not available: {e}")

        embeddings = OpenAIEmbeddings(model=self.embed_model)
        return embeddings.embed_query(text)

    def ensure_collection(self, client, name: str, vector_size: int):
        """Ensure collection exists with proper indexing."""
        try:
            from qdrant_client.models import Distance, VectorParams, PayloadSchemaType  # type: ignore
        except ImportError as e:
            raise ImportError(f"qdrant-client not available: {e}")

        try:
            collections = client.get_collections().collections or []
            for coll in collections:
                if getattr(coll, "name", None) == name:
                    return

            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

            # Create index for wine_slug filtering
            client.create_payload_index(
                collection_name=name,
                field_name="wine_slug",
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to ensure collection '{name}': {e}")

    def upsert_documents(
        self,
        docs: List[CachedDoc],
        collection: str,
        wine_query: Optional[str] = None,
        wine_slug: Optional[str] = None,
    ) -> Tuple[int, Optional[str]]:
        """Upsert documents to Qdrant collection."""
        if not self.qdrant_url or not self.qdrant_api_key:
            return 0, "Qdrant env not set; skipping upsert"

        try:
            from qdrant_client import QdrantClient  # type: ignore
            from qdrant_client.models import PointStruct  # type: ignore
        except ImportError as e:
            return 0, f"qdrant-client not available: {e}"

        try:
            client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
        except Exception as e:
            return 0, f"Qdrant connection failed: {e}"

        # Create embeddings
        vectors = self.embed_texts([d.content for d in docs])
        if vectors is None:
            return 0, "OpenAI embeddings not configured; skipping upsert"

        if not docs:
            return 0, None

        dim = len(vectors[0])

        try:
            self.ensure_collection(client, collection, dim)
        except Exception as e:
            return 0, f"Collection setup failed: {e}"

        points = []
        for d, vec in zip(docs, vectors):
            payload = {
                "url": d.url,
                "title": d.title,
                "site": d.site,
                "fetched_at": d.fetched_at,
                "path": d.path,
            }
            if wine_query:
                payload["wine_query"] = wine_query
            if wine_slug:
                payload["wine_slug"] = wine_slug

            # Convert SHA1 hash to UUID format
            point_id = (
                d.id[:8]
                + "-"
                + d.id[8:12]
                + "-"
                + d.id[12:16]
                + "-"
                + d.id[16:20]
                + "-"
                + d.id[20:32]
            )
            points.append(PointStruct(id=point_id, vector=vec, payload=payload))

        try:
            client.upsert(collection_name=collection, points=points, wait=True)
            return len(points), None
        except Exception as e:
            return 0, f"Upsert failed: {e}"

    def search_documents(
        self,
        query: str,
        k: int,
        collection: str,
        wine_slug: Optional[str] = None,
    ) -> Dict:
        """Search for similar documents in Qdrant."""
        if not self.qdrant_url or not self.qdrant_api_key:
            return {"error": "Qdrant env not set"}

        try:
            from qdrant_client import QdrantClient  # type: ignore
            from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore
        except ImportError as e:
            return {"error": f"qdrant-client not available: {e}"}

        vec = self.embed_query(query)
        if vec is None:
            return {"error": "OpenAI embeddings not configured"}

        client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)

        try:
            query_filter = None
            if wine_slug:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="wine_slug", match=MatchValue(value=wine_slug)
                        )
                    ]
                )

            hits = client.search(
                collection_name=collection,
                query_vector=vec,
                limit=max(1, k),
                query_filter=query_filter,
            )
        except Exception as e:
            return {"error": f"search failed: {e}"}

        results = []
        for h in hits or []:
            payload = getattr(h, "payload", {}) or {}
            doc = {
                "doc_id": str(getattr(h, "id", "")),
                "score": float(getattr(h, "score", 0.0)),
                "url": payload.get("url"),
                "title": payload.get("title"),
                "site": payload.get("site"),
                "fetched_at": payload.get("fetched_at"),
                "path": payload.get("path"),
                "wine_query": payload.get("wine_query"),
                "wine_slug": payload.get("wine_slug"),
            }
            results.append(doc)

        return {
            "query": query,
            "k": k,
            "collection": collection,
            "wine_slug": wine_slug,
            "results": results,
        }

    def inspect_collections(self) -> Dict:
        """List all collections with metadata."""
        if not self.qdrant_url or not self.qdrant_api_key:
            return {"error": "Qdrant env not set"}

        try:
            from qdrant_client import QdrantClient  # type: ignore
        except ImportError as e:
            return {"error": f"qdrant-client not available: {e}"}

        try:
            client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
            collections = client.get_collections().collections or []

            result = {"collections": []}
            for coll in collections:
                name = getattr(coll, "name", "unknown")

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

    def get_wine_documents(self, collection: str, wine_slug: str) -> Dict:
        """Get all documents for a specific wine."""
        if not self.qdrant_url or not self.qdrant_api_key:
            return {"error": "Qdrant env not set"}

        try:
            from qdrant_client import QdrantClient  # type: ignore
            from qdrant_client.models import Filter, FieldCondition, MatchValue  # type: ignore
        except ImportError as e:
            return {"error": f"qdrant-client not available: {e}"}

        try:
            client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)

            query_filter = Filter(
                must=[
                    FieldCondition(key="wine_slug", match=MatchValue(value=wine_slug))
                ]
            )

            points = client.scroll(
                collection_name=collection,
                scroll_filter=query_filter,
                limit=100,
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
            return {"error": f"Failed to get wine documents: {e}"}
