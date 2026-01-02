"""Tests for L8-4 Side-Effect Channels v0.1"""

from __future__ import annotations

import pytest

from layer8_execution.side_effects_v0_1 import SideEffectBus, SideEffectPolicyError


def test_side_effect_bus_allows_declared_channel() -> None:
    bus = SideEffectBus(
        declared_channels=("log",),
        clock_utc=lambda: "1970-01-01T00:00:00Z",
        action_id="TEST",
        run_id="RUN",
    )
    ev = bus.emit("log", {"msg": "hello"})
    snap = bus.snapshot()

    assert ev.seq == 1
    assert ev.channel == "log"
    assert ev.payload == {"msg": "hello"}
    assert snap[0].seq == 1
    assert snap[0].channel == "log"


def test_side_effect_bus_blocks_undeclared_channel() -> None:
    bus = SideEffectBus(
        declared_channels=("log",),
        clock_utc=lambda: "1970-01-01T00:00:00Z",
        action_id="TEST",
        run_id="RUN",
    )
    with pytest.raises(SideEffectPolicyError):
        bus.emit("metric", {"value": 1})


def test_side_effect_bus_deterministic_seq_order() -> None:
    bus = SideEffectBus(
        declared_channels=("log",),
        clock_utc=lambda: "1970-01-01T00:00:00Z",
        action_id="TEST",
        run_id="RUN",
    )
    bus.emit("log", {"a": 1})
    bus.emit("log", {"b": 2})
    snap = bus.snapshot()

    assert [e.seq for e in snap] == [1, 2]
