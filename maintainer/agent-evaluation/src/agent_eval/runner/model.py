"""Run model: labels, sample semantics, and cache publication policy."""

from __future__ import annotations

from typing import Callable, Mapping

from ..eval import AgentEval
from ..result import Run


def publish_when_no_provider_errors(run: Run[object]) -> bool:
    """Return whether a completed run may enter the execution cache.

    Runs whose value reports provider errors — insufficient quota, rate
    limits, and alike — stay out of the cache so the same request re-executes
    naturally on the next run. Values without an ``errors`` attribute or
    mapping key are always publishable.
    """

    value = run.value
    errors = getattr(value, "errors", None)
    if errors is None and isinstance(value, Mapping):
        errors = value.get("errors")
    if errors is None:
        return True
    return not len(errors)


class RunModel:
    """Apply the run model on top of a generic evaluation kernel.

    A :class:`RunModel` owns one run label — the provenance of one live
    invocation — and executes requests through the kernel with the label
    excluded from every cache identity. Unchanged requests replay from the
    cache; provider failures retry naturally; deliberate re-execution is
    explicit (``fresh`` and :meth:`run_samples`).
    """

    def __init__(
        self,
        evaluation: AgentEval,
        *,
        label: str | None = None,
        cache_publish: Callable[[Run[object]], bool] | None = None,
    ) -> None:
        from .labels import generate_run_label

        self.evaluation = evaluation
        self.label = label if label else generate_run_label()
        self._cache_publish = (
            cache_publish
            if cache_publish is not None
            else publish_when_no_provider_errors
        )

    def run(
        self,
        name: str,
        program: object,
        *,
        identity: str,
        environment: object = None,
        continue_from: Run[object] | None = None,
        workspace: object = None,
        fresh: bool = False,
    ) -> Run[object]:
        """Execute one request, cache-aware unless ``fresh``.

        Without ``fresh``, an unchanged identity replays from the cache and
        a changed one executes. With ``fresh``, the request re-executes even
        when a cache entry exists; it is the only way to re-run an already
        successful request.
        """

        run = self.evaluation.run(
            name,
            program,
            environment=environment,
            continue_from=continue_from,
            workspace=workspace,
            cache_key=identity,
            cache_read=not fresh,
            cache_publish=self._cache_publish,
        )
        self._record_provenance(run, identity=identity, sample_index=0)
        return run

    def run_samples(
        self,
        name: str,
        program: object,
        *,
        identity: str,
        count: int,
        environment: object = None,
        continue_from: Run[object] | None = None,
        workspace: object = None,
    ) -> tuple[Run[object], ...]:
        """Execute the same request ``count`` times as variance samples.

        Every sample is a genuine execution of the identical request
        identity, recorded under the invocation's run label.
        """

        if count < 1:
            raise ValueError("sample count must be positive")
        runs = []
        for sample_index in range(count):
            run = self.evaluation.run(
                name,
                program,
                environment=environment,
                continue_from=continue_from,
                workspace=workspace,
                cache_key=identity,
                cache_read=False,
                cache_publish=self._cache_publish,
            )
            self._record_provenance(
                run,
                identity=identity,
                sample_index=sample_index,
            )
            runs.append(run)
        return tuple(runs)

    def _record_provenance(
        self,
        run: Run[object],
        *,
        identity: str,
        sample_index: int,
    ) -> None:
        run.record(
            "run-model.json",
            {
                "schema": 1,
                "label": self.label,
                "identity": identity,
                "cache_hit": run.cache_hit,
                "sample_index": sample_index,
                "run_id": run.run_id,
            },
        )
