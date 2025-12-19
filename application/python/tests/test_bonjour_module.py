from __future__ import annotations

"""Unit tests for :mod:`agent_terminal_app.bonjour`.

These tests focus on verifying that ``start_bonjour`` and
``stop_bonjour`` interact with the Zeroconf API as expected without
requiring an actual mDNS environment.
"""

from typing import Any

from agent_terminal_app import bonjour as bonjour_mod


class _DummyZeroconf:
    def __init__(self) -> None:
        self.register_calls: list[Any] = []
        self.unregister_calls: list[Any] = []
        self.closed: bool = False

    def register_service(self, info: Any) -> None:
        self.register_calls.append(info)

    def unregister_service(self, info: Any) -> None:
        self.unregister_calls.append(info)

    def close(self) -> None:
        self.closed = True


class _DummyServiceInfo:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


def test_start_and_stop_bonjour_registers_and_unregisters(monkeypatch) -> None:
    """Bonjour helpers should call Zeroconf register/unregister/close."""

    monkeypatch.setattr(bonjour_mod, "Zeroconf", _DummyZeroconf)
    monkeypatch.setattr(bonjour_mod, "ServiceInfo", _DummyServiceInfo)

    handle = bonjour_mod.start_bonjour("Test Service", 12345)
    assert isinstance(handle, bonjour_mod.BonjourServiceHandle)

    zc = handle.zeroconf
    assert isinstance(zc, _DummyZeroconf)
    assert len(zc.register_calls) == 1

    bonjour_mod.stop_bonjour(handle)
    # Service should be unregistered and zeroconf closed.
    assert len(zc.unregister_calls) == 1
    assert zc.closed is True
