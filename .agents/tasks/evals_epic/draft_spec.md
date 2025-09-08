# Evals Epic — Phased Rollout (Low-Effort → High-Impact)

Goal: Ship evals in small, safe iterations that immediately increase robustness, create feedback loops, and gate regressions. Each phase is ≤1–2 days of work, with runnable tests and clear acceptance criteria.

## Phase 0 — Wiring & Offline Determinism (foundation)

- Scope:
  - Minimal metrics plumbing (`Metrics` + `.metrics.json`) and `gate_or_halt` helper (no runtime model changes).
  - Offline test mode: run with cache-only, `WINE_SEARCH_CALLS_PER_RUN=0`.
- Datasets/fixtures:
  - Tiny seed set (5–10 items) for normalized_name + grapes using `.cache` fixtures.
- Acceptance:
  - `.metrics.json` persisted on runs; gates log reasons.
  - Deterministic outputs under fixed seed; offline run passes.

## Phase 1 — Ambiguity/Validation Gates (biggest stability win)

- Hooks to implement:
  - (1,3,4,5) Disambiguation reason logging; ambiguity gate; validation expected/actual/match; failure reason event.
- Tests:
  - Ambiguous query → halts with NEED_CLARIFICATION; disamb overcommit flagged.
  - Validator pass/fail parity on labeled cases.
- Acceptance:
  - Ambiguity gate blocks Phase 1 when needed; validation match ≥ 0.9 on seed set.

## Phase 2 — Planning/TODO Hygiene (prevent downstream waste)

- Hooks:
  - (6,7,8,9) Required tasks present; first task `normalized_name`; FSM transitions; language note present.
- Tests:
  - TODO plan includes all required fields and correct initial state; illegal transitions rejected.
- Acceptance:
  - 100% of test runs produce valid TODOs; FSM forbids illegal jumps.

## Phase 3 — Normalized Name Checkpoint (critical correctness gate)

- Hooks:
  - (10,11,12,13) Exact label match; NV-aware vintage; hard stop if mismatch; at least one citation.
- Datasets:
  - 20-item gold with exact labels + NV/ranges.
- Acceptance:
  - Exact match ≥ 0.95; zero violations of the mismatch gate.

## Phase 4 — Core Fields Accuracy (producer/region/appellation/vintage/grapes)

- Hooks:
  - (14–19) Producer eq, region in canon, appellation alias, vintage numeric, grapes F1 + % sanity, citations present.
- Datasets:
  - 30–50 gold items with canonical ontology (use mappings + curated JSON).
- Acceptance:
  - Producer/region/appellation exact ≥ 0.9; grapes F1 ≥ 0.85; % sanity pass ≥ 0.95.

## Phase 5 — Retrieval & Cache/Qdrant Efficiency

- Hooks:
  - (20–28, 25–28 new) Budget gate; preferred/trusted/recency; contradiction count; rerank delta; cache hits; Qdrant recall@k.
- Datasets:
  - Retrieval labels: query → relevant URLs (20–30 queries).
- Acceptance:
  - Budget respected; preferred/trusted ratio ≥ target; stale_source_gate never violated; recall@k ≥ 0.7 on labeled set.

## Phase 6 — Generation Faithfulness & Attribution

- Hooks:
  - (29–33) Faithfulness (RAGAS) + context utilization; claim coverage ratio; schema/version; CSV/JSON injection safety.
- Datasets:
  - 20 gold Q&A with passages and citations (eAmbrosia/VIVC/TTB/OIV).
- Acceptance:
  - Faithfulness ≥ 0.85; claims_supported_ratio ≥ 0.8; schema/version enforced; no injection violations.

## Phase 7 — Planner & Tool Discipline

- Hooks:
  - (34–40) Phase ordering; clarification halt; retries/backoff; minimality; backtrack cap; args schema; deterministic retries.
- Tests:
  - Inject tool faults; verify recovery and no thrashing; detect extraneous calls.
- Acceptance:
  - Backtracks ≤ 2; retries ≤ 3; deterministic retry passes; zero extraneous calls in tests.

## Phase 8 — Export E2E Quality (WooCommerce)

- Hooks:
  - (41–45) Pre-export validation with rule IDs; mapping coverage; WPML links; delimiter/pipe; bilingual parity.
- Datasets:
  - Use `test_data/export/wine.json` + mappings; 5–10 curated wines.
- Acceptance:
  - Zero validation errors; WPML linking correct; parity ≥ 0.9; CSV format checks pass.

## Phase 9 — Ontologies, I18N, Safety

- Hooks:
  - (46–51) Synonym canon rate; region-country consistency; appellation–style; output language fidelity; disclaimers; age guard.
- Acceptance:
  - Synonym canon rate tracked; zero consistency/style violations on tests; language fidelity 100%.

## Phase 10 — Reliability, Provenance, HITL

- Hooks:
  - (52–62) Context utilization; prompt cap; cache ETag; fault injection recovery; determinism; cycle tripwire; claim→source map; URL canonicalization; link-rot; HITL triggers; feedback capture.
- Acceptance:
  - No prompt bloat; determinism holds; cycle detection green; HITL triggers on intended gates; `.metrics.json` contains provenance map key.

---

## Per-Phase Deliverables

- Tests: `tests/evals/phase_{n}_*.py` (offline-capable where possible).
- Config: optional `evals/suites/gates.yaml` loaded by gate helper.
- Metrics: `.metrics.json` persisted for each run.
- Docs: `PROGRESS.md` entry with timestamp, problem, done, memo.

## Promotion Policy (CI Gates)

- Promote a phase only when all acceptance checks pass on dev and holdout sets; block merges on regression.
- Track trend lines for: ambiguity gate pass rate, normalized_name exactness, faithfulness, claims coverage, retrieval recall, grapes F1, latency, cost, steps.

## Next Steps (start here)

1. Implement Phase 0 wiring + offline fixtures (cache-only); add one smoke test.
2. Add Phase 1 ambiguity/validation gates and tests; measure baseline.
3. Proceed to Phase 3 normalized_name checkpoint (highest leverage correctness gate).
