"""Request identity: the only input to the execution cache key."""

from __future__ import annotations

from typing import Mapping

from ..cache import stable_hash


def request_identity(
    *,
    namespace: str,
    version: str,
    components: Mapping[str, object],
) -> str:
    """Compose the cache identity of one evaluation request.

    The identity covers the request material only — scenario, agent, model,
    effort, prompt, guidance compilation, and alike. Run labels are
    structurally absent: this function takes no label argument, so
    provenance can never leak into the cache key. Two requests with the
    same components share a cache entry; any component change misses.
    """

    return f"{namespace}:{version}:{stable_hash(dict(components))}"
