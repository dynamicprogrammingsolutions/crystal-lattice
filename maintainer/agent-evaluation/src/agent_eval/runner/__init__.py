"""Reusable run model for evaluation suites.

The layer sits between the generic kernel and evaluation suites: suites
consume it and wire execution environments (for example the crystal-lattice
adapter) into it, while the layer itself depends only on the kernel and
receives environments as parameters. It owns run labels (pure provenance,
never part of any cache identity), request identity composition, sample
execution semantics, the provider-failure publication policy, and the
consolidation core (label selection and per-cell sample statistics).
"""

from .consolidation import (
    CellRecord,
    aggregate_metric,
    cell_statistics,
    completeness,
    record_paths,
    render_selection,
    select_cell_records,
)
from .identity import request_identity
from .labels import generate_run_label
from .model import RunModel, publish_when_no_provider_errors

__all__ = [
    "CellRecord",
    "RunModel",
    "aggregate_metric",
    "cell_statistics",
    "completeness",
    "generate_run_label",
    "publish_when_no_provider_errors",
    "record_paths",
    "render_selection",
    "request_identity",
    "select_cell_records",
]
