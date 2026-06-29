"""Docker Bonjour discovery integration test.

Starts the CLI in a Docker container with ``--enable-bonjour``, then runs
a discovery script in another container on the same Docker network to verify
the service is advertised via mDNS.

Marked ``integration`` + ``docker`` so it is excluded from default runs.
Run with::

    pytest application/python/tests/test_cli_bonjour_docker.py -m 'integration and docker' -v
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.docker]


ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "bonjour-docker"


def _ensure_docker() -> None:
    if shutil.which("docker") is None:
        pytest.skip("Docker is not available")
    result = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"Docker daemon is not available\n{result.stdout}")


def _docker_compose_cmd() -> list[str]:
    if shutil.which("docker-compose") is not None:
        return ["docker-compose"]
    return ["docker", "compose"]


def test_bonjour_discoverable_from_another_container() -> None:
    """CLI with --enable-bonjour is discoverable via mDNS from another container."""
    _ensure_docker()

    compose = _docker_compose_cmd()
    compose_file = str(FIXTURES_DIR / "docker-compose.yml")

    try:
        # Start the server container.
        subprocess.run(
            [*compose, "-f", compose_file, "up", "-d", "--build", "server"],
            cwd=str(FIXTURES_DIR),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300,
        )

        # Wait for the server to be ready (poll via docker exec).
        deadline = time.monotonic() + 120
        ready = False
        while time.monotonic() < deadline:
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "bonjour-docker-server-1",
                    "python",
                    "-c",
                    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/hello', timeout=2)",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                ready = True
                break
            time.sleep(2)

        if not ready:
            # Dump server logs for debugging.
            logs = subprocess.run(
                [*compose, "-f", compose_file, "logs", "server"],
                cwd=str(FIXTURES_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=30,
            )
            pytest.fail(f"Server did not become ready.\nLogs:\n{logs.stdout[:2000]}")

        # Run the discoverer container.
        result = subprocess.run(
            [*compose, "-f", compose_file, "run", "--rm", "discoverer"],
            cwd=str(FIXTURES_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            pytest.fail(f"Discovery script failed:\n{result.stdout[:2000]}")

        # Parse the JSON output from the discoverer.
        # The output may contain pip install lines before the JSON.
        output = result.stdout.strip()
        # Find the JSON array in the output.
        json_start = output.find("[")
        json_end = output.rfind("]")
        if json_start == -1 or json_end == -1:
            pytest.fail(f"No JSON found in discovery output:\n{output[:2000]}")

        services = json.loads(output[json_start : json_end + 1])
        assert len(services) > 0, f"No services discovered. Output:\n{output[:2000]}"

        # Verify the service has the expected type and a valid port.
        service = services[0]
        assert "_http._tcp" in service["type"]
        assert service["port"] > 0
        assert service["host"], "Service host is empty"

    finally:
        # Tear down.
        subprocess.run(
            [*compose, "-f", compose_file, "down", "--remove-orphans", "-v"],
            cwd=str(FIXTURES_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=60,
        )
