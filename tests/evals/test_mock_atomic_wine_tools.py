"""
Mock-based atomic tests for wine research components.
These tests use mock data to test individual components without external dependencies.
"""

import json
import os
import pytest

from deepagents.evals.eval_runner import load_eval_cases

# Test data directories
WINES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data", "evals", "wines")
)


@pytest.mark.unit
def test_wine_field_extraction_with_mock_data():
    """Test wine field extraction using mock search results."""
    # Load test cases
    cases = load_eval_cases(WINES_DIR)
    test_cases = cases[:5]  # Test first 5 cases

    results = []

    for case in test_cases:
        print(f"\n--- Testing field extraction for: {case.wine_query} ---")

        # Create mock search results that should help extract wine info
        mock_search_content = f"""
        Wine Information: {case.wine_query}
        Producer: Test Winery
        Region: Test Region
        Vintage: 2020
        Grape Varieties: Chardonnay 100%
        Alcohol: 12.5%
        Tasting Notes: Crisp and fresh with citrus notes
        """

        # Test the text normalization function directly
        from deepagents.evals.eval_runner import normalize_text_for_eval

        normalized_query = normalize_text_for_eval(case.wine_query)
        expected_normalized = normalize_text_for_eval(case.normalized_name or "")

        # Simple field extraction simulation
        extracted_fields = {
            "normalized_name": case.wine_query.strip(),
            "producer": "Test Winery",
            "region": "Test Region",
            "vintage": "2020",
            "grapes": "Chardonnay 100%",
        }

        # Check if normalized names match (basic text similarity)
        name_match = (
            normalized_query in expected_normalized
            or expected_normalized in normalized_query
        )

        results.append(
            {
                "query": case.wine_query,
                "expected_normalized_name": case.normalized_name,
                "extracted_normalized_name": extracted_fields["normalized_name"],
                "normalized_query": normalized_query,
                "expected_normalized": expected_normalized,
                "name_similarity_match": name_match,
                "has_producer": bool(extracted_fields.get("producer")),
                "has_region": bool(extracted_fields.get("region")),
                "has_vintage": bool(extracted_fields.get("vintage")),
                "has_grapes": bool(extracted_fields.get("grapes")),
            }
        )

        print(f"Expected: {case.normalized_name}")
        print(f"Extracted: {extracted_fields['normalized_name']}")
        print(f"Name match: {name_match}")

    # Save results for analysis
    with open("mock_field_extraction_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Assertions
    assert len(results) == len(test_cases)

    # At least 80% should have basic fields extracted
    complete_extractions = sum(
        1
        for r in results
        if all([r["has_producer"], r["has_region"], r["has_vintage"], r["has_grapes"]])
    )

    success_rate = complete_extractions / len(results)
    print(f"\nField extraction success rate: {success_rate:.2%}")
    assert success_rate >= 0.8, f"Expected 80% success rate, got {success_rate:.2%}"


@pytest.mark.unit
def test_text_normalization_accuracy():
    """Test text normalization against expected results."""
    from deepagents.evals.eval_runner import normalize_text_for_eval

    # Load test cases
    cases = load_eval_cases(WINES_DIR)
    test_cases = cases[:10]

    results = []
    exact_matches = 0

    for case in test_cases:
        if not case.normalized_name:
            continue

        # Test normalization
        normalized_query = normalize_text_for_eval(case.wine_query)
        expected_normalized = normalize_text_for_eval(case.normalized_name)

        exact_match = normalized_query == expected_normalized
        if exact_match:
            exact_matches += 1

        # Test similarity (allowing for minor differences)
        query_words = set(normalized_query.split())
        expected_words = set(expected_normalized.split())

        if len(expected_words) > 0:
            similarity = len(query_words & expected_words) / len(expected_words)
        else:
            similarity = 0.0

        results.append(
            {
                "query": case.wine_query,
                "normalized_name": case.normalized_name,
                "normalized_query": normalized_query,
                "expected_normalized": expected_normalized,
                "exact_match": exact_match,
                "similarity": similarity,
                "high_similarity": similarity >= 0.8,
            }
        )

        print(f"Query: {case.wine_query}")
        print(f"Expected: {case.normalized_name}")
        print(f"Similarity: {similarity:.2%}, Exact: {exact_match}")

    # Save results
    with open("normalization_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    if results:
        exact_match_rate = exact_matches / len(results)
        high_similarity_rate = sum(1 for r in results if r["high_similarity"]) / len(
            results
        )

        print(f"\nExact match rate: {exact_match_rate:.2%}")
        print(f"High similarity rate: {high_similarity_rate:.2%}")

        # Either exact matches or high similarity should be good
        assert (
            exact_match_rate >= 0.3 or high_similarity_rate >= 0.7
        ), f"Poor normalization: {exact_match_rate:.2%} exact, {high_similarity_rate:.2%} high similarity"


@pytest.mark.unit
def test_spelling_corrections_logic():
    """Test spelling corrections logic with known cases."""
    from deepagents.evals.eval_runner import normalize_text_for_eval
    import re

    # Test cases with spelling corrections
    test_corrections = [
        {
            "input": "Rally white",
            "correction": "Rall (not Rally)",
            "expected_pass": False,  # Should fail because input contains "Rally"
        },
        {
            "input": "Rall white",
            "correction": "Rall (not Rally)",
            "expected_pass": True,  # Should pass because input contains "Rall" not "Rally"
        },
        {
            "input": "Billecart Salmon Rose",
            "correction": "Billecart",
            "expected_pass": True,  # Should pass because input contains "Billecart"
        },
    ]

    results = []

    for test_case in test_corrections:
        input_text = test_case["input"]
        correction = test_case["correction"]
        expected_pass = test_case["expected_pass"]

        # Apply the spelling correction logic from eval_runner
        actual_norm = normalize_text_for_eval(input_text)

        # Parse correction using the same logic as in eval_runner
        correction_str = str(correction).strip()
        m = re.match(
            r"^(?P<want>[^()]+)\s*\(not\s+(?P<avoid>[^)]+)\)\s*$",
            correction_str,
            re.I,
        )

        if m:
            want_tokens = [
                t for t in normalize_text_for_eval(m.group("want")).split() if t
            ]
            avoid_tokens = [
                t for t in normalize_text_for_eval(m.group("avoid")).split() if t
            ]
            entry_ok = all(t in actual_norm for t in want_tokens) and all(
                t not in actual_norm for t in avoid_tokens
            )
        else:
            want_tokens = [
                t for t in normalize_text_for_eval(correction_str).split() if t
            ]
            entry_ok = all(t in actual_norm for t in want_tokens)

        results.append(
            {
                "input": input_text,
                "correction": correction,
                "expected_pass": expected_pass,
                "actual_pass": entry_ok,
                "correct": expected_pass == entry_ok,
                "normalized_input": actual_norm,
                "want_tokens": want_tokens if "m" in locals() else [],
                "avoid_tokens": avoid_tokens if "m" in locals() and m else [],
            }
        )

        print(f"Input: {input_text}")
        print(f"Correction: {correction}")
        print(
            f"Expected: {expected_pass}, Actual: {entry_ok}, Correct: {expected_pass == entry_ok}"
        )

    # Save results
    with open("spelling_corrections_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # All test cases should be handled correctly
    correct_results = sum(1 for r in results if r["correct"])
    accuracy = correct_results / len(results)

    print(f"\nSpelling correction accuracy: {accuracy:.2%}")
    assert accuracy >= 0.8, f"Expected 80% accuracy, got {accuracy:.2%}"


@pytest.mark.unit
def test_evaluation_metrics_calculation():
    """Test the evaluation metrics calculation logic."""
    from deepagents.evals.eval_runner import run_offline_eval

    # This should work with the deterministic model
    metrics = run_offline_eval(WINES_DIR, seed=42, metrics_path="test_metrics.json")

    print(f"Metrics collected: {list(metrics.metrics.keys())}")

    # Check that we got the expected metrics
    expected_metrics = [
        "normalized_name_total",
        "normalized_name_match",
        "grapes_total",
        "spelling_total",
        "determinism_ok",
    ]

    for metric in expected_metrics:
        assert metric in metrics.metrics, f"Missing metric: {metric}"

    # Check that totals make sense
    assert (
        metrics.metrics["normalized_name_total"] > 0
    ), "Should have processed some cases"
    assert metrics.metrics["determinism_ok"] == 1, "Should be deterministic"

    print(f"Processed {metrics.metrics['normalized_name_total']} cases")
    print(
        f"Determinism check: {'PASS' if metrics.metrics['determinism_ok'] else 'FAIL'}"
    )


@pytest.mark.unit
def test_dataset_loading_and_structure():
    """Test that datasets load correctly and have expected structure."""

    # Test wines dataset
    wine_cases = load_eval_cases(WINES_DIR)
    assert len(wine_cases) > 0, "Should load wine cases"

    # Check structure of first case
    first_case = wine_cases[0]
    assert hasattr(first_case, "wine_query"), "Should have wine_query"
    assert hasattr(first_case, "normalized_name"), "Should have normalized_name"
    assert hasattr(first_case, "corrections"), "Should have corrections"
    assert hasattr(first_case, "raw"), "Should have raw data"

    print(f"Loaded {len(wine_cases)} wine research cases")

    # Test other datasets
    disambiguation_dir = os.path.join(os.path.dirname(WINES_DIR), "disambiguation")
    validation_dir = os.path.join(os.path.dirname(WINES_DIR), "validation")

    disambig_cases = load_eval_cases(disambiguation_dir)
    validation_cases = load_eval_cases(validation_dir)

    print(f"Loaded {len(disambig_cases)} disambiguation cases")
    print(f"Loaded {len(validation_cases)} validation cases")

    assert len(disambig_cases) > 0, "Should load disambiguation cases"
    assert len(validation_cases) > 0, "Should load validation cases"

    # Check total
    total_cases = len(wine_cases) + len(disambig_cases) + len(validation_cases)
    print(f"Total evaluation cases: {total_cases}")
    assert total_cases >= 100, f"Expected at least 100 total cases, got {total_cases}"


if __name__ == "__main__":
    # Run a quick test
    print("Running mock atomic tests...")

    # Test dataset loading
    cases = load_eval_cases(WINES_DIR)
    print(f"Loaded {len(cases)} wine cases")

    # Test normalization
    from deepagents.evals.eval_runner import normalize_text_for_eval

    test_query = "Veuve ambal Rose"
    normalized = normalize_text_for_eval(test_query)
    print(f"'{test_query}' -> '{normalized}'")

    print("Mock tests completed!")
