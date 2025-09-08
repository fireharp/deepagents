## TS: 2025-09-07 23:31:08 CEST

## PROBLEM: Jina provider returned empty results in tests; fallback not triggered

## WHAT WAS DONE: Implemented structured + simple endpoint fallback in `_discover_urls`; removed strict content-type dependency; added text parsing; verified all search tests pass

MEMO: Jina discovery now resilient to response shape/content-type; raw content fetching and domain filtering validated by tests
