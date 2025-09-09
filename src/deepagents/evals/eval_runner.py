from __future__ import annotations

import hashlib
import json
import os
import random
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml

from .metrics import Metrics, gate_or_halt


@dataclass
class EvalCase:
    """A single labeled evaluation case for wine research testing."""

    wine_query: str
    normalized_name: Optional[str]
    vintage: Optional[str]
    grapes: Optional[str]
    corrections: Dict[str, Any]
    raw: Dict[str, Any]


# Backward-compat alias
LabeledCase = EvalCase


def load_eval_cases(path: str) -> List[EvalCase]:
    """Load evaluation YAML files from a directory or single file into EvalCase objects.

    Supports both:
    - Individual YAML files (legacy format)
    - Consolidated YAML files with 'cases' array (new format)
    - Directory containing YAML files
    """
    cases: List[EvalCase] = []

    if os.path.isfile(path):
        # Single file
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Check if this is a consolidated file with multiple cases
        if "cases" in data and isinstance(data["cases"], list):
            # New consolidated format
            for case_data in data["cases"]:
                cases.append(_create_eval_case(case_data))
        else:
            # Legacy individual case format
            cases.append(_create_eval_case(data))

    elif os.path.isdir(path):
        # Directory of files
        for filename in sorted(os.listdir(path)):
            if not filename.endswith(".yaml"):
                continue
            filepath = os.path.join(path, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # Check if this is a consolidated file with multiple cases
            if "cases" in data and isinstance(data["cases"], list):
                # New consolidated format
                for case_data in data["cases"]:
                    cases.append(_create_eval_case(case_data))
            else:
                # Legacy individual case format
                cases.append(_create_eval_case(data))

    return cases


def _create_eval_case(data: dict) -> EvalCase:
    """Create an EvalCase from a single case data dictionary."""
    return EvalCase(
        wine_query=str(data.get("wine_query", "")),
        normalized_name=data.get("normalized_name"),
        vintage=(
            data.get("vintage")
            if data.get("vintage") is None
            else str(data.get("vintage"))
        ),
        grapes=(
            data.get("grapes")
            if data.get("grapes") is None
            else str(data.get("grapes"))
        ),
        corrections=dict(data.get("corrections", {}) or {}),
        raw=data,
    )


# Backward-compat function name
def load_yaml_cases(directory: str) -> List[EvalCase]:
    return load_eval_cases(directory)


def normalize_text_for_eval(text: str) -> str:
    # Accent fold + case fold + collapse spaces
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    lowered = ascii_text.lower()
    collapsed = " ".join(lowered.split())
    return collapsed


# Backward-compat alias
normalize_text_basic = normalize_text_for_eval


def deterministic_offline_eval_model(case: EvalCase, *, seed: int) -> Dict[str, Any]:
    """A minimal deterministic stub model for offline evaluation testing.

    For offline evaluation we do NOT perform any external search. We return a structure with
    normalized_name inferred as best-effort from the label when present, otherwise
    a normalized variant of the query. Vintage is set to None if query suggests NV.
    """
    rnd = random.Random(seed)
    # Use label when present to allow exact-match checks without gating
    name_value = case.normalized_name or case.wine_query
    # Simple NV heuristic: if inventory_vintage is "NV" or vintage label is None
    inv_v = str(case.raw.get("inventory_vintage", "")).strip().upper()
    if inv_v == "NV":
        predicted_vintage = None
    else:
        predicted_vintage = case.vintage if case.vintage not in ("", "null") else None

    # Grapes: if labeled, echo; else empty
    predicted_grapes = case.grapes

    # Return structure similar to final wine json shape (minimal for tests)
    return {
        "wine": {
            "normalized_name": {"value": name_value},
            "vintage": {"value": predicted_vintage},
            "grapes": {"value": predicted_grapes},
        }
    }


def hash_eval_output(obj: Dict[str, Any]) -> str:
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


# Backward-compat alias
def hash_output(obj: Dict[str, Any]) -> str:  # type: ignore[override]
    return hash_eval_output(obj)


def run_offline_eval(
    dataset_dir: str, *, seed: int = 42, metrics_path: str = ".metrics.json"
) -> Metrics:
    """Run offline deterministic evaluation over a dataset of labeled wine cases.

    Args:
        dataset_dir: Directory containing YAML evaluation cases
        seed: Random seed for deterministic results
        metrics_path: Where to persist metrics JSON

    Returns:
        Metrics object with evaluation results
    """
    # Force offline mode: tests set WINE_SEARCH_CALLS_PER_RUN=0; we avoid any search here
    metrics = Metrics()
    cases = load_eval_cases(dataset_dir)

    # Determinism check aggregate
    all_deterministic = True

    for case in cases:
        # 1) Run model twice with fixed seed; hashes must match
        out1 = deterministic_offline_eval_model(case, seed=seed)
        out2 = deterministic_offline_eval_model(case, seed=seed)
        h1, h2 = hash_eval_output(out1), hash_eval_output(out2)
        if h1 != h2:
            all_deterministic = False

        # 2) Normalized name exact when labeled
        label_name = case.normalized_name
        if label_name:
            actual = out1["wine"]["normalized_name"]["value"] or ""
            ok = normalize_text_for_eval(actual) == normalize_text_for_eval(label_name)
            metrics.increment("normalized_name_total", 1)
            metrics.increment("normalized_name_match", 1 if ok else 0)
            if not ok:
                metrics.record_event(
                    "normalized_name_mismatch",
                    {
                        "query": case.wine_query,
                        "expected": label_name,
                        "actual": actual,
                    },
                )

        # 3) NV handling
        if case.raw.get("inventory_vintage") == "NV" or case.vintage is None:
            actual_v = out1["wine"]["vintage"]["value"]
            ok_nv = actual_v in (None, "NV", "nv")
            metrics.increment("nv_vintage_total", 1)
            metrics.increment("nv_vintage_ok", 1 if ok_nv else 0)
            if not ok_nv:
                metrics.record_event(
                    "nv_vintage_bad",
                    {"query": case.wine_query, "actual": actual_v},
                )

        # 4) Grapes presence when labeled (token contains)
        if case.grapes:
            actual_grapes = out1["wine"]["grapes"]["value"] or ""
            # Token presence check (case/accent insensitive)
            label_tokens = [
                t
                for t in normalize_text_for_eval(case.grapes).replace(",", " ").split()
                if t
            ]
            actual_norm = normalize_text_for_eval(str(actual_grapes))
            contains = all(token in actual_norm for token in label_tokens)
            metrics.increment("grapes_total", 1)
            metrics.increment("grapes_contains_label", 1 if contains else 0)

        # 5) Spelling minimal check: if spelling_corrections present → ensure name matches corrected form heuristic
        spelling_corr = case.corrections.get("spelling_corrections") or []
        if spelling_corr:
            actual = out1["wine"]["normalized_name"]["value"] or ""
            actual_norm = normalize_text_for_eval(actual)
            ok_spell = True

            for entry in spelling_corr:
                entry_str = str(entry).strip()
                # Handle "X (not Y)" pattern
                m = re.match(
                    r"^(?P<want>[^()]+)\s*\(not\s+(?P<avoid>[^)]+)\)\s*$",
                    entry_str,
                    re.I,
                )
                if m:
                    want_tokens = [
                        t for t in normalize_text_for_eval(m.group("want")).split() if t
                    ]
                    avoid_tokens = [
                        t
                        for t in normalize_text_for_eval(m.group("avoid")).split()
                        if t
                    ]
                    entry_ok = all(t in actual_norm for t in want_tokens) and all(
                        t not in actual_norm for t in avoid_tokens
                    )
                else:
                    # Simple case: all tokens must be present
                    want_tokens = [
                        t for t in normalize_text_for_eval(entry_str).split() if t
                    ]
                    entry_ok = all(t in actual_norm for t in want_tokens)

                if not entry_ok:
                    ok_spell = False
                    break

            metrics.increment("spelling_total", 1)
            metrics.increment("spelling_corrected", 1 if ok_spell else 0)

        # Log a no-op gate for visibility in offline evaluation
        gate_or_halt("offline_eval_gate", True, detail=case.wine_query, sink=metrics)

    metrics.record_metric("determinism_ok", 1 if all_deterministic else 0)
    metrics.persist(metrics_path)
    return metrics
