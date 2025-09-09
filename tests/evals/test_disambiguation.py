"""Tests for disambiguation functionality."""

import os
import tempfile
from pathlib import Path

import pytest

from deepagents.evals.ambiguity_validation import (
    DisambiguationCase,
    disambiguate_query,
    load_disambiguation_cases,
    run_ambiguity_validation_eval,
)


class TestDisambiguationLogic:
    """Test the core disambiguation logic."""

    def test_one_exact_cases(self):
        """Test queries that should return one_exact outcome."""
        test_cases = [
            "Domaine de la Romanee-Conti Montrachet 2018",
            "Caymus Cabernet Sauvignon 2020",
            "Opus One 2019",
            "Screaming Eagle Cabernet Sauvignon 2018",
        ]

        for query in test_cases:
            outcome, reason = disambiguate_query(query)
            assert (
                outcome == "one_exact"
            ), f"Query '{query}' should be one_exact, got {outcome}"
            assert "specific" in reason.lower() or "producer" in reason.lower()

    def test_needs_clarification_cases(self):
        """Test queries that should return needs_clarification outcome."""
        test_cases = [
            "Chardonnay",
            "Bordeaux red wine",
            "Pinot Noir from Oregon",
            "Spanish Tempranillo",
        ]

        for query in test_cases:
            outcome, reason = disambiguate_query(query)
            assert (
                outcome == "needs_clarification"
            ), f"Query '{query}' should need clarification, got {outcome}"
            assert "generic" in reason.lower() or "detail" in reason.lower()

    def test_overcommit_cases(self):
        """Test queries that should return overcommit outcome."""
        test_cases = [
            "Domaine de la Romanee-Conti Montrachet 2018 from the specific vineyard plot Les Chevaliers",
            "Caymus Cabernet Sauvignon 2020 but from Bordeaux region with 15% alcohol",
            "Barolo from Giuseppe Rinaldi harvested on October 15th 2019 at 3:47 PM",
            "Wine from the planet Mars vintage 3021",
        ]

        for query in test_cases:
            outcome, reason = disambiguate_query(query)
            assert (
                outcome == "overcommit"
            ), f"Query '{query}' should be overcommit, got {outcome}"
            assert "constraint" in reason.lower() or "conflict" in reason.lower()


class TestDisambiguationCaseLoading:
    """Test loading disambiguation cases from YAML files."""

    def test_load_disambiguation_cases(self):
        """Test loading disambiguation test cases from directory."""
        # Use the actual test data we created
        test_dir = (
            Path(__file__).parent.parent.parent
            / "test_data"
            / "evals"
            / "ambiguity_validation"
            / "disambiguation"
        )

        if not test_dir.exists():
            pytest.skip(f"Test data directory not found: {test_dir}")

        cases = load_disambiguation_cases(str(test_dir))

        # Should have 12 cases (4 of each type)
        assert len(cases) >= 8, f"Expected at least 8 cases, got {len(cases)}"

        # Check case structure
        for case in cases:
            assert isinstance(case, DisambiguationCase)
            assert case.query
            assert case.expected_outcome in [
                "one_exact",
                "needs_clarification",
                "overcommit",
            ]

            # one_exact cases should have gold_name
            if case.expected_outcome == "one_exact":
                assert (
                    case.gold_name is not None
                ), f"one_exact case missing gold_name: {case.query}"


class TestDisambiguationEvaluation:
    """Test the full disambiguation evaluation pipeline."""

    def test_disamb_outcomes_accuracy(self):
        """Test that disambiguation outcomes match expected labels."""
        test_dir = Path(__file__).parent.parent.parent / "test_data" / "evals"

        if not (test_dir / "ambiguity_validation" / "disambiguation").exists():
            pytest.skip("Ambiguity validation test data not available")

        # Set offline mode
        os.environ["WINE_SEARCH_CALLS_PER_RUN"] = "0"

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            metrics = run_ambiguity_validation_eval(
                str(test_dir), metrics_path=tmp.name
            )

        # Check disambiguation accuracy
        total = metrics.metrics.get("disamb_outcome_total", 0)
        correct = metrics.metrics.get("disamb_outcome_correct", 0)

        assert total > 0, "No disambiguation cases processed"
        accuracy = correct / total if total > 0 else 0
        assert (
            accuracy >= 0.9
        ), f"Disambiguation accuracy {accuracy:.2f} below threshold 0.9"

        # Check that we have all outcome types
        assert metrics.metrics.get("disamb_one_exact_total", 0) > 0
        assert metrics.metrics.get("disamb_needs_clarification_total", 0) > 0
        assert metrics.metrics.get("disamb_overcommit_total", 0) > 0

        # Clean up
        os.unlink(tmp.name)

    def test_ambiguity_gate_behavior(self):
        """Test that ambiguity gate halts on needs_clarification and overcommit."""
        test_dir = Path(__file__).parent.parent.parent / "test_data" / "evals"

        if not (test_dir / "ambiguity_validation" / "disambiguation").exists():
            pytest.skip("Ambiguity validation test data not available")

        os.environ["WINE_SEARCH_CALLS_PER_RUN"] = "0"

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            metrics = run_ambiguity_validation_eval(
                str(test_dir), metrics_path=tmp.name
            )

        # Check gate events
        gate_events = [
            e
            for e in metrics.events
            if e["name"] == "gate" and e["data"]["gate"] == "ambiguity_gate"
        ]

        # Should have gate events for needs_clarification and overcommit cases
        failed_gates = [e for e in gate_events if not e["data"]["passed"]]

        # We expect at least 8 failed gates (4 needs_clarification + 4 overcommit)
        assert (
            len(failed_gates) >= 8
        ), f"Expected at least 8 failed ambiguity gates, got {len(failed_gates)}"

        # Check halt counter
        halts = metrics.metrics.get("ambiguity_gate_halts", 0)
        assert halts >= 8, f"Expected at least 8 ambiguity gate halts, got {halts}"

        # Clean up
        os.unlink(tmp.name)

    def test_gold_name_matching(self):
        """Test that one_exact cases match their gold normalized names."""
        test_dir = Path(__file__).parent.parent.parent / "test_data" / "evals"

        if not (test_dir / "ambiguity_validation" / "disambiguation").exists():
            pytest.skip("Ambiguity validation test data not available")

        os.environ["WINE_SEARCH_CALLS_PER_RUN"] = "0"

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            metrics = run_ambiguity_validation_eval(
                str(test_dir), metrics_path=tmp.name
            )

        # Check gold name matching
        total = metrics.metrics.get("disamb_gold_name_total", 0)
        matches = metrics.metrics.get("disamb_gold_name_match", 0)

        if total > 0:
            accuracy = matches / total
            assert (
                accuracy >= 0.9
            ), f"Gold name accuracy {accuracy:.2f} below threshold 0.9"

        # Clean up
        os.unlink(tmp.name)
