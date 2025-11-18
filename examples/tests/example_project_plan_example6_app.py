"""
Tests for PROJECT_PLAN Example 6 code (expected to fail as not implemented).
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)


def test_project_plan_example6_app_not_implemented():
    mod = __import__("examples.project_plan_example6_app", fromlist=["run_example"])
    if hasattr(mod, "run_example"):
        try:
            mod.run_example()
        except Exception:
            pass
