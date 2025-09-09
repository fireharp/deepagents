"""Tests for validation functionality."""

import os
import tempfile
from pathlib import Path

import pytest

from deepagents.evals.ambiguity_validation import (
    ValidationCase,
    load_validation_cases,
    run_ambiguity_validation_eval,
    validate_query_feasibility,
)


class TestValidationLogic:
    """Test the core validation logic."""

    def test_validation_pass_cases(self):
        """Test queries that should pass validation."""
        test_cases = [
            "Domaine de la Romanee-Conti Montrachet 2018",
            "Caymus Cabernet Sauvignon 2020",
            "Barolo from Giacomo Conterno 2017",
            "Dom Perignon Champagne 2012",
        ]

        for query in test_cases:
            should_pass, reason = validate_query_feasibility(query)
            assert should_pass, f"Query '{query}' should pass validation, got {reason}"
            assert "realistic" in reason.lower() or "feasible" in reason.lower()

    def test_validation_fail_cases(self):
        """Test queries that should fail validation."""
        test_cases = [
            "Wine from the planet Mars vintage 3021",
            "Chateau Nonexistent Bordeaux 1850",
            "Burgundy wine made from coconut grapes",
            "Champagne from California with 50% alcohol content",
        ]

        for query in test_cases:
            should_pass, reason = validate_query_feasibility(query)
            assert (
                not should_pass
            ), f"Query '{query}' should fail validation, but passed with {reason}"
            assert any(
                keyword in reason.lower()
                for keyword in [
                    "impossible",
                    "fictional",
                    "geographic",
                    "unrealistic",
                    "future",
                ]
            )


class TestValidationCaseLoading:
    """Test loading validation cases from YAML files."""

    def test_load_validation_cases(self):
        """Test loading validation test cases from directory."""
        test_dir = (
            Path(__file__).parent.parent.parent
            / "test_data"
            / "evals"
            / "ambiguity_validation"
            / "validation"
        )

        if not test_dir.exists():
            pytest.skip(f"Test data directory not found: {test_dir}")

        cases = load_validation_cases(str(test_dir))

        # Should have 8 cases (4 pass, 4 fail)
        assert len(cases) >= 6, f"Expected at least 6 cases, got {len(cases)}"

        # Check case structure
        for case in cases:
            assert isinstance(case, ValidationCase)
            assert case.query
            assert isinstance(case.expected_pass, bool)
            assert case.reason_code

        # Should have both pass and fail cases
        pass_cases = [c for c in cases if c.expected_pass]
        fail_cases = [c for c in cases if not c.expected_pass]

        assert len(pass_cases) > 0, "No pass cases found"
        assert len(fail_cases) > 0, "No fail cases found"


class TestValidationEvaluation:
    """Test the full validation evaluation pipeline."""

    def test_validation_parity(self):
        """Test that validation expected vs actual parity is high."""
        test_dir = Path(__file__).parent.parent.parent / "test_data" / "evals"

        if not (test_dir / "ambiguity_validation" / "validation").exists():
            pytest.skip("Ambiguity validation test data not available")

        # Set offline mode
        os.environ["WINE_SEARCH_CALLS_PER_RUN"] = "0"

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            metrics = run_ambiguity_validation_eval(
                str(test_dir), metrics_path=tmp.name
            )

        # Check validation parity
        total = metrics.metrics.get("validation_parity_total", 0)
        correct = metrics.metrics.get("validation_parity_correct", 0)

        assert total > 0, "No validation cases processed"
        parity = correct / total if total > 0 else 0
        assert parity >= 0.9, f"Validation parity {parity:.2f} below threshold 0.9"

        # Check that validation_match metric is recorded
        assert (
            "validation_match" in metrics.metrics
        ), "validation_match metric not recorded"

        # Clean up
        os.unlink(tmp.name)

    def test_validation_fail_reasons(self):
        """Test that validation failure reasons are recorded."""
        test_dir = Path(__file__).parent.parent.parent / "test_data" / "evals"

        if not (test_dir / "ambiguity_validation" / "validation").exists():
            pytest.skip("Ambiguity validation test data not available")

        os.environ["WINE_SEARCH_CALLS_PER_RUN"] = "0"

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            metrics = run_ambiguity_validation_eval(
                str(test_dir), metrics_path=tmp.name
            )

        # Check for validation failure reason events
        fail_events = [
            e for e in metrics.events if e["name"] == "validation_fail_reason"
        ]

        # Should have failure reasons recorded for fail cases
        assert len(fail_events) > 0, "No validation failure reasons recorded"

        # Check that reasons are meaningful
        for event in fail_events:
            reason = event["data"]
            assert isinstance(reason, str) and len(reason) > 0
            assert any(
                keyword in reason.lower()
                for keyword in [
                    "impossible",
                    "fictional",
                    "geographic",
                    "unrealistic",
                    "future",
                ]
            )

        # Clean up
        os.unlink(tmp.name)


class TestNormalizedNameGate:
    """Test the normalized name gate functionality."""

    def test_normalized_name_gate_default(self):
        """Test that normalized name gate passes by default."""
        test_dir = Path(__file__).parent.parent.parent / "test_data" / "evals"

        if not (test_dir / "ambiguity_validation").exists():
            pytest.skip("Ambiguity validation test data not available")

        os.environ["WINE_SEARCH_CALLS_PER_RUN"] = "0"

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            metrics = run_ambiguity_validation_eval(
                str(test_dir), metrics_path=tmp.name
            )

        # Check normalized name gate events
        gate_events = [
            e
            for e in metrics.events
            if e["name"] == "gate" and e["data"]["gate"] == "normalized_name_gate"
        ]

        assert len(gate_events) > 0, "No normalized name gate events recorded"

        # Should pass by default (no mismatch)
        passed_events = [e for e in gate_events if e["data"]["passed"]]
        assert len(passed_events) > 0, "Normalized name gate should pass by default"

        # Should not have halts in default case
        halts = metrics.metrics.get("normalized_name_gate_halts", 0)
        assert halts == 0, f"Expected 0 normalized name gate halts, got {halts}"

        # Clean up
        os.unlink(tmp.name)
