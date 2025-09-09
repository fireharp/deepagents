"""Integration tests for ambiguity and validation evaluation system."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from deepagents.evals.ambiguity_validation import run_ambiguity_validation_eval
from deepagents.evals.metrics import gate_or_halt, Metrics


class TestAmbiguityValidationIntegration:
    """Test the complete ambiguity and validation evaluation pipeline."""

    def test_full_ambiguity_validation_evaluation(self):
        """Test running the complete ambiguity and validation evaluation."""
        test_dir = Path(__file__).parent.parent.parent / "test_data" / "evals"

        if not (test_dir / "ambiguity_validation").exists():
            pytest.skip("Ambiguity validation test data not available")

        # Set offline mode
        os.environ["WINE_SEARCH_CALLS_PER_RUN"] = "0"

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            metrics = run_ambiguity_validation_eval(
                str(test_dir), seed=42, metrics_path=tmp.name
            )

        # Verify metrics structure
        assert isinstance(metrics, Metrics)
        assert len(metrics.metrics) > 0, "No metrics recorded"
        assert len(metrics.events) > 0, "No events recorded"

        # Check that metrics file was created and is valid JSON
        with open(tmp.name, "r") as f:
            data = json.load(f)

        assert "timestamp" in data
        assert "metrics" in data
        assert "events" in data

        # Verify key metrics are present
        required_metrics = [
            "disamb_outcome_total",
            "validation_parity_total",
        ]

        for metric in required_metrics:
            assert metric in data["metrics"], f"Required metric {metric} not found"

        # Verify key events are present
        event_names = {e["name"] for e in data["events"]}
        required_events = ["gate", "disamb_reason"]

        for event_name in required_events:
            assert event_name in event_names, f"Required event {event_name} not found"

        # Clean up
        os.unlink(tmp.name)

    def test_acceptance_criteria(self):
        """Test that ambiguity validation meets the acceptance criteria from the spec."""
        test_dir = Path(__file__).parent.parent.parent / "test_data" / "evals"

        if not (test_dir / "ambiguity_validation").exists():
            pytest.skip("Ambiguity validation test data not available")

        os.environ["WINE_SEARCH_CALLS_PER_RUN"] = "0"

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            metrics = run_ambiguity_validation_eval(
                str(test_dir), metrics_path=tmp.name
            )

        # 1. Disambiguation accuracy ≥ 0.9 on seed set
        disamb_total = metrics.metrics.get("disamb_outcome_total", 0)
        disamb_correct = metrics.metrics.get("disamb_outcome_correct", 0)

        if disamb_total > 0:
            disamb_accuracy = disamb_correct / disamb_total
            assert (
                disamb_accuracy >= 0.9
            ), f"Disambiguation accuracy {disamb_accuracy:.2f} < 0.9"

        # 2. Gold name matching for one_exact cases
        gold_total = metrics.metrics.get("disamb_gold_name_total", 0)
        gold_matches = metrics.metrics.get("disamb_gold_name_match", 0)

        if gold_total > 0:
            gold_accuracy = gold_matches / gold_total
            assert gold_accuracy >= 0.9, f"Gold name accuracy {gold_accuracy:.2f} < 0.9"

        # 3. Ambiguity gate halts on needs_clarification and overcommit
        halts = metrics.metrics.get("ambiguity_gate_halts", 0)
        needs_clarif = metrics.metrics.get("disamb_needs_clarification_total", 0)
        overcommit = metrics.metrics.get("disamb_overcommit_total", 0)
        expected_halts = needs_clarif + overcommit

        if expected_halts > 0:
            assert (
                halts == expected_halts
            ), f"Expected {expected_halts} ambiguity gate halts, got {halts}"

        # 4. Validation parity ≥ 0.9
        val_total = metrics.metrics.get("validation_parity_total", 0)
        val_correct = metrics.metrics.get("validation_parity_correct", 0)

        if val_total > 0:
            val_parity = val_correct / val_total
            assert val_parity >= 0.9, f"Validation parity {val_parity:.2f} < 0.9"

        # 5. Metrics JSON includes outcome counts and gate events
        assert metrics.metrics.get("disamb_one_exact_total", 0) > 0
        assert metrics.metrics.get("disamb_needs_clarification_total", 0) > 0
        assert metrics.metrics.get("disamb_overcommit_total", 0) > 0

        gate_events = [e for e in metrics.events if e["name"] == "gate"]
        assert len(gate_events) > 0, "No gate events recorded"

        # Clean up
        os.unlink(tmp.name)


class TestGateEnforcement:
    """Test gate enforcement functionality."""

    def test_gate_enforcement_disabled_by_default(self):
        """Test that gates don't enforce by default (log-only mode)."""
        metrics = Metrics()

        # Should not raise exception even when condition is False
        result = gate_or_halt("test_gate", False, detail="test", sink=metrics)
        assert result is True

        # Should log the event
        gate_events = [e for e in metrics.events if e["name"] == "gate"]
        assert len(gate_events) == 1
        assert not gate_events[0]["data"]["passed"]
        assert gate_events[0]["data"]["gate"] == "test_gate"

    def test_gate_enforcement_when_enabled(self):
        """Test that gates can enforce when explicitly enabled."""
        metrics = Metrics()

        # Should pass when condition is True
        result = gate_or_halt(
            "test_gate", True, detail="test", sink=metrics, enforce=True
        )
        assert result is True

        # Should raise exception when condition is False and enforce=True
        with pytest.raises(AssertionError, match="Gate 'test_gate' failed"):
            gate_or_halt(
                "test_gate", False, detail="test failure", sink=metrics, enforce=True
            )

    def test_deterministic_behavior(self):
        """Test that ambiguity validation evaluation is deterministic."""
        test_dir = Path(__file__).parent.parent.parent / "test_data" / "evals"

        if not (test_dir / "ambiguity_validation").exists():
            pytest.skip("Ambiguity validation test data not available")

        os.environ["WINE_SEARCH_CALLS_PER_RUN"] = "0"

        # Run twice with same seed
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp1:
            metrics1 = run_ambiguity_validation_eval(
                str(test_dir), seed=42, metrics_path=tmp1.name
            )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp2:
            metrics2 = run_ambiguity_validation_eval(
                str(test_dir), seed=42, metrics_path=tmp2.name
            )

        # Results should be identical
        assert metrics1.metrics == metrics2.metrics, "Metrics not deterministic"

        # Event counts should match (events may have timestamps, so count by name)
        events1_by_name = {}
        for event in metrics1.events:
            name = event["name"]
            events1_by_name[name] = events1_by_name.get(name, 0) + 1

        events2_by_name = {}
        for event in metrics2.events:
            name = event["name"]
            events2_by_name[name] = events2_by_name.get(name, 0) + 1

        assert events1_by_name == events2_by_name, "Events not deterministic"

        # Clean up
        os.unlink(tmp1.name)
        os.unlink(tmp2.name)
