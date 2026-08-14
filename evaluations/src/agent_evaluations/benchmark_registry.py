from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib
import importlib.util
import os
from pathlib import Path
import pkgutil
import sys
from types import ModuleType
from typing import Any, Callable, Dict, Iterable


RegisterParserFn = Callable[[Any], None]


@dataclass(frozen=True)
class BenchmarkDefinition:
    benchmark_id: str
    register_download: RegisterParserFn
    register_manifest: RegisterParserFn
    register_run: RegisterParserFn
    register_internal_run_single: RegisterParserFn


def _benchmark_modules() -> Iterable[ModuleType]:
    """Discover benchmark modules.

    Discovery order:
    1. External benchmarks (out-of-tree) if ``AGENT_EVALUATIONS_BENCHMARKS_DIR``
       is set and points at a directory of benchmark subdirectories.
    2. In-package benchmarks under ``agent_evaluations.evaluations.*`` — each
       evaluation subpackage may contain one or more ``benchmark_*.py`` modules
       that export a ``BENCHMARK`` attribute.
    3. Legacy in-package benchmarks under ``agent_evaluations.benchmarks.*``
       (top-level modules only) for backwards compatibility.
    """
    seen: set[str] = set()
    modules: list[ModuleType] = []
    for module in _external_benchmark_modules():
        if module.__name__ not in seen:
            seen.add(module.__name__)
            modules.append(module)
    for module in _evaluations_package_benchmark_modules():
        if module.__name__ not in seen:
            seen.add(module.__name__)
            modules.append(module)
    for module in _legacy_package_benchmark_modules():
        if module.__name__ not in seen:
            seen.add(module.__name__)
            modules.append(module)
    return modules


def _external_benchmarks_root() -> Path | None:
    configured = os.environ.get("AGENT_EVALUATIONS_BENCHMARKS_DIR")
    if isinstance(configured, str) and configured.strip():
        candidate = Path(configured).expanduser().resolve()
        if candidate.is_dir():
            return candidate
    return None


def _external_benchmark_modules() -> Iterable[ModuleType]:
    """Load benchmark modules from an out-of-tree directory.

    Each subdirectory may contain one or more ``benchmark*.py`` files. Each
    such file is loaded as a standalone module and is expected to export a
    ``BENCHMARK`` attribute.
    """
    root = _external_benchmarks_root()
    if root is None:
        return []
    modules = []
    for benchmark_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        benchmark_files = sorted(benchmark_dir.glob("benchmark*.py"))
        for module_path in benchmark_files:
            stem = module_path.stem
            module_name = f"agent_evaluations_external_benchmark_{benchmark_dir.name}_{stem}"
            cached = sys.modules.get(module_name)
            if isinstance(cached, ModuleType):
                modules.append(cached)
                continue
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            modules.append(module)
    return modules


def _evaluations_package_benchmark_modules() -> Iterable[ModuleType]:
    """Discover ``benchmark_*.py`` modules under ``agent_evaluations.evaluations.*``.

    Each subpackage of ``agent_evaluations.evaluations`` represents one
    evaluation. A subpackage may contain one or more ``benchmark_*.py`` modules,
    each exporting a ``BENCHMARK`` attribute.
    """
    try:
        evaluations_pkg = importlib.import_module("agent_evaluations.evaluations")
    except ImportError:
        return []
    pkg_path = getattr(evaluations_pkg, "__path__", None)
    if pkg_path is None:
        return []
    modules: list[ModuleType] = []
    for _, eval_name, is_pkg in pkgutil.iter_modules(pkg_path):
        if not is_pkg:
            continue
        try:
            eval_pkg = importlib.import_module(f"agent_evaluations.evaluations.{eval_name}")
        except ImportError:
            continue
        eval_pkg_path = getattr(eval_pkg, "__path__", None)
        if eval_pkg_path is None:
            continue
        for _, mod_name, _ in pkgutil.iter_modules(eval_pkg_path):
            if not mod_name.startswith("benchmark"):
                continue
            full_name = f"agent_evaluations.evaluations.{eval_name}.{mod_name}"
            try:
                modules.append(importlib.import_module(full_name))
            except ImportError:
                continue
    return modules


def _legacy_package_benchmark_modules() -> Iterable[ModuleType]:
    """Legacy discovery: top-level modules under ``agent_evaluations.benchmarks``."""
    try:
        package = importlib.import_module("agent_evaluations.benchmarks")
    except ImportError:
        return []
    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return []
    modules = []
    for module_info in pkgutil.iter_modules(package_path):
        if module_info.ispkg:
            continue
        modules.append(importlib.import_module(f"{package.__name__}.{module_info.name}"))
    return modules


def load_benchmarks() -> Dict[str, BenchmarkDefinition]:
    benchmarks: Dict[str, BenchmarkDefinition] = {}
    for module in _benchmark_modules():
        benchmark = getattr(module, "BENCHMARK", None)
        if benchmark is None:
            continue
        if not isinstance(benchmark, BenchmarkDefinition):
            raise TypeError(
                f"Benchmark module {module.__name__} exported BENCHMARK with invalid type"
            )
        if benchmark.benchmark_id in benchmarks:
            raise ValueError(
                f"Duplicate benchmark id registered: {benchmark.benchmark_id}"
            )
        benchmarks[benchmark.benchmark_id] = benchmark
    return benchmarks