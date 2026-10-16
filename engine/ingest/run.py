"""Run-state manager (Phase 2, Task 1).

Coordinates the active source adapter, tracks run identity, and
provides start/step/reset controls for the scenario API.  State
is in-memory only — restarting the process resets everything.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence

from engine.ingest.source import SourceAdapter, SourceMode, SourceRecord


@dataclass
class StepResult:
    """What a single step() returned, plus bookkeeping."""
    run_id: str
    step_index: int
    current_time: datetime
    records: Sequence[SourceRecord]
    is_exhausted: bool
    display_label: str


class RunState:
    """Manages the active source adapter and run lifecycle.

    In-memory only — lost on process restart.  This is a hackathon
    design decision documented in docs/DECISIONS.md.
    """

    def __init__(self) -> None:
        self._adapter: SourceAdapter | None = None
        self._run_id: str = ""
        self._step_index: int = 0
        self._history: list[StepResult] = []

    @property
    def is_active(self) -> bool:
        return self._adapter is not None

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def step_index(self) -> int:
        return self._step_index

    @property
    def mode(self) -> SourceMode | None:
        return self._adapter.mode() if self._adapter else None

    @property
    def display_label(self) -> str:
        return self._adapter.display_label() if self._adapter else "NO SOURCE"

    @property
    def current_time(self) -> datetime | None:
        return self._adapter.current_time() if self._adapter else None

    @property
    def is_exhausted(self) -> bool:
        return self._adapter.is_exhausted() if self._adapter else True

    def start(self, adapter: SourceAdapter) -> str:
        """Begin a new run with the given adapter."""
        self._adapter = adapter
        self._run_id = f"run-{uuid.uuid4().hex[:12]}"
        self._step_index = 0
        self._history = []
        return self._run_id

    def step(self) -> StepResult:
        """Advance one time step."""
        if not self._adapter:
            raise RuntimeError("No active source — call start() first")
        if self._adapter.is_exhausted():
            raise RuntimeError("Source is exhausted — reset or start a new run")

        records = self._adapter.step()
        if any(r.available_at > self._adapter.current_time() or r.event_time > self._adapter.current_time() for r in records):
            raise ValueError('Source attempted to expose future observations')
        self._step_index += 1
        result = StepResult(
            run_id=self._run_id,
            step_index=self._step_index,
            current_time=self._adapter.current_time(),
            records=records,
            is_exhausted=self._adapter.is_exhausted(),
            display_label=self._adapter.display_label(),
        )
        self._history.append(result)
        return result

    @property
    def records(self):
        return [record for step in self._history for record in step.records]

    def reset(self) -> str:
        """Reset the current adapter and start a fresh run."""
        if not self._adapter:
            raise RuntimeError("No active source — call start() first")
        self._adapter.reset()
        self._run_id = f"run-{uuid.uuid4().hex[:12]}"
        self._step_index = 0
        self._history = []
        return self._run_id

    def stop(self) -> None:
        """Stop the current run and release the adapter."""
        self._adapter = None
        self._run_id = ""
        self._step_index = 0
        self._history = []

    def status(self) -> dict:
        """Summary of current run state for the API."""
        return {
            "is_active": self.is_active,
            "run_id": self._run_id or None,
            "mode": self.mode.value if self.mode else None,
            "step_index": self._step_index,
            "current_time": self.current_time.isoformat() if self.current_time else None,
            "is_exhausted": self.is_exhausted,
            "display_label": self.display_label,
            "steps_completed": len(self._history),
        }
