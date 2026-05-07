from __future__ import annotations

import gc
import os
import threading
import weakref
from typing import Dict, Mapping


class RuntimeEnvOverlay:
    """Process-wide environment overlay for application runtime keys.

    The overlay installs resolved config env values into ``os.environ`` so
    plugins can access them through the real process environment. Values are
    reference-counted so multiple application instances may share the same
    overlay safely. Conflicting live values raise a clear error because
    process-global environment variables cannot represent multiple different
    application roots at once.
    """

    _lock = threading.RLock()
    _managed: Dict[str, Dict[str, object]] = {}

    def __init__(self, values: Mapping[str, str]) -> None:
        self._values: Dict[str, str] = {
            key: str(value)
            for key, value in values.items()
            if isinstance(key, str) and key and isinstance(value, str)
        }
        self._installed = False
        self._owner_ref = weakref.ref(self)

    @property
    def values(self) -> Dict[str, str]:
        return dict(self._values)

    def install(self) -> None:
        if self._installed:
            return
        with self._lock:
            self._cleanup_stale_locked()
            for key, desired in sorted(self._values.items()):
                record = self._managed.get(key)
                if record is not None:
                    current_value = record.get("value")
                    if current_value != desired:
                        gc.collect()
                        self._cleanup_stale_locked()
                        record = self._managed.get(key)
                        current_value = (
                            record.get("value") if record is not None else None
                        )
                    if record is not None and current_value != desired:
                        raise RuntimeError(
                            "Conflicting runtime environment overlay for "
                            f"{key!r}: existing value {current_value!r}, new value {desired!r}"
                        )
                    if record is not None:
                        owners = self._live_owner_refs(record)
                        owners.append(self._owner_ref)
                        record["owners"] = owners
                        continue

                previous_exists = key in os.environ
                previous_value = os.environ.get(key)
                os.environ[key] = desired
                self._managed[key] = {
                    "value": desired,
                    "owners": [self._owner_ref],
                    "previous_exists": previous_exists,
                    "previous_value": previous_value,
                }
        self._installed = True

    def close(self) -> None:
        if not self._installed:
            return
        with self._lock:
            for key, desired in sorted(self._values.items(), reverse=True):
                record = self._managed.get(key)
                if record is None or record.get("value") != desired:
                    continue
                owners = [
                    owner_ref
                    for owner_ref in self._live_owner_refs(record)
                    if owner_ref() is not self
                ]
                if owners:
                    record["owners"] = owners
                    continue
                if bool(record.get("previous_exists")):
                    previous_value = record.get("previous_value")
                    if isinstance(previous_value, str):
                        os.environ[key] = previous_value
                    else:
                        os.environ.pop(key, None)
                else:
                    os.environ.pop(key, None)
                self._managed.pop(key, None)
        self._installed = False

    @staticmethod
    def _live_owner_refs(
        record: Dict[str, object],
    ) -> list[weakref.ReferenceType["RuntimeEnvOverlay"]]:
        raw_owners = record.get("owners")
        if not isinstance(raw_owners, list):
            return []
        live: list[weakref.ReferenceType["RuntimeEnvOverlay"]] = []
        seen: set[int] = set()
        for owner_ref in raw_owners:
            if not isinstance(owner_ref, weakref.ReferenceType):
                continue
            owner = owner_ref()
            if owner is None:
                continue
            ident = id(owner)
            if ident in seen:
                continue
            seen.add(ident)
            live.append(owner_ref)
        return live

    @classmethod
    def _cleanup_stale_locked(cls) -> None:
        for key in list(cls._managed.keys()):
            record = cls._managed.get(key)
            if record is None:
                continue
            owners = cls._live_owner_refs(record)
            if owners:
                record["owners"] = owners
                continue
            if bool(record.get("previous_exists")):
                previous_value = record.get("previous_value")
                if isinstance(previous_value, str):
                    os.environ[key] = previous_value
                else:
                    os.environ.pop(key, None)
            else:
                os.environ.pop(key, None)
            cls._managed.pop(key, None)

    @classmethod
    def _reset_for_tests(cls) -> None:
        """Release all live overlays between tests.

        Production callers should close their owning applications. Test suites
        often create many short-lived applications without explicit cleanup,
        so this helper prevents one test's process-wide env overlay from
        leaking into the next.
        """

        owners: list[RuntimeEnvOverlay] = []
        with cls._lock:
            for record in cls._managed.values():
                for owner_ref in cls._live_owner_refs(record):
                    owner = owner_ref()
                    if owner is not None:
                        owners.append(owner)

        seen: set[int] = set()
        for owner in owners:
            ident = id(owner)
            if ident in seen:
                continue
            seen.add(ident)
            owner.close()

        with cls._lock:
            cls._cleanup_stale_locked()
