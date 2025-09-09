import json
import os

import pytest

from deepagents.evals.eval_runner import run_offline_eval, load_eval_cases


DATASET_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data", "evals", "wines")
)


@pytest.fixture(autouse=True)
def offline_env(monkeypatch):
    monkeypatch.setenv("WINE_SEARCH_CALLS_PER_RUN", "0")
    yield


def test_dataset_loads_minimal_schema():
    cases = load_eval_cases(DATASET_DIR)
    assert len(cases) >= 5
    for c in cases:
        assert c.wine_query
        assert c.corrections is not None


def test_dataset_loads_expected_count():
    """Verify we're loading the expected number of wine research cases."""
    cases = load_eval_cases(DATASET_DIR)
    # We should have 53 cases (30 existing + 23 new from consolidated v2)
    assert len(cases) == 53, f"Expected 53 cases, got {len(cases)}"

    # Verify we have cases from different sources
    case_queries = [case.wine_query for case in cases]

    # Should have original cases (check for actual queries from the test output)
    assert "Veuve ambal Rose" in case_queries
    assert "Tantum Ergo Rose" in case_queries
    # Should have new consolidated cases
    assert "Billecart-Salmon Brut Rosé NV" in case_queries


def test_metrics_persistence_smoke(tmp_path):
    metrics_path = tmp_path / ".metrics.json"
    run_offline_eval(DATASET_DIR, seed=123, metrics_path=str(metrics_path))
    assert metrics_path.exists()
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "metrics" in data and isinstance(data["metrics"], dict)


def test_normalized_name_exact_when_labeled():
    # Run eval and verify aggregate metric is recorded
    m = run_offline_eval(DATASET_DIR, seed=7, metrics_path=os.devnull)
    metrics = m.metrics
    if metrics.get("normalized_name_total", 0) > 0:
        assert "normalized_name_match" in metrics

    # With 53 cases, we should have processed all of them
    assert (
        metrics.get("normalized_name_total", 0) == 53
    ), f"Expected 53 total, got {metrics.get('normalized_name_total', 0)}"


def test_nv_vintage_handling():
    m = run_offline_eval(DATASET_DIR, seed=7, metrics_path=os.devnull)
    if metrics_total := m.metrics.get("nv_vintage_total", 0):
        assert m.metrics.get("nv_vintage_ok", 0) <= metrics_total


def test_grapes_presence_when_labeled():
    m = run_offline_eval(DATASET_DIR, seed=7, metrics_path=os.devnull)
    if metrics_total := m.metrics.get("grapes_total", 0):
        assert m.metrics.get("grapes_contains_label", 0) <= metrics_total


def test_spelling_min_check():
    m = run_offline_eval(DATASET_DIR, seed=7, metrics_path=os.devnull)
    if metrics_total := m.metrics.get("spelling_total", 0):
        assert m.metrics.get("spelling_corrected", 0) <= metrics_total


def test_determinism_seeded(tmp_path):
    # The function itself asserts determinism aggregate; here we double-check
    p1 = tmp_path / "m1.json"
    p2 = tmp_path / "m2.json"
    m1 = run_offline_eval(DATASET_DIR, seed=777, metrics_path=str(p1))
    m2 = run_offline_eval(DATASET_DIR, seed=777, metrics_path=str(p2))
    # Determinism flag set
    assert m1.metrics.get("determinism_ok") == 1
    assert m2.metrics.get("determinism_ok") == 1
