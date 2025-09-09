from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class Metrics:
    """Lightweight metrics sink for Phase 0.

    Records simple integer metrics and free-form events, and persists to a JSON file.
    """

    metrics: Dict[str, int] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def record_metric(self, name: str, value: int) -> None:
        self.metrics[name] = int(value)

    def increment(self, name: str, by: int = 1) -> None:
        self.metrics[name] = int(self.metrics.get(name, 0)) + int(by)

    def record_event(self, name: str, data: Any) -> None:
        self.events.append({"name": name, "data": data})

    def persist(self, path: str = ".metrics.json") -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": self.metrics,
            "events": self.events,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)


def gate_or_halt(
    name: str,
    condition: bool,
    detail: str | None = None,
    *,
    sink: Metrics | None = None,
    enforce: bool = False,
) -> bool:
    """Evaluation gate helper: log-only in offline mode, optionally enforce.

    Args:
        name: Gate name for logging
        condition: Whether the gate should pass
        detail: Additional detail for logging
        sink: Metrics sink for recording events
        enforce: If True, raise exception when condition is False (for tests)

    Returns:
        True in offline evaluation mode (unless enforce=True and condition=False)

    Raises:
        AssertionError: If enforce=True and condition=False
    """
    if sink is not None:
        sink.record_event(
            "gate",
            {
                "gate": name,
                "passed": bool(condition),
                "detail": detail,
                "mode": "offline_eval",
                "enforce": enforce,
            },
        )

    if enforce and not condition:
        raise AssertionError(f"Gate '{name}' failed: {detail}")

    return True
