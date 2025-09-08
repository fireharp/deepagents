# Qdrant Integration for DeepAgents

This module provides vector database capabilities for persisting and retrieving cached wine research data using Qdrant.

## Overview

The Qdrant integration allows you to:

- **Persist cached sources**: Store `.cache/wine_sources/*.txt` files in a Qdrant collection for cross-run reuse
- **Retrieve semantically**: Query for top-k similar wine information snippets
- **Filter by wine**: Prevent cross-wine confusion in shared collections
- **Inspect database**: Monitor what's stored and debug ingestion issues

## Installation

```bash
# Install DeepAgents with Qdrant support
pip install deepagents[qdrant]

# Or install dependencies manually
pip install qdrant-client langchain-openai tiktoken
```

## Environment Variables

```bash
# Required for Qdrant
QDRANT_URL=https://your-cluster.qdrant.io:6333
# OR
QDRANT_API_ENDPOINT=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-api-key

# Required for embeddings
OPENAI_API_KEY=your-openai-key

# Optional
OPENAI_EMBED_MODEL=text-embedding-3-small  # default
QDRANT_COLLECTION=tavily_cache              # default collection name
```

## Quick Start

### 1. Ingest Wine Research Data

```bash
# From agent state file (JSON with file mappings)
python ingest_qdrant.py --state-file path/to/state.json --collection my_wine_collection

# From filesystem directory
python ingest_qdrant.py --ingest-dir .cache/wine_sources --collection my_wine_collection
```

### 2. Query Wine Information

```bash
# General semantic search
python query_qdrant.py --query "alcohol content" --k 5 --collection my_wine_collection

# Wine-specific search (prevents cross-wine confusion)
python query_qdrant.py --query "fermentation" --wine nivarius-tempranillo-blanco-2023 --collection my_wine_collection
```

### 3. Inspect Database

```bash
# List all collections
python inspect_qdrant.py --action collections

# Sample documents from collection
python inspect_qdrant.py --action points --collection my_wine_collection --limit 10

# All documents for specific wine
python inspect_qdrant.py --action wine --collection my_wine_collection --wine nivarius-tempranillo-blanco-2023
```

## Data Model

### Document Structure

Each cached wine source file follows this format:

```
URL: https://example.com/wine-page
Title: Wine Name and Details
Fetched: 2025-09-07T18:48:51Z

[Raw page content used for extraction...]
```

### Qdrant Payload

Each document stored in Qdrant includes:

```json
{
  "url": "https://example.com/wine-page",
  "title": "Wine Name and Details",
  "site": "example.com",
  "fetched_at": "2025-09-07T18:48:51Z",
  "path": ".cache/wine_sources/example.com__wine-page.txt",
  "wine_query": "nivarius tempranillo blanco 2023",
  "wine_slug": "nivarius-tempranillo-blanco-2023"
}
```

### Wine Context

- **wine_query**: Original search query (from `question.txt` in state)
- **wine_slug**: Normalized identifier for filtering (auto-generated)
- **Filtering**: Use `--wine wine-slug` to get results for specific wine only

## API Usage

### QdrantTools Class

```python
from deepagents.qdrant import QdrantTools, CachedDoc

tools = QdrantTools()

# Collect documents from state
docs = tools.collect_docs_from_state(state_files_dict)

# Derive wine context
wine_query, wine_slug = tools.derive_wine_context(state_files_dict)

# Upsert to Qdrant
upserted, error = tools.upsert_documents(docs, "collection_name", wine_query, wine_slug)

# Search documents
results = tools.search_documents("alcohol content", k=5, collection="collection_name", wine_slug="wine-slug")

# Inspect database
collections = tools.inspect_collections()
wine_docs = tools.get_wine_documents("collection_name", "wine-slug")
```

## Command Reference

### ingest_qdrant.py

Ingest cached wine sources into Qdrant collection.

**Arguments:**

- `--state-file`: Path to JSON state file containing file mappings
- `--ingest-dir`: Directory with cached files (default: `.cache/wine_sources`)
- `--collection`: Qdrant collection name (default: `tavily_cache`)

**Output:**

```json
{
  "ingest_plan": {
    "num_docs": 11,
    "collection": "wine_collection",
    "wine_context": {
      "wine_query": "nivarius tempranillo blanco 2023",
      "wine_slug": "nivarius-tempranillo-blanco-2023"
    },
    "sources": [...]
  }
}
{"upserted": 11, "collection": "wine_collection"}
```

### query_qdrant.py

Query Qdrant for semantically similar documents.

**Arguments:**

- `--query`: Search text (required)
- `--k`: Number of results (default: 5)
- `--collection`: Collection name (default: `tavily_cache`)
- `--wine`: Wine slug filter (optional)

**Output:**

```json
{
  "query": "alcohol content",
  "k": 5,
  "collection": "wine_collection",
  "wine_slug": "nivarius-tempranillo-blanco-2023",
  "results": [
    {
      "doc_id": "uuid",
      "score": 0.85,
      "url": "https://example.com/wine",
      "title": "Wine Details",
      "site": "example.com",
      "wine_query": "original query",
      "wine_slug": "wine-identifier"
    }
  ]
}
```

### inspect_qdrant.py

Inspect Qdrant database contents.

**Arguments:**

- `--action`: What to inspect
  - `collections`: List all collections (default)
  - `points`: Sample documents from collection
  - `wine`: Documents for specific wine
- `--collection`: Collection name (for points/wine actions)
- `--wine`: Wine slug (required for wine action)
- `--limit`: Max points to show (default: 10)

## Best Practices

### Production Monitoring

```bash
# Daily health check
python inspect_qdrant.py --action collections > daily_collections.json

# Verify wine ingestion
python inspect_qdrant.py --action wine --wine $WINE_SLUG --collection $COLLECTION

# Monitor collection growth
python inspect_qdrant.py --action points --limit 1 | jq '.sample_points | length'
```

### Development Workflow

```bash
# 1. Ingest new wine data
python ingest_qdrant.py --state-file research_output.json

# 2. Verify ingestion
python inspect_qdrant.py --action collections

# 3. Test queries
python query_qdrant.py --query "alcohol" --wine wine-slug-here

# 4. Debug specific wine
python inspect_qdrant.py --action wine --wine wine-slug-here
```

### Error Handling

All tools gracefully handle:

- Missing environment variables
- Network connectivity issues
- Missing dependencies
- Invalid collection names
- Malformed data

Errors return structured JSON with clear messages instead of throwing exceptions.

## Troubleshooting

### Common Issues

**"Qdrant env not set"**

- Set `QDRANT_URL` (or `QDRANT_API_ENDPOINT`) and `QDRANT_API_KEY`

**"OpenAI embeddings not configured"**

- Set `OPENAI_API_KEY`

**"qdrant-client not available"**

- Install: `pip install qdrant-client`

**"Collection setup failed"**

- Check Qdrant endpoint connectivity
- Verify API key permissions

### Debug Commands

```bash
# Test Qdrant connectivity
python -c "from qdrant_client import QdrantClient; import os; c=QdrantClient(url=os.environ['QDRANT_URL'], api_key=os.environ['QDRANT_API_KEY']); print(c.get_collections())"

# Test OpenAI embeddings
python -c "from langchain_openai import OpenAIEmbeddings; import os; e=OpenAIEmbeddings(); print(len(e.embed_query('test')))"

# Check environment
env | grep -E "(QDRANT|OPENAI)"
```

## Wine Context System

### Automatic Wine Detection

The system automatically derives wine context from `question.txt` in agent state:

```
"nivarius tempranillo blanco 2023" → wine_slug: "nivarius-tempranillo-blanco-2023"
```

### Multi-Wine Collections

Store multiple wines in the same collection safely:

```bash
# Wine 1
python ingest_qdrant.py --state-file wine1_state.json --collection shared_collection

# Wine 2
python ingest_qdrant.py --state-file wine2_state.json --collection shared_collection

# Query specific wine only
python query_qdrant.py --query "alcohol" --wine wine1-slug --collection shared_collection
python query_qdrant.py --query "alcohol" --wine wine2-slug --collection shared_collection
```

## Integration with Wine Agent

The tools integrate seamlessly with the wine research agent workflow:

1. **Agent researches wine** → Caches sources in `.cache/wine_sources/`
2. **Ingest to Qdrant** → `python ingest_qdrant.py --state-file agent_state.json`
3. **Future queries** → `python query_qdrant.py --query "field" --wine wine-slug`

This enables cross-run knowledge persistence and faster field lookups.
