# Qdrant Usage Guide - Wine Research Example

Quick reference for using Qdrant tools with the wine research agent.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (add to .env)
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-api-key
OPENAI_API_KEY=your-openai-key
```

## Common Commands

### 📥 Ingest Wine Data

```bash
# From agent state file
python ingest_qdrant.py --state-file ../../.agents/docs/files_state_example/state.md

# From filesystem cache
python ingest_qdrant.py --ingest-dir .cache/wine_sources
```

### 🔍 Query Wine Information

```bash
# Search for alcohol information
python query_qdrant.py --query "alcohol content" --k 5

# Search specific wine only
python query_qdrant.py --query "fermentation" --wine nivarius-tempranillo-blanco-2023

# Search for tasting notes
python query_qdrant.py --query "tasting notes stone fruit" --k 3
```

### 📊 Inspect Database

```bash
# Show all collections
python inspect_qdrant.py --action collections

# Sample documents from collection
python inspect_qdrant.py --action points --limit 5

# All documents for specific wine
python inspect_qdrant.py --action wine --wine nivarius-tempranillo-blanco-2023
```

## Example Workflow

```bash
# 1. Run wine agent to research a wine
langgraph dev  # Start agent, research "Dom Pérignon 2015"

# 2. Ingest the cached research
python ingest_qdrant.py --state-file agent_state.json --collection wine_db

# 3. Verify ingestion
python inspect_qdrant.py --action collections

# 4. Query specific information
python query_qdrant.py --query "dosage" --wine dom-perignon-2015 --collection wine_db

# 5. Check what's stored for this wine
python inspect_qdrant.py --action wine --wine dom-perignon-2015 --collection wine_db
```

## Output Examples

### Ingestion Output
```json
{
  "ingest_plan": {
    "num_docs": 11,
    "collection": "wine_db",
    "wine_context": {
      "wine_query": "nivarius tempranillo blanco 2023",
      "wine_slug": "nivarius-tempranillo-blanco-2023"
    }
  }
}
{"upserted": 11, "collection": "wine_db"}
```

### Query Output
```json
{
  "query": "alcohol",
  "k": 3,
  "wine_slug": "nivarius-tempranillo-blanco-2023",
  "results": [
    {
      "doc_id": "f0bb4ba3-962c-f713-750b-b35a8190dc6a",
      "score": 0.229,
      "url": "https://www.wine-searcher.com/grape-2006-tempranillo-blanco",
      "title": "Tempranillo Blanco - White Wine Grape Variety",
      "site": "www.wine-searcher.com"
    }
  ]
}
```

### Collections Inspection
```json
{
  "collections": [
    {
      "name": "wine_db",
      "points_count": 45,
      "vector_size": 1536
    }
  ]
}
```

## Production Tips

### Monitoring Scripts

```bash
#!/bin/bash
# daily_check.sh - Monitor Qdrant health

echo "=== Collections Status ==="
python inspect_qdrant.py --action collections

echo -e "\n=== Recent Documents ==="
python inspect_qdrant.py --action points --limit 5

echo -e "\n=== Collection Size ==="
python inspect_qdrant.py --action collections | jq '.collections[] | "\(.name): \(.points_count) docs"'
```

### Backup/Migration

```bash
# Export wine documents for backup
python inspect_qdrant.py --action wine --wine wine-slug-here > wine_backup.json

# List all wine slugs in collection
python inspect_qdrant.py --action points --limit 1000 | jq '.sample_points[].payload.wine_slug' | sort | uniq
```

### Performance Monitoring

```bash
# Check embedding dimensions consistency
python inspect_qdrant.py --action collections | jq '.collections[] | "Collection \(.name): \(.vector_size)d vectors"'

# Count documents per wine
python inspect_qdrant.py --action points --limit 1000 | jq '.sample_points | group_by(.payload.wine_slug) | map({wine: .[0].payload.wine_slug, count: length})'
```

## Error Handling

All tools return structured JSON with error messages instead of crashing:

```json
{"error": "Qdrant env not set"}
{"error": "OpenAI embeddings not configured"}
{"error": "Collection setup failed: ..."}
```

This makes them safe for automated scripts and CI/CD pipelines.

## Integration Points

### With Wine Agent

The tools integrate with the wine research agent through:
1. Agent caches sources in `.cache/wine_sources/`
2. State includes `question.txt` for wine context
3. Ingestion derives wine_slug automatically
4. Queries filter by wine_slug to prevent confusion

### With LangGraph

Use programmatically in LangGraph tools:

```python
from deepagents.qdrant import QdrantTools

@tool
def qdrant_sync_cache(
    collection_name: str = "tavily_cache",
    state: Annotated[DeepAgentState, InjectedState] = None,
) -> str:
    """Sync cached sources to Qdrant."""
    tools = QdrantTools()
    files = state.get("files", {})
    
    wine_query, wine_slug = tools.derive_wine_context(files)
    docs = tools.collect_docs_from_state(files)
    
    upserted, error = tools.upsert_documents(docs, collection_name, wine_query, wine_slug)
    
    if error:
        return f"Sync failed: {error}"
    return f"Synced {upserted} documents to {collection_name}"

@tool  
def qdrant_retrieve(
    query: str,
    k: int = 5,
    collection_name: str = "tavily_cache",
    wine_slug: Optional[str] = None,
) -> List[Dict]:
    """Retrieve similar documents from Qdrant."""
    tools = QdrantTools()
    result = tools.search_documents(query, k, collection_name, wine_slug)
    
    if "error" in result:
        return [{"error": result["error"]}]
    
    return result.get("results", [])
```

## Files Overview

- `client.py`: Main QdrantTools class with all functionality
- `models.py`: CachedDoc dataclass for type safety
- `__init__.py`: Module exports
- `README.md`: This documentation

## Dependencies

- `qdrant-client`: Vector database client
- `langchain-openai`: OpenAI embeddings
- `tiktoken`: Token counting for embeddings
- `httpx`: HTTP client (transitive)

All dependencies are optional - the core DeepAgents package works without Qdrant.
