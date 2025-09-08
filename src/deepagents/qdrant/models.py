"""Data models for Qdrant integration."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CachedDoc:
    """Represents a cached document for Qdrant ingestion."""

    id: str
    url: Optional[str]
    title: Optional[str]
    site: Optional[str]
    fetched_at: Optional[str]
    content: str
    path: str
