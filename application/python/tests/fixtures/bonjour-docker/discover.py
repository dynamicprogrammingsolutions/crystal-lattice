"""Discover _http._tcp services via zeroconf and print as JSON.

Used by the Docker Bonjour integration test.  The discoverer container
runs this script on the same Docker network as the CLI server container.
mDNS multicast works across Docker bridge networks, so the discoverer
can find the service advertised by the server.

Output: a JSON array of ``{name, type, host, port}`` objects, one per
discovered service.  The script listens for 15 seconds then exits.
"""

from __future__ import annotations

import json
import socket
import sys
import time
from typing import Any

from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf


class _Listener:
    def __init__(self) -> None:
        self.services: list[dict[str, Any]] = []

    def add_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        info: ServiceInfo | None = zc.get_service_info(service_type, name)
        if info is None:
            return
        host = socket.inet_ntoa(info.address) if info.address else ""
        self.services.append(
            {
                "name": name,
                "type": service_type,
                "host": host,
                "port": info.port,
            }
        )

    def remove_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        pass

    def update_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        pass


def main() -> None:
    zc = Zeroconf()
    listener = _Listener()
    ServiceBrowser(zc, "_http._tcp.local.", listener)

    time.sleep(15)
    zc.close()

    json.dump(listener.services, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
