"""Tests for the pipeline utility function."""

import pytest
from agent_core.utils import pipeline


def test_pipeline_single_value_no_fixed_params():
    """Test pipeline with single value and no fixed parameters."""

    def add_one(x):
        return x + 1

    def multiply_two(x):
        return x * 2

    pipe = pipeline()
    result = pipe([add_one, multiply_two], 5)
    assert result == 12  # (5 + 1) * 2


def test_pipeline_single_value_with_fixed_params():
    """Test pipeline with single value and fixed parameters."""

    def add(fixed, x):
        return x + fixed

    def multiply(fixed, x):
        return x * fixed

    pipe = pipeline(3)
    result = pipe([add, multiply], 5)
    assert result == 24  # (5 + 3) * 3


def test_pipeline_multiple_values_no_fixed_params():
    """Test pipeline with multiple values and no fixed parameters."""

    def process1(a, b):
        return a + 1, b * 2

    def process2(a, b):
        return a * 2, b + 1

    pipe = pipeline()
    a, b = pipe([process1, process2], 5, 10)
    assert a == 12  # (5 + 1) * 2
    assert b == 21  # (10 * 2) + 1


def test_pipeline_multiple_values_with_fixed_params():
    """Test pipeline with multiple values and fixed parameters."""

    def process1(config, a, b):
        return a + config, b * config

    def process2(config, a, b):
        return a * 2, b + config

    pipe = pipeline(3)
    a, b = pipe([process1, process2], 5, 10)
    assert a == 16  # (5 + 3) * 2
    assert b == 33  # (10 * 3) + 3


def test_pipeline_three_values():
    """Test pipeline with three values (like finalize pattern)."""

    def finalize1(finals, native, state):
        return [*finals, "f1"], [*native, "n1"], {**state, "s1": True}

    def finalize2(finals, native, state):
        return [*finals, "f2"], [*native, "n2"], {**state, "s2": True}

    pipe = pipeline()
    finals, native, state = pipe([finalize1, finalize2], [], [], {})
    assert finals == ["f1", "f2"]
    assert native == ["n1", "n2"]
    assert state == {"s1": True, "s2": True}


def test_pipeline_empty_transforms():
    """Test pipeline with no transforms returns initial values."""
    pipe = pipeline()
    result = pipe([], 42)
    assert result == 42

    a, b = pipe([], 1, 2)
    assert a == 1
    assert b == 2


def test_pipeline_empty_initial_values():
    """Test pipeline with no initial values raises error."""
    pipe = pipeline()
    with pytest.raises(ValueError, match="at least one initial value"):
        pipe([lambda x: x])


def test_pipeline_single_transform():
    """Test pipeline with single transform."""

    def double(x):
        return x * 2

    pipe = pipeline()
    result = pipe([double], 5)
    assert result == 10


def test_pipeline_preserves_tuple_output():
    """Test that tuple outputs are preserved through the pipeline."""

    def make_tuple(x):
        return x, x * 2

    def sum_tuple(a, b):
        return a + b

    pipe = pipeline()
    result = pipe([make_tuple, sum_tuple], 5)
    assert result == 15  # 5 + 10


def test_pipeline_mixed_signatures():
    """Test pipeline with transforms that have different signatures."""

    # Simulating the extension finalize pattern
    def ext_finalize(final_messages, native_messages, state):
        return [*final_messages, "ext"], [*native_messages, "ext_n"], {**state, "ext": True}

    pipe = pipeline()
    # Using lambda to adapt signature
    transforms = [lambda f, n, s: ext_finalize(final_messages=f, native_messages=n, state=s)]
    finals, native, state = pipe(transforms, [], [], {})
    assert finals == ["ext"]
    assert native == ["ext_n"]
    assert state == {"ext": True}


def test_pipeline_with_list_comprehension():
    """Test pipeline with transforms generated from list comprehension."""

    class MockPlugin:
        def __init__(self, name):
            self.name = name

        def transform(self, config, value):
            return f"{value}+{self.name}"

    plugins = [MockPlugin("A"), MockPlugin("B"), MockPlugin("C")]
    pipe = pipeline("config")
    result = pipe([p.transform for p in plugins], "start")
    assert result == "start+A+B+C"


def test_pipeline_stateful_transforms():
    """Test pipeline with stateful transforms (like provider state)."""

    def init_state(config, state):
        return {**state, "initialized": True, "config": config}

    def add_feature(config, state):
        features = state.get("features", [])
        return {**state, "features": [*features, "new_feature"]}

    pipe = pipeline({"model": "gpt-4"})
    state = pipe([init_state, add_feature], {})
    assert state["initialized"] is True
    assert state["config"] == {"model": "gpt-4"}
    assert state["features"] == ["new_feature"]


def test_pipeline_real_world_from_native():
    """Test pipeline mimicking real from_native_messages usage."""

    class MockExtension:
        def __init__(self, name):
            self.name = name

        def from_native_messages(self, native, core):
            # Add a marker to show this extension processed the messages
            return [{**m, "processed_by": [*m.get("processed_by", []), self.name]} for m in core]

    extensions = [MockExtension("ext1"), MockExtension("ext2")]
    native = [{"role": "assistant", "content": "hello"}]
    core_initial = [{"role": "assistant", "content": "hello", "processed_by": []}]

    pipe = pipeline(native)
    final_core = pipe([ext.from_native_messages for ext in extensions], core_initial)

    assert final_core[0]["processed_by"] == ["ext1", "ext2"]


def test_pipeline_chained_operations():
    """Test complex chained pipeline operations."""

    def convert_to_native(state, messages):
        return [{**m, "native": True} for m in messages]

    def add_metadata(state, messages):
        return [{**m, "meta": state["key"]} for m in messages]

    def finalize(state, messages):
        return [{**m, "final": True} for m in messages]

    pipe = pipeline({"key": "value"})
    result = pipe([convert_to_native, add_metadata, finalize], [{"content": "test"}])

    assert result == [{"content": "test", "native": True, "meta": "value", "final": True}]
