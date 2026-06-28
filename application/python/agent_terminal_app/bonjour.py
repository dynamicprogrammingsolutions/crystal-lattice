"""Bonjour / mDNS advertising helpers for the FastAPI server.

This module provides a very small wrapper around :mod:`zeroconf` so that
the :mod:`agent_terminal_app.server` can advertise itself as a
``_http._tcp`` service on the local network. The goal is parity with the
standalone ``bonjour_server.py`` example used by the mobile clients,
without coupling the core application logic to zeroconf or networking
details.

Usage (from the server module)::

    from agent_terminal_app import bonjour as bonjour_mod

    _bonjour_handle: Optional[bonjour_mod.BonjourServiceHandle] = None

    @app.on_event("startup")
    async def _on_startup() -> None:
        global _bonjour_handle
        if os.getenv("ENABLE_BONJOUR"):
            _bonjour_handle = bonjour_mod.start_bonjour(
                service_name="Agent Terminal App",
                port=8080,
            )

    @app.on_event("shutdown")
    async def _on_shutdown() -> None:
        global _bonjour_handle
        if _bonjour_handle is not None:
            bonjour_mod.stop_bonjour(_bonjour_handle)
            _bonjour_handle = None

The concrete port and service name are controlled by the caller; the
module itself is intentionally small and side-effect free.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import logging
import socket

try:  # Optional import so environments without zeroconf can still import
    from zeroconf import ServiceInfo, Zeroconf  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - handled gracefully at runtime
    ServiceInfo = None  # type: ignore[assignment]
    Zeroconf = None  # type: ignore[assignment]


log = logging.getLogger(__name__)


@dataclass
class BonjourServiceHandle:
    """Handle for a registered Bonjour service.

    The FastAPI app keeps an instance of this dataclass so that the
    underlying ``Zeroconf`` object and ``ServiceInfo`` can be cleaned up
    reliably on shutdown.
    """

    zeroconf: Any
    info: Any


def get_local_ip() -> str:
    """Best-effort detection of a non-loopback local IPv4 address.

    Mirrors the logic from the standalone Bonjour example: attempt to
    connect to a non-routable address to discover the preferred outbound
    interface, falling back to ``127.0.0.1`` when this fails.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        ip = sock.getsockname()[0]
    except Exception:  # pragma: no cover - environment dependent
        ip = "127.0.0.1"
    finally:
        try:
            sock.close()
        except Exception:  # pragma: no cover - defensive
            pass
    return ip


def start_bonjour(service_name: str, port: int) -> Optional[BonjourServiceHandle]:
    """Register a ``_http._tcp`` Bonjour service on the local network.

    Returns a :class:`BonjourServiceHandle` that must later be passed to
    :func:`stop_bonjour`. When :mod:`zeroconf` is not available, a warning
    is logged and ``None`` is returned so that callers can degrade
    gracefully without failing startup.
    """

    if Zeroconf is None or ServiceInfo is None:
        log.warning("zeroconf is not installed; Bonjour advertising disabled")
        return None

    try:
        zc = Zeroconf()
    except Exception as exc:  # pragma: no cover - very unlikely
        log.error("Failed to create Zeroconf instance for Bonjour: %s", exc)
        return None

    properties = {
        b"path": b"/",
        b"txtvers": b"1",
        b"description": b"Agent Terminal App HTTP API",
    }

    local_ip = get_local_ip()

    try:
        info = ServiceInfo(
            "_http._tcp.local.",
            f"{service_name}._http._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties=properties,
            server=f"{socket.gethostname()}.local.",
        )
        log.info("Constructed ServiceInfo for Bonjour: %r", info)
    except Exception as exc:  # pragma: no cover - defensive
        log.error(
            "Failed to construct ServiceInfo for Bonjour (service=%r ip=%s port=%s): %s",
            service_name,
            local_ip,
            port,
            exc,
        )
        try:
            zc.close()
        except Exception:
            pass
        return None

    # Log before attempting registration so that we always have a
    # trace of the intended service parameters even when registration
    # fails.
    log.info(
        "[bonjour] registering service name=%r type=%r ip=%s port=%s server=%r",
        service_name,
        "_http._tcp.local.",
        local_ip,
        port,
        f"{socket.gethostname()}.local.",
    )

    try:

        zc.register_service(info)
    except Exception:  # pragma: no cover - defensive
        # Use ``log.exception`` so that the exception type, message and
        # full stack trace are visible even when ``str(exc)`` is empty.
        log.exception(
            "[bonjour] failed to register service name=%r ip=%s port=%s",
            service_name,
            local_ip,
            port,
        )
        try:
            zc.close()
        except Exception:
            pass
        return None

    log.info(
        "[bonjour] advertising service name=%r ip=%s port=%s",
        service_name,
        local_ip,
        port,
    )
    return BonjourServiceHandle(zeroconf=zc, info=info)


def stop_bonjour(handle: Optional[BonjourServiceHandle]) -> None:
    """Unregister and clean up a Bonjour service handle.

    Any exceptions are caught and logged so that shutdown is resilient
    even when the underlying zeroconf resources are already gone.
    """

    if handle is None:
        return

    zc = handle.zeroconf
    info = handle.info

    # Best-effort extraction of the advertised service name for
    # logging. ``ServiceInfo`` exposes ``name`` on real zeroconf
    # instances; for tests or dummy objects this may be missing.
    service_name = None
    try:
        service_name = getattr(info, "name", None)
    except Exception:  # pragma: no cover - defensive
        service_name = None

    if service_name:
        log.info("[bonjour] unregistering service %r", service_name)
    else:
        log.info("[bonjour] unregistering service (name unavailable)")

    try:
        if zc is not None and info is not None:
            zc.unregister_service(info)
    except Exception:  # pragma: no cover - defensive
        log.debug("Error while unregistering Bonjour service", exc_info=True)
    finally:
        try:
            if zc is not None:
                zc.close()
        except Exception:  # pragma: no cover - defensive
            log.debug("Error while closing Zeroconf instance", exc_info=True)
