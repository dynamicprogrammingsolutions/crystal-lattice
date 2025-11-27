# Refactoring Plan: Functional Pipeline Transformation

## Overview

Refactor repetitive pipe transformation loops in `core.py` and `provider.py` to use a functional pipeline helper that is more declarative, less error-prone, and more maintainable.

## Current Problem

Multiple places in the codebase follow this pattern:

```python
# Manual pipe transformation
for ext in self._iter_extensions():
    final_messages, full_history, new_state = ext.finalize(
        final_messages=final_messages,
        native_messages=full_history,
        state=new_state,
    )
```

Issues:
- Easy to accidentally skip updating a variable
- Repetitive boilerplate
- Hard to see the transformation intent
- No single place to add cross-cutting concerns (logging, profiling)

## Analysis of Current Patterns

### Pattern A: Single-value pipes (1 transformed output)
- `to_native_messages(fixed_params, native) → native`
- `from_native_messages(fixed_params, core) → core`
- `init(config, state) → state`
- `get_models(config, models) → models`

### Pattern B: Multi-value pipes (2-3 transformed outputs)
- `finalize(finals, native, state) → (finals, native, state)`
- `process_chunk(chunk, partials, finals, native, state) → (partials, finals, native, state)`
- `initialize_request(native, state) → state`

### Pattern C: Mixed signatures (parameter order ≠ output order)
- `ext.finalize(final_messages=x, native_messages=y, state=z)` outputs `(x, y, z)`
- Requires adapter functions

## Proposed Solution

### Pipeline Utility

```python
from functools import reduce
from typing import Callable, List, TypeVar, Tuple, Any

def pipeline(*fixed_params):
    """Create a pipeline that applies transforms with fixed parameters.
    
    Args:
        *fixed_params: Parameters passed to all transforms but not modified.
        
    Returns:
        Function that takes (transforms, *initial_values) and returns transformed values.
        
    Example:
        pipe = pipeline(config, extra_context)
        result1, result2 = pipe(
            [plugin.transform for plugin in plugins],
            initial1, initial2
        )
    """
    def apply_transforms(transforms: List[Callable], *initial_transformed):
        if not transforms:
            return initial_transformed if len(initial_transformed) > 1 else initial_transformed[0]
        
        def reducer(transformed, transform):
            result = transform(*fixed_params, *transformed)
            # Normalize to tuple for consistent handling
            return result if isinstance(result, tuple) else (result,)
        
        initial = initial_transformed if len(initial_transformed) > 1 else (initial_transformed[0],)
        result = reduce(reducer, transforms, initial)
        
        # Unwrap single-element tuples for cleaner syntax
        return result[0] if len(result) == 1 else result
    
    return apply_transforms
```

## Refactoring Steps

### Step 1: Add pipeline utility ✓
- Add `pipeline()` helper function to `agent_core/core.py`
- Add comprehensive tests in `tests/test_pipeline_utility.py`
- Verify tests pass

### Step 2: Refactor provider.py pipes ✓

**Location 1: `provider.py:188-190` - init chain**
```python
# Before:
for ext in self._iter_extensions():
    self.state = ext.init(config, self._get_state())

# After:
pipe = pipeline(config)
self.state = pipe([ext.init for ext in self._iter_extensions()], self._get_state())
```

**Location 2: `provider.py:272-274` - initialize_request chain**
```python
# Before:
for ext in self._iter_extensions():
    new_state = ext.initialize_request(native_messages, new_state)

# After:
pipe = pipeline(native_messages)
new_state = pipe([ext.initialize_request for ext in self._iter_extensions()], new_state)
```

**Location 3: `provider.py:341-343` - apply_extension_transforms**
```python
# Before:
for ext in self._iter_extensions():
    transformed_native = ext.to_native_messages(messages, transformed_native)

# After:
pipe = pipeline(messages)
transformed_native = pipe([ext.to_native_messages for ext in self._iter_extensions()], transformed_native)
```

**Location 4: `provider.py:474-481` - process_chunk extension chain**
```python
# Before:
for ext in self._iter_extensions():
    partial_messages, final_messages, full_history, ext_state = ext.process_chunk(
        native_chunk=native_chunk,
        state=ext_state,
        partial_messages=partial_messages,
        final_messages=final_messages,
        native_messages=full_history,
    )

# After:
pipe = pipeline()
partial_messages, final_messages, full_history, ext_state = pipe(
    [lambda p, f, h, s: ext.process_chunk(
        native_chunk=native_chunk, state=s,
        partial_messages=p, final_messages=f, native_messages=h
    ) for ext in self._iter_extensions()],
    partial_messages, final_messages, full_history, ext_state
)
```

**Location 5: `provider.py:487-490` - from_native_messages in process_chunk**
```python
# Before:
core_partials = self.plugin.from_native_messages(partial_messages, ext_state)
for ext in self._extensions:
    core_partials = ext.from_native_messages(partial_messages, core_partials)

# After:
pipe = pipeline(partial_messages)
core_partials = pipe(
    [self.plugin.from_native_messages] + [ext.from_native_messages for ext in self._extensions],
    ext_state if not core_partials else core_partials  # Note: logic may need adjustment
)
```

**Location 6: `provider.py:522-527` - finalize extension chain**
```python
# Before:
for ext in self._iter_extensions():
    final_messages, full_history, new_state = ext.finalize(
        final_messages=final_messages,
        native_messages=full_history,
        state=new_state,
    )

# After:
pipe = pipeline()
final_messages, full_history, new_state = pipe(
    [lambda f, h, s: ext.finalize(final_messages=f, native_messages=h, state=s)
     for ext in self._iter_extensions()],
    final_messages, full_history, new_state
)
```

### Step 3: Refactor core.py pipes ✓

**Location 1: `core.py:240-242` - init feature chain**
```python
# Before:
for feature in self._features:
    state = feature.init({}, state)
    provider.set_state(state)

# After:
pipe = pipeline({})
for _ in self._features:
    state = pipe([feature.init for feature in self._features], state)
    provider.set_state(state)
# Note: This has side effects (set_state), may need special handling
```

**Location 2: `core.py:252-255` - to_native_messages feature chain**
```python
# Before:
for feature in self._features:
    suffix_native = feature.to_native_messages(core_new_msg, suffix_native)

# After:
pipe = pipeline(core_new_msg)
suffix_native = pipe([feature.to_native_messages for feature in self._features], suffix_native)
```

**Location 3: `core.py:655-657` - init feature chain in _pre_request**
```python
# Before:
for feature in features:
    state = feature.init(provider_config, state)
    provider.set_state(state)

# After:
pipe = pipeline(provider_config)
for _ in features:
    state = pipe([feature.init for feature in features], state)
    provider.set_state(state)
# Note: Side effect handling needed
```

**Location 4: `core.py:677-678` - to_native_messages feature chain in _pre_request**
```python
# Before:
for feature in features:
    native_messages = feature.to_native_messages(messages, native_messages)

# After:
pipe = pipeline(messages)
native_messages = pipe([feature.to_native_messages for feature in features], native_messages)
```

**Location 5: `core.py:682-684` - initialize_request feature chain**
```python
# Before:
for feature in features:
    state = feature.initialize_request(native_messages, state)
    provider.set_state(state)

# After:
pipe = pipeline(native_messages)
for _ in features:
    state = pipe([feature.initialize_request for feature in features], state)
    provider.set_state(state)
# Note: Side effect handling needed
```

**Location 6: `core.py:738-740` - finalize feature chain in send_request**
```python
# Before:
for feature in features:
    final_native, native_messages, state = feature.finalize(
        final_native, native_messages, state
    )

# After:
pipe = pipeline()
final_native, native_messages, state = pipe(
    [feature.finalize for feature in features],
    final_native, native_messages, state
)
```

**Location 7: `core.py:745-747` - from_native_messages extension and feature chain**
```python
# Before:
for ext in enabled_extensions:
    final_core = ext.from_native_messages(final_native, final_core)
for feature in features:
    final_core = feature.from_native_messages(final_native, final_core)

# After:
pipe = pipeline(final_native)
final_core = pipe(
    [ext.from_native_messages for ext in enabled_extensions] +
    [feature.from_native_messages for feature in features],
    final_core
)
```

**Location 8: `core.py:815-818` - finalize feature chain in send_request_stream**
```python
# Before:
for feature in features:
    final_native, native_messages, state = feature.finalize(
        final_native, native_messages, state
    )

# After:
pipe = pipeline()
final_native, native_messages, state = pipe(
    [feature.finalize for feature in features],
    final_native, native_messages, state
)
```

**Location 9: `core.py:825-829` - from_native_messages chains in send_request_stream**
```python
# Before:
for ext in enabled_extensions:
    final_core = ext.from_native_messages(combined_native_finals, final_core)
for feature in features:
    final_core = feature.from_native_messages(combined_native_finals, final_core)

# After:
pipe = pipeline(combined_native_finals)
final_core = pipe(
    [ext.from_native_messages for ext in enabled_extensions] +
    [feature.from_native_messages for feature in features],
    final_core
)
```

**Location 10: `core.py:888-891` - finalize feature chain in send_request_stream_async**
```python
# Before:
for feature in features:
    final_native, native_messages, state = feature.finalize(
        final_native, native_messages, state
    )

# After:
pipe = pipeline()
final_native, native_messages, state = pipe(
    [feature.finalize for feature in features],
    final_native, native_messages, state
)
```

**Location 11: `core.py:899-902` - from_native_messages chains in send_request_stream_async**
```python
# Before:
for ext in enabled_extensions:
    final_core = ext.from_native_messages(combined_native_finals, final_core)
for feature in features:
    final_core = feature.from_native_messages(combined_native_finals, final_core)

# After:
pipe = pipeline(combined_native_finals)
final_core = pipe(
    [ext.from_native_messages for ext in enabled_extensions] +
    [feature.from_native_messages for feature in features],
    final_core
)
```

### Step 4: Handle Side Effects ✓

Some transformations have side effects (e.g., `provider.set_state(state)`). Options:

1. **Keep imperative for side effects**: Only refactor pure transformations
2. **Pipeline with side effects**: Add callback parameter to pipeline
3. **Explicit side effect wrapper**: `pipe_with_effect(transforms, effect_fn, initial)`

Recommendation: Use option 1 for now - only refactor pure pipes, keep loops with side effects as-is.

## Benefits

1. **Less error-prone**: Can't accidentally skip updating one variable in the loop
2. **More declarative**: Shows intent (pipeline transformation) vs imperative loop
3. **Reusable**: Same pattern for all transformations
4. **Testable**: Pipeline logic separated from business logic
5. **Flexible**: Easy to add logging, profiling, or conditional transforms

## Risks & Mitigations

- **Readability**: Nested lambdas can be hard to read
  - *Mitigation*: Extract lambda factories for complex cases
- **Performance**: Extra function calls
  - *Mitigation*: Negligible for non-hot-path code; measure if concerned
- **Debugging**: Stack traces may be deeper
  - *Mitigation*: Add clear error messages in pipeline wrapper

## Future Enhancements

### Step 5: Standardize signatures (optional, breaking change)
- Align parameter order with output order for cleaner lambda-free calls
- This can be done later; temporary lambdas work fine

### Step 6: Add Pipeline Utilities
- `pipeline_with_logging()` - Log each transformation
- `pipeline_with_profiling()` - Profile performance
- `conditional_pipeline()` - Skip transforms based on predicates

## Testing Strategy

1. Unit tests for `pipeline()` utility
2. Regression tests: Ensure all existing tests pass
3. Integration tests: Verify end-to-end behavior unchanged
4. Performance tests: Measure overhead (should be negligible)
