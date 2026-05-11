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
    external_modules = list(_external_benchmark_modules())
    if external_modules:
        return external_modules
    return list(_package_benchmark_modules())


def _external_benchmarks_root() -> Path | None:
    configured = os.environ.get("AGENT_EVALUATIONS_BENCHMARKS_DIR")
    if isinstance(configured, str) and configured.strip():
        candidate = Path(configured).expanduser().resolve()
        if candidate.is_dir():
            return candidate

    source_tree_candidate = Path(__file__).resolve().parents[2] / "benchmarks"
    if source_tree_candidate.is_dir():
        return source_tree_candidate

    cwd_candidate = Path.cwd() / "evaluations" / "benchmarks"
    if cwd_candidate.is_dir():
        return cwd_candidate.resolve()

    return None


def _external_benchmark_modules() -> Iterable[ModuleType]:
    root = _external_benchmarks_root()
    if root is None:
        return []
    modules = []
    for benchmark_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        module_path = benchmark_dir / "benchmark.py"
        if not module_path.is_file():
            continue
        module_name = f"agent_evaluations_external_benchmark_{benchmark_dir.name}"
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


def _package_benchmark_modules() -> Iterable[ModuleType]:
    package = importlib.import_module("agent_evaluations.benchmarks")
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