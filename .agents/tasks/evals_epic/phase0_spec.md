# Phase 0 — Wiring & Offline Determinism (foundation)

- **Objective**: Stand up metrics plumbing and a deterministic offline evaluation loop. No runtime model changes. Prove `.metrics.json` persists and smoke tests run over a tiny labeled set.

## Scope

- **Plumbing**: Lightweight `Metrics` sink and `gate_or_halt` helper (no-op gates in Phase 0; log only).
- **Offline mode**: Run with cache-only, set `WINE_SEARCH_CALLS_PER_RUN=0` in tests.
- **Determinism**: Fixed seed; same inputs → same outputs.
- **Eval focus**: Minimal checks on `normalized_name` and obvious field constraints (when provided in labels) without gating.

## Dataset assessment (attached `.agents/docs/wines/*.yaml`)

- **Files** (10):

  - `veuve_ambal_rose.yaml` — NV vs fabricated vintage; inventory mismatch; traditional method required.
  - `tantum_ergo_rose_2022.yaml` — vintage must be 2022 though inventory says NV; name accent.
  - `umbretum_brut_nature.yaml` — tech facts (100% Garrido Fino, 24m en rima, Cádiz), avoid generic sparkling.
  - `nivarius_finca_la_nevera_2018.yaml` — fermentation must be stainless steel (not barrels), aging months.
  - `pepe_mendoza_giro.yaml` — inventory name expansion trap; should not expand into a different wine.
  - `rall_white.yaml` — spelling correction (Rall vs Rally), producer normalization.
  - `finca_calvestra_merseguera_2023.yaml` — producer must be Mustiguillo; vintage and grape present.
  - `laventura_viura_2022.yaml` — producer presence (MacRobert & Canals), spelling correction in note.
  - `clos_de_oratoire_2021.yaml` — duplication flag; appellation present.
  - `casa_sosegada_2022.yaml` — grape composition correctness (NOT Bobal), indigenous mix.

- **Coverage vs Phase 0 needs**:

  - Sufficient for Phase 0. We need 5–10 labeled items; we have 10 with diverse edge-cases: NV handling, wrong producer, spelling, dedup, name expansion, tech facts, vintage corrections.
  - These enable deterministic sanity checks for `normalized_name` and selected fields (vintage, grapes) when labels provided.

- **Optional adds (nice-to-have, not required for Phase 0)**:
  - 2 alias cases (region/appellation synonyms) for later phases.
  - 1 clearly ambiguous query to exercise disambiguation in Phase 1.

## Minimal YAML schema (validated in tests)

- Required keys: `wine_query`, `normalized_name` (can be null only if test is negative), `corrections`.
- Optional: `producer`, `region`, `appellation`, `vintage` (string or null), `grapes` (string or null), `fermentation`, `aging`, `notes`, `metadata`.

## Test plan (pytest; offline)

- Location: `tests/evals/phase_0_*.py`
- Common setup:

  - Set env `WINE_SEARCH_CALLS_PER_RUN=0`.
  - Fix random seed (model wrapper or test harness) for repeatability.
  - Load N YAML cases from `.agents/docs/wines/`.

- Tests:

  - **metrics_persistence_smoke**: Run a no-op agent step (or minimal function) and assert `.metrics.json` is written and parseable.
  - **normalized_name_exact_when_labeled**: For items with `normalized_name` set, assert agent output name normalization equals label. Log mismatches to metrics.
  - **nv_vintage_handling**: For NV cases (`veuve_ambal_rose.yaml`, `umbretum_brut_nature.yaml`), assert output vintage is null/"NV" (no fabricated year).
  - **grapes_presence_when_labeled**: If `grapes` label provided, assert output contains labeled variety tokens (case-insensitive, accent-normalized), not strict F1 yet.
  - **spelling_min_check**: If `corrections.spelling_corrections` present, assert normalized name matches corrected form.
  - **determinism_seeded**: Same input twice under fixed seed → same output hash.

- Non-goals in Phase 0:
  - No gates enforced (only log). No external search. No Qdrant. No CSV export.

## Metrics to record (log-only in Phase 0)

- `normalized_name_match` (0/1 per case).
- `nv_vintage_ok` (0/1 per NV case).
- `grapes_contains_label` (0/1 when label provided).
- `spelling_corrected` (0/1 when correction present).
- `determinism_ok` (0/1 aggregate).

## Acceptance criteria

- `.metrics.json` persists and includes the metrics above.
- All tests pass offline with the provided 10 YAMLs.
- Determinism holds under fixed seed.

## Follow-ups (Phase 1 prep)

- Add 1–2 ambiguous queries for the disambiguation gate.
- Introduce tiny alias list (region/appellation) for later accuracy checks.
