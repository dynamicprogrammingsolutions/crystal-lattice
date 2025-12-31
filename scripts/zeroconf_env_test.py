from __future__ import annotations

"""Minimal Zeroconf registration test script.

This script registers a single ``_http._tcp`` Bonjour/mDNS service using
the same pattern as the bonjour example server and ``agent_terminal_app``:

* Detect a non-loopback IPv4 address using a UDP "connect" trick.
* Construct a :class:`zeroconf.ServiceInfo` with that address.
* Call :func:`zeroconf.Zeroconf.register_service`.

You can run this script from *any* Python environment that has
``zeroconf`` installed. It is useful for checking how mDNS behaves on
your machine independently of the full server application.

Example usage (ai-agent-platform venv)::

    cd /Users/ferenci84/Dev/Mine/ai-agent-platform
    . .venv/bin/activate
    python scripts/zeroconf_env_test.py \
        --service-name "VenvTest Service" \
        --port 8123 \
        --duration 30

While it is running, you can inspect Bonjour state with::

    dns-sd -B _http._tcp local.
    dns-sd -L "VenvTest Service" _http._tcp local.

Hit Ctrl+C in the terminal running this script to unregister and exit
early.
"""

import argparse
import socket
import time
from typing import Final

from zeroconf import ServiceInfo, Zeroconf


def _get_local_ip() -> str:
    """Return a best-effort non-loopback IPv4 address.

    Mirrors the logic used in both the bonjour example server and
    :mod:`agent_terminal_app.bonjour`: connect a UDP socket to a
    non-routable address to discover the preferred outbound interface,
    falling back to ``127.0.0.1`` when this fails.
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        ip = sock.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        try:
            sock.close()
        except Exception:
            pass
    return ip


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Register a temporary _http._tcp Bonjour service to test "
            "Zeroconf/mDNS behaviour in the current environment."
        ),
    )
    parser.add_argument(
        "--service-name",
        type=str,
        default="VenvTest Service",
        help="Instance name to advertise (default: VenvTest Service)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8123,
        help="TCP port to advertise on (default: 8123)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=20,
        help="Seconds to keep the service registered (default: 20)",
    )

    args = parser.parse_args()

    local_ip: Final[str] = _get_local_ip()

    properties = {
        b"path": b"/",
        b"txtvers": b"1",
        b"description": b"Zeroconf env test service",
    }

    info = ServiceInfo(
        "_http._tcp.local.",
        f"{args.service_name}._http._tcp.local.",
        addresses=[socket.inet_aton(local_ip)],
        port=args.port,
        properties=properties,
        server=f"{socket.gethostname()}.local.",
    )

    print(
        f"[zeroconf_env_test] local_ip={local_ip} "
        f"service_name={args.service_name!r} port={args.port}",
        flush=True,
    )

    zc = Zeroconf()
    print("[zeroconf_env_test] Zeroconf created:", zc, flush=True)

    try:
        zc.register_service(info)
        print("[zeroconf_env_test] Service registered; sleeping...", flush=True)
        try:
            time.sleep(max(1, args.duration))
        except KeyboardInterrupt:
            print("[zeroconf_env_test] Interrupted by user; unregistering...", flush=True)
    finally:
        try:
            print("[zeroconf_env_test] Unregistering service", flush=True)
            zc.unregister_service(info)
        except Exception as exc:  # pragma: no cover - diagnostic only
            print(f"[zeroconf_env_test] Error during unregister: {exc}", flush=True)
        try:
            zc.close()
        except Exception as exc:  # pragma: no cover - diagnostic only
            print(f"[zeroconf_env_test] Error while closing Zeroconf: {exc}", flush=True)
        print("[zeroconf_env_test] Done", flush=True)


if __name__ == "__main__":  # pragma: no cover - manual execution only
    main()
