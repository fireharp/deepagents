# Test Data Directory

This directory contains test data extracted from the LangGraph Docker container for wine research testing.

## Investigation Results

**Container ID**: `faa9ff7601b7` (agnohq/agent-api:dev)

### Key Findings:

1. The "cache files" mentioned in terminal logs are not persistent disk files
2. They are real-time HTTP requests to Jina AI's web scraping service:
   - `https://r.jina.ai/` - Reader API for web content extraction
   - `https://s.jina.ai/` - Search API for web searches

### URLs Being Processed:

Based on terminal logs, the system is processing these wine-related sources:

- winefolly.com/grapes/tempranillo/
- cellartours.com/blog/spain/riojas-unique-gift-tempranillo-blanco
- napavalleywineacademy.com (Rioja wine content)
- chinchinwinetrading.com (Tempranillo Blanco products)
- kysela.com (Nivarius Tempranillo Blanco)
- plummarket.com (2023 Nivarius Tempranillo Blanco)
- wine-searcher.com (Nivarius searches)
- riojavega.com (Tempranillo Blanco Reserva)

### Container Structure:

- Working directory: `/app`
- Cache directory: `/app/.cache` (mostly empty, contains rosetta)
- No persistent wine data files found on disk
- Application runs via uvicorn with live API requests

### Recommendation:

To capture wine research data for tests, consider:

1. Intercepting API responses during live sessions
2. Creating mock data based on the URLs being processed
3. Using the same Jina AI endpoints to fetch fresh data for tests
