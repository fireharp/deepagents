# Phase 1 — Ambiguity & Validation Gates (biggest stability win)

Objective: Enforce correctness at the very start of the pipeline by handling ambiguous requests and validating feasibility before planning. Halt safely with reason codes; log detailed metrics.

## Scope

- Implement ambiguity and validation gates (log + enforce in tests; warn-only in dev if needed).
- Standardize disambiguation outcomes and validation pass/fail logging.
- No changes to model wiring; only evaluation hooks + tests.

## Hooks to implement (from brainstorming)

- (1) Disambiguation outcome + reason code
  - `ok, reason = disamb_ok(result)` → reason ∈ {"one_exact","needs_clarification","overcommit"}
  - `record_event("disamb_reason", reason)`
  - `gate_or_halt("ambiguity_gate", not needs_clarification, detail=reason)`
- (3) Validation expected vs actual parity
  - `record_metric("validation_expected", int(expected_pass))`
  - `record_metric("validation_actual", int(actual_pass))`
  - `record_metric("validation_match", int(expected_pass == actual_pass))`
- (5) Validation failure reason
  - `record_event("validation_fail_reason", reason)`
- (12) Normalized-name mismatch gate (pre-Phase-2)
  - `gate_or_halt("normalized_name_gate", not normalized_name_mismatch)`

## Datasets

- Directory: `test_data/evals/phase1/`
- Two YAML sets:
  1. `disambiguation/*.yaml`
     - Fields: `query`, `expected_outcome` ("one_exact"|"needs_clarification"|"overcommit"), `gold_name` (when one_exact), optional `notes`.
  2. `validation/*.yaml`
     - Fields: `query`, `expected_pass` (bool), `reason_code` (string), optional `notes`.
- Seed size: 12–20 cases total (balanced).

## Tests (pytest; offline where possible)

- Location: `tests/evals/test_phase1_*.py`
- Env: `WINE_SEARCH_CALLS_PER_RUN=0` for offline disamb/validation stubs; or cache-backed if needed.
- Tests:
  - `test_disamb_outcomes`: Each disambiguation case returns the labeled outcome; when `one_exact`, gold normalized name equals predicted.
  - `test_ambiguity_gate_behavior`: For `needs_clarification`, gate halts and logs reason; for `overcommit`, gate halts.
  - `test_validation_parity`: Each validation case logs expected/actual and sets `validation_match==1` when equal.
  - `test_norm_name_gate`: If `normalized_name_mismatch==True` (synthetic runner flag), gate halts prior to Phase 2.

## Metrics

- Counters/metrics:
  - `disamb_one_exact_total`, `disamb_needs_clarification_total`, `disamb_overcommit_total` (increment per outcome)
  - `validation_expected`, `validation_actual`, `validation_match`
  - `ambiguity_gate_halts`, `normalized_name_gate_halts`
- Events:
  - `disamb_reason`, `validation_fail_reason`, gate events with details.

## Acceptance

- Disambiguation accuracy ≥ 0.9 on seed set (`one_exact` cases match gold normalized name).
- Ambiguity gate halts 100% on `needs_clarification` and `overcommit` cases.
- Validation parity: `validation_match` ≥ 0.9 on seed set.
- `.metrics.json` includes outcome counts and gate events.

## Implementation Notes

- Reuse Phase 0 `Metrics` and `gate_or_halt` machinery.
- Provide a small stub runner for Phase 1 that:
  - Simulates disambiguation outcomes deterministically based on YAML (no external search)
  - Simulates validation pass/fail via labels
- Keep gates enforceable only inside tests to avoid breaking dev flows initially (config flag to toggle hard/soft gates).
