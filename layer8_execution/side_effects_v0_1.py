"""
GUS v4.0 — L8 Execution Layer
Side-Effect Channels v0.1 (L8-4)

Purpose:
- Provide a deterministic, declared-IO-only side-effect mechanism.
- Actions may emit side effects ONLY through declared channels.
- All emitted events are captured for audit and record hashing.

Notes:
- This enforces declared side effects at the engine boundary (SideEffectBus).
- It does not attempt to intercept direct filesystem/network IO in user code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Final, Mapping


class SideEffectPolicyError(RuntimeError):
    """Raised when an action attempts an undeclared side effect."""


@dataclass(frozen=True)
class SideEffectEvent:
    seq: int
    timestamp_utc: str
    channel: str
    payload: Mapping[str, Any]
    action_id: str
    run_id: str


class SideEffectBus:
    """
    Deterministic side-effect bus.

    - Enforces a fixed allow-list of channels per action (declared at registration).
    - Captures every emission as a SideEffectEvent (ordered by seq).
    """

    def __init__(
        self,
        *,
        declared_channels: tuple[str, ...],
        clock_utc: Callable[[], str],
        action_id: str,
        run_id: str,
    ) -> None:
        self._declared_channels: Final[tuple[str, ...]] = tuple(declared_channels)
        self._clock_utc = clock_utc
        self._action_id = action_id
        self._run_id = run_id
        self._seq = 0
        self._events: list[SideEffectEvent] = []

    @property
    def declared_channels(self) -> tuple[str, ...]:
        return self._declared_channels

    def emit(self, channel: str, payload: Mapping[str, Any]) -> SideEffectEvent:
        if not isinstance(channel, str) or not channel.strip():
            raise TypeError("channel must be a non-empty string")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict (JSON-serializable mapping)")
        if channel not in self._declared_channels:
            raise SideEffectPolicyError(
                f"Undeclared side-effect channel: {channel}. Declared: {self._declared_channels}"
            )

        self._seq += 1
        ev = SideEffectEvent(
            seq=self._seq,
            timestamp_utc=self._clock_utc(),
            channel=channel,
            payload=payload,
            action_id=self._action_id,
            run_id=self._run_id,
        )
        self._events.append(ev)
        return ev

    def snapshot(self) -> tuple[SideEffectEvent, ...]:
        """Return an immutable snapshot of events in deterministic order."""
        return tuple(self._events)
