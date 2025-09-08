# Evals Epic — Brainstormed Hook Placements (20–30)

Below are concrete places to add evaluations, grouped by purpose. Each item lists where in the codebase and a 1–2 line pythonic pseudocode sketch.

## 1) Disambiguation & Validation (Stage 0)

1. Disambiguation result correctness (tuned)
   - Where: `examples/research/wine_agent.py` (Phase 0 Step 1, after wine-disambiguator output)

```python
ok, reason = disamb_ok(result)  # one_exact | needs_clarification | overcommit
record_event("disamb_reason", reason)
assert ok or reason == "needs_clarification"
```

2. Disambiguation overcommit check (folded into #1)
   - Where: `examples/research/wine_agent.py` (Phase 0 Step 1)

```python
# handled by disamb_ok(...) returning reason="overcommit"
```

3. Validation decision accuracy (tuned)
   - Where: `examples/research/wine_agent.py` (Phase 0 Step 2, after wine-validator)

```python
record_metric("validation_expected", int(expected_pass))
record_metric("validation_actual", int(actual_pass))
record_metric("validation_match", int(expected_pass == actual_pass))
```

4. Early-stop on ambiguity enforcement (gate helper)
   - Where: `examples/research/wine_agent.py` (transition between Phase 0 and Phase 1)

```python
gate_or_halt("ambiguity_gate", not needs_clarification, detail="NEED_CLARIFICATION")
```

5. Failure reason capture for diagnostics
   - Where: `examples/research/wine_agent.py` (validator failure branch)

```python
record_event("validation_fail_reason", reason)
```

## 2) Planning & TODO Hygiene (Stage 1)

6. Required tasks presence
   - Where: `src/deepagents/tools.py::write_todos` usage sites in `examples/research/wine_agent.py`

```python
assert includes_all_required_fields(todos)
```

7. First task must be normalized_name
   - Where: `examples/research/wine_agent.py` (immediately after TODO creation)

```python
assert first_in_progress(todos).name == "normalized_name"
```

8. Proper task lifecycle transitions (tuned with FSM)
   - Where: `src/deepagents/state.py` (when updating todos)

```python
assert fsm_allows(prev, nxt), f"illegal transition {prev}->{nxt}"
record_counter("todo_transition", 1)
```

9. Language discipline note in plan
   - Where: `examples/research/wine_agent.py` (Phase 1 instructions handling)

```python
assert plan_mentions_output_language(question_language)
```

## 3) Field Research — normalized_name (Stage 2 core)

10. Exact label match to request

- Where: `examples/research/wine_agent.py` (after normalized_name sub-task)

```python
assert normalize(found_name) == normalize(requested_name)
```

11. Vintage consistency for normalized_name (tuned NV-aware)

- Where: `examples/research/wine_agent.py` (normalized_name checkpoint)

```python
assert vintage_match(requested_vintage, found_vintage)  # NV & ranges supported
```

12. Stop-on-mismatch compliance (gate helper)

- Where: `examples/research/wine_agent.py` (checkpoint gate before other fields)

```python
gate_or_halt("normalized_name_gate", not normalized_name_mismatch)
```

13. Citation presence for normalized_name

- Where: `examples/research/wine_agent.py` (field output assembler)

```python
assert has_at_least_one_citation(field_output)
```

## 4) Field Research — core fields

14. Producer exactness

- Where: `examples/research/wine_agent.py` (producer sub-task)

```python
assert exact_string(producer_found, producer_expected)
```

15. Region mapping to canonical set

- Where: `examples/research/wine_agent.py` (region sub-task)

```python
assert region_found in canonical_regions
```

16. Appellation correctness against aliases

- Where: `examples/research/wine_agent.py` (appellation sub-task)

```python
assert alias_eq(appellation_found, appellation_expected)
```

17. Vintage numeric validity

- Where: `examples/research/wine_agent.py` (vintage sub-task)

```python
assert isinstance(vintage, int) and 1900 <= vintage <= current_year
```

18. Grapes composition F1 & percentages sanity (tuned)

- Where: `examples/research/wine_agent.py` (grapes sub-task)

```python
record_metric("grapes_f1", f1_score(gold_grapes, found_grapes))
assert percent_sum_in_range(found_grapes, soft=(95,105), hard=(90,110))
```

19. Citation sufficiency per core field

- Where: `examples/research/wine_agent.py` (after each field)

```python
assert all_required_fields_have_citations(wine_json)
```

## 5) Search/Retrieval & Cache/Qdrant

20. External search call budget (gate)

- Where: `examples/research/wine_agent.py::internet_search` tool

```python
gate_or_halt("search_budget_gate", within_budget("internet_search_calls", max_calls))
```

21. Preferred domains ratio

- Where: `examples/research/wine_agent.py::internet_search` tool

```python
record_metric("preferred_domain_ratio", ratio(urls, preferred_domains))
```

22. Cache hit rate for sources

- Where: cache tools (`cache_get_source`, `cache_list_sources`)

```python
record_metric("cache_hit", hit)
```

23. Qdrant retrieval recall@k (when configured)

- Where: `src/deepagents/qdrant/tools.py::qdrant_retrieve`

```python
record_metric("qdrant_recall@k", recall_at_k(gold_ids, retrieved_ids))
```

24. Qdrant sync integrity

- Where: `src/deepagents/qdrant/tools.py::qdrant_sync_cache`

```python
assert synced_count == expected_count
```

25. Reranker effectiveness (NEW 38)

- Where: `src/deepagents/search/base.py` after reranking

```python
record_metric("rerank_mrr_delta", mrr_after - mrr_before)
```

26. Trusted source share (NEW 39)

- Where: `examples/research/wine_agent.py::internet_search`

```python
record_metric("trusted_source_share", trusted(urls)/max(len(urls),1))
```

27. Recency guard (NEW 40)

- Where: same as above

```python
gate_or_halt("stale_source_gate", not using_stale_sources(urls, max_age_years=7))
```

28. Cross-source contradiction check (NEW 41)

- Where: before final synthesis

```python
contradictions = count_contradictions(passages)
record_metric("source_contradictions", contradictions)
assert contradictions <= threshold
```

## 6) Generation, JSON, and Attribution

29. Faithfulness to provided context (+ utilization) (tuned)

- Where: `src/deepagents/graph.py` (post-model boundary or wrapper)

```python
record_metric("faithfulness", ragas_faithfulness(context, answer))
record_metric("context_utilization", used_tokens/context_tokens)
```

30. Attribution coverage with claim counts (tuned)

- Where: `examples/research/wine_agent.py` (before final wine.json write)

```python
n_claims, n_cited = count_atomic_claims(answer), count_cited_claims(answer)
record_metric("claims_supported_ratio", n_cited / max(n_claims,1))
```

31. JSON schema adherence for wine.json

- Where: `examples/research/wine_agent.py` (on write of wine.json)

```python
assert validate_against_schema(wine_json, wine_schema)
```

32. wine.json version & deterministic serialization (NEW 51–52)

- Where: serializer

```python
assert wine_json["schema_version"] == CURRENT_SCHEMA
assert serialized == deterministic_serialize(wine_json)
```

33. JSON/CSV injection safety (NEW 53)

- Where: export finalizer

```python
assert not starts_with_risky_chars(any_text_fields)
```

## 7) State & Transitions (Agentic correctness)

34. Phase ordering compliance

- Where: `examples/research/wine_agent.py` (between phases)

```python
assert not phase2_started_before(normalized_name_confirmed)
```

35. Clarification path halts correctly

- Where: `examples/research/wine_agent.py` (disambiguator NEED CLARIFICATION)

```python
gate_or_halt("ambiguity_gate", requests_user_clarification_and_halts(flow_state))
```

36. Tool retries/backoff (tuned)

- Where: `src/deepagents/graph.py` (tool call wrapper)

```python
record_metric("tool_retries", retries)
record_metric("tool_backoff_total_ms", backoff_ms)
```

37. Action minimality (NEW 44)

- Where: `src/deepagents/graph.py` after a plan step

```python
assert not extraneous_tool_calls(step_plan, observed_calls)
```

38. Branch stability cap (NEW 45)

- Where: agent loop

```python
record_metric("branch_backtracks", backtracks); gate_or_halt("branch_backtrack_gate", backtracks <= cap)
```

39. Tool schema conformance (NEW 46)

- Where: tools boundary

```python
assert tool_args_match_schema(tool_name, args)
```

40. Deterministic retries (NEW 47)

- Where: tool wrapper

```python
assert deterministic_on_retry(tool_name, args, hash(output))
```

## 8) Export Pipeline (WooCommerce CSV)

41. Pre-export validation pass rate (tuned: log rule ids)

- Where: `examples/research/export/woocommerce_finalizer.py::validate_wine`

```python
errors = validate_wine(wine); record_event("export_validation_errors", errors); assert errors == []
```

42. Mapping coverage (countries/types/grapes)

- Where: `examples/research/export/woocommerce_finalizer.py`

```python
record_metric("mapping_coverage", mapped_fields / total_fields)
```

43. ES/EN parity and WPML link

- Where: `examples/research/export/woocommerce_finalizer.py`

```python
assert has_wpml_link(en_row, es_sku)
```

44. Delimiter and pipe correctness

- Where: `examples/research/export/woocommerce_finalizer.py` (post-write)

```python
assert csv_uses_semicolons_and_pipes(output_files)
```

45. Bilingual semantic parity (NEW 55)

- Where: export pipeline

```python
assert bilingual_semantic_equivalence(en_text, es_text) >= 0.9
```

## 9) Ontologies & Normalization

46. Synonym canonicalization hit rate (NEW 48)

- Where: field assemblers

```python
record_metric("synonym_canon_rate", canon_hits/max(total,1))
```

47. Region-country consistency (NEW 49)

- Where: region sub-task

```python
assert region_country_consistent(region_found, country_found)
```

48. Appellation–style compatibility (NEW 50)

- Where: appellation sub-task

```python
assert style_allowed_by_appellation(style, appellation_found)
```

## 10) Internationalization & Safety

49. Output language fidelity (NEW 54)

- Where: final synthesis

```python
assert output_language(answer) == question_language
```

50. Alcohol/health disclaimer policy (NEW 56)

- Where: recommendation stage

```python
assert includes_required_disclaimer(answer, context)
```

51. Age-appropriateness guard (NEW 57)

- Where: Stage 0

```python
assert not violates_age_policy(user_context)
```

## 11) Performance, Cost & Determinism

52. Context utilization ratio (NEW 58)

- Where: post-model hook

```python
record_metric("context_utilization", used_tokens/context_tokens)
```

53. Prompt bloat detector (NEW 59)

- Where: model wrapper

```python
gate_or_halt("prompt_bloat_gate", prompt_tokens <= prompt_cap)
```

54. Cache invalidation correctness (NEW 60)

- Where: cache layer

```python
assert cache_etag == origin_etag
```

55. Fault injection pass rate (NEW 61)

- Where: tool wrapper (test mode)

```python
record_metric("fault_recovery_rate", recovered/max(injected_faults,1))
```

56. Seeded determinism (NEW 62)

- Where: test harness

```python
assert stable_under_seed(hash(inputs), hash(outputs))
```

57. Infinite-loop tripwire (NEW 63)

- Where: agent loop

```python
assert not detect_cycle(action_history)
```

## 12) Provenance & HITL

58. Claim→source alignment map (NEW 64)

- Where: before finalize

```python
record_blob("claim_source_map.json", align_claims_to_sources(answer, passages))
```

59. URL canonicalization rate (NEW 65)

- Where: search/citation normalizer

```python
record_metric("canonicalization_rate", canon_count/max(total_urls,1))
```

60. Link-rot early warning (NEW 66)

- Where: nightly job

```python
record_metric("dead_link_ratio", dead/max(checked,1))
```

61. HITL escalation readiness (NEW 67)

- Where: any gate violation

```python
assert triggers_hitl(reason_codes) == expected_policy
```

62. Feedback capture loop (NEW 68)

- Where: post-run

```python
enqueue_feedback_items(failures_for_labeling)
```

---

### Shared metrics & gate plumbing (sketch)

- Minimal `src/deepagents/metrics.py`:

```python
from dataclasses import dataclass, field
from time import time
from typing import Any, Dict, List

@dataclass
class Metrics:
    counters: Dict[str, int] = field(default_factory=dict)
    metrics:  Dict[str, float] = field(default_factory=dict)
    timers:   Dict[str, float] = field(default_factory=dict)
    events:   List[Dict[str, Any]] = field(default_factory=list)
    blobs:    Dict[str, Any] = field(default_factory=dict)
    def record_counter(self, name: str, inc: int = 1): self.counters[name] = self.counters.get(name, 0) + inc
    def record_metric(self, name: str, value: float): self.metrics[name] = float(value)
    def record_timer(self, name: str, start_ts: float): self.timers[name] = self.timers.get(name, 0.0) + (time() - start_ts) * 1000.0
    def record_event(self, name: str, payload: Any): self.events.append({"name": name, "payload": payload, "ts": time()})
    def record_blob(self, name: str, obj: Any): self.blobs[name] = obj
    def as_dict(self) -> Dict[str, Any]:
        return {"counters": self.counters, "metrics": self.metrics, "timers": self.timers, "events": self.events, "blobs": list(self.blobs.keys())}
```

- Wire in once (e.g., in `graph.py`) and persist:

```python
state.metrics = Metrics()
record_metric  = state.metrics.record_metric
record_counter = state.metrics.record_counter
record_timer   = state.metrics.record_timer
record_event   = state.metrics.record_event
record_blob    = state.metrics.record_blob
state.files[".metrics.json"] = json.dumps(state.metrics.as_dict(), ensure_ascii=False, indent=2)
```

- Gate helper:

```python
class AgentGateError(RuntimeError):
    def __init__(self, gate: str, detail: str = ""): super().__init__(f"[GATE:{gate}] {detail}"); self.gate, self.detail = gate, detail

def gate_or_halt(gate_name: str, condition: bool, detail: str = "") -> bool:
    record_event("gate_check", {"gate": gate_name, "ok": condition, "detail": detail})
    if not condition: raise AgentGateError(gate_name, detail)
    return True
```

- Optional policy file `evals/suites/gates.yaml` for severities/thresholds.

---

Notes:

- “record\_\*”/gate helpers are placeholders for a lightweight metrics sink into `.metrics.json` via `DeepAgentState.files` before `persist_run`.
- Qdrant optionality: no-op the Qdrant hooks when not configured.
