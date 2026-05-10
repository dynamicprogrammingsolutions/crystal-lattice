from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib
import pkgutil
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
    package = importlib.import_module("agent_evaluations.benchmarks")
    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return []
    modules = []
    for module_info in pkgutil.iter_modules(package_path):
        if module_info.ispkg:
            continue
        modules.append(
            importlib.import_module(f"{package.__name__}.{module_info.name}")
        )
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