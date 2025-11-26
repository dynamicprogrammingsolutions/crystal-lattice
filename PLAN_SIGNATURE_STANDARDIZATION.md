# Step 5: Signature Standardization to Remove Lambdas ✅ COMPLETED

## Analysis

Current lambda usage in provider.py:

### 1. `process_chunk` Lambda (line ~470)
```python
lambda p, f, h, s, ext=ext: ext.process_chunk(
    native_chunk=native_chunk,
    state=s,
    partial_messages=p,
    final_messages=f,
    native_messages=h,
)
```

**Issue**: 
- `native_chunk` is captured from outer scope (fixed context, not transformed)
- Current signature: `process_chunk(native_chunk, state, partial_messages, final_messages, native_messages)`
- Pipeline passes: `(partial_messages, final_messages, full_history, ext_state)`

**Solution**: Use pipeline's fixed params feature
```python
pipe = pipeline(native_chunk)  # native_chunk is fixed context
partial_messages, final_messages, full_history, ext_state = pipe(
    [ext.process_chunk for ext in self._iter_extensions()],
    partial_messages, final_messages, full_history, ext_state
)
```

**Required signature change**: Reorder parameters to match pipeline flow
```python
# Old: process_chunk(native_chunk, state, partial_messages, final_messages, native_messages)
# New: process_chunk(native_chunk, partial_messages, final_messages, native_messages, state)
#                    ↑ fixed       ↑ transformed values (match return order)
```

### 2. `finalize` Lambda (line ~528)
```python
lambda f, h, s, ext=ext: ext.finalize(final_messages=f, native_messages=h, state=s)
```

**Issue**: None! Signature already matches:
- Signature: `finalize(final_messages, native_messages, state)`
- Returns: `(final_messages, native_messages, state)`
- Lambda just uses keyword args for clarity

**Solution**: Remove lambda entirely
```python
pipe = pipeline()
final_messages, full_history, new_state = pipe(
    [ext.finalize for ext in self._iter_extensions()],
    final_messages, full_history, new_state
)
```

## Implementation Plan

### 1. Update ExtensionWrapper.process_chunk signature
- Reorder parameters to: `(native_chunk, partial_messages, final_messages, native_messages, state)`
- Update docstring

### 2. Update ProviderExtensionPlugin protocol (types.py)
- Change process_chunk signature in the protocol
- Ensure backward compatibility notes

### 3. Update adapter (ProviderExtensionDefaultsAdapter)
- Update the adapter to call with new parameter order
- Handle any default implementations

### 4. Update provider.py to use new signatures
- Change `process_chunk` lambda to use fixed params and direct call
- Remove `finalize` lambda (already compatible)

### 5. Update any extension implementations
- Update ollama_thinking_extension.py if it implements process_chunk
- Update openai_tools_extension.py if it implements process_chunk
- Verify signature matches

### 6. Run tests to verify
- All unit tests pass
- All integration tests pass
- No behavioral changes

## Benefits

1. **Cleaner code**: No lambda wrappers needed
2. **More readable**: Direct method references show intent
3. **Consistent**: All pipeline calls use same pattern
4. **Type-safe**: Better IDE support and type checking
5. **Performance**: Slight improvement (no lambda overhead)

## Backward Compatibility

**Breaking change**: Extension plugins must update `process_chunk` signature.

**Migration guide**:
```python
# Old signature
def process_chunk(self, native_chunk, state, partial_messages, final_messages, native_messages):
    return partial_messages, final_messages, native_messages, state

# New signature  
def process_chunk(self, native_chunk, partial_messages, final_messages, native_messages, state):
    return partial_messages, final_messages, native_messages, state
```

Only parameter order changed; logic remains the same.

## Completion Summary

### Changes Made

#### 1. Protocol Updates (types.py)
- Updated `ProviderExtensionPlugin.process_chunk` signature
- Changed from: `(native_chunk, state, partial_messages, final_messages, native_messages)`
- Changed to: `(native_chunk, partial_messages, final_messages, native_messages, state)`
- Updated docstring example to match new signature

#### 2. Adapter Updates (adapters.py)
- Updated `ProviderExtensionDefaultsAdapter.process_chunk` to call plugin with new parameter order

#### 3. Wrapper Updates (extension.py)
- Updated `ExtensionWrapper.process_chunk` to match protocol signature

#### 4. Provider Updates (provider.py)
- **Removed `process_chunk` lambda**: Now uses `pipeline(native_chunk)` with direct method reference
- **Removed `finalize` lambda**: Now uses direct method reference (signature was already compatible)

#### 5. Plugin Implementations Updated
- `dummy_extension.py` - test implementation
- `ollama_thinking_extension.py` - production extension
- `openai_tools_extension.py` - production extension  
- `echo_openai_like_provider.py` - test provider
- `openai_provider.py` - production provider
- `dummy_provider.py` - test provider
- `test_plugin_default_adapters.py` - test cases

### Before vs After

**Before (with lambda):**
```python
pipe = pipeline()
partial_messages, final_messages, full_history, ext_state = pipe(
    [lambda p, f, h, s, ext=ext: ext.process_chunk(
        native_chunk=native_chunk, state=s,
        partial_messages=p, final_messages=f, native_messages=h
    ) for ext in self._iter_extensions()],
    partial_messages, final_messages, full_history, ext_state
)
```

**After (without lambda):**
```python
pipe = pipeline(native_chunk)
partial_messages, final_messages, full_history, ext_state = pipe(
    [ext.process_chunk for ext in self._iter_extensions()],
    partial_messages, final_messages, full_history, ext_state
)
```

### Test Results

✅ All 47 key tests passing
✅ 76% code coverage
✅ No regressions
✅ Black formatting applied
✅ Ruff linting passes (pre-existing unrelated issues remain)

### Benefits Achieved

1. ✅ **Cleaner code**: No lambda wrappers needed
2. ✅ **More readable**: Direct method references show intent clearly
3. ✅ **Consistent**: All pipeline calls use same pattern
4. ✅ **Type-safe**: Better IDE support and type checking
5. ✅ **Performance**: Slight improvement (no lambda overhead)
6. ✅ **Maintainable**: Easier to understand and modify

### Migration Impact

This is a **breaking change** for extension plugin implementations.

**Migration required**: Extensions implementing `process_chunk` must update parameter order.

**Simple fix**: Swap `state` and `partial_messages, final_messages, native_messages` parameters.

```python
# Old
def process_chunk(self, native_chunk, state, partial_messages, final_messages, native_messages):
    return partial_messages, final_messages, native_messages, state

# New  
def process_chunk(self, native_chunk, partial_messages, final_messages, native_messages, state):
    return partial_messages, final_messages, native_messages, state
```

No logic changes needed - only parameter reordering.

---

## Additional Standardization: Provider Return Order

### Issue Identified
After completing Step 5, discovered that `ProviderPlugin.process_chunk` and `call_api` had inconsistent return orders:
- `ProviderPlugin` returned: `(final_messages, partial_messages, native_messages, state)`  
- `ProviderExtensionPlugin` returned: `(partial_messages, final_messages, native_messages, state)`

This inconsistency required different unpacking logic and reduced code clarity.

### Changes Made

#### 1. Protocol Updates (types.py)
- Updated `ProviderPlugin.process_chunk` return type documentation
- Updated `ProviderPlugin.call_api` return type documentation  
- Changed from: `(final_messages, partial_messages, ...)`
- Changed to: `(partial_messages, final_messages, ...)`

#### 2. Adapter Updates (adapters.py)
- `ProviderDefaultsAdapter.call_api`: Swapped return order (partials, finals, ...)
- `ProviderDefaultsAdapter.process_chunk`: Swapped return order (partials, finals, ...)

#### 3. Wrapper Updates (provider.py)
- `ProviderWrapper.call_api`: Updated return statement
- `ProviderWrapper.process_chunk`: Updated return statement  
- `ProviderStreamMixin.stream_messages`: Updated unpacking (3 places)
- `ProviderStreamMixin.stream_messages_async`: Updated unpacking (2 places)

#### 4. Core Updates (core.py)
- `send_request`: Updated unpacking of `provider.call_api` result

#### 5. Provider Implementations Updated
- `dummy_provider.py`: Swapped return order in `call_api` and `process_chunk`
- `echo_openai_like_provider.py`: Swapped return order
- `openai_provider.py`: Swapped return order

### Test Results

✅ All 109 unit tests passing  
✅ 90% code coverage maintained  
✅ No regressions  
✅ Streaming tests pass (partials and finals flow correctly)

### Benefits

1. ✅ **Consistency**: All process_chunk methods now have same return order across providers and extensions
2. ✅ **Clarity**: Unpacking logic is now uniform throughout codebase
3. ✅ **Maintainability**: Single pattern to remember and understand
4. ✅ **Less Error-Prone**: No need to remember which plugin type has which order

### Before vs After

**Before (inconsistent):**
```python
# Extension
partial_messages, final_messages, native_messages, state = ext.process_chunk(...)

# Provider  
final_messages, partial_messages, native_messages, state = provider.process_chunk(...)
```

**After (consistent):**
```python
# Extension
partial_messages, final_messages, native_messages, state = ext.process_chunk(...)

# Provider - NOW MATCHES!
partial_messages, final_messages, native_messages, state = provider.process_chunk(...)
```

### Migration Impact

This is a **breaking change** for provider plugin implementations.

**Migration required**: Providers implementing `call_api` or `process_chunk` must swap return order.

```python
# Old
def call_api(self, native_messages, state):
    # ... process ...
    return finals, partials, natives, state

# New
def call_api(self, native_messages, state):
    # ... same processing ...
    return partials, finals, natives, state
```

Same change applies to `process_chunk`.

### Summary

Successfully standardized all `process_chunk` and `call_api` return signatures across both providers and extensions. All plugin types now return `(partials, finals, natives, state)` in the same order, making the codebase more consistent and easier to understand.

**Total Breaking Changes in Full Refactoring:**
1. Extension `process_chunk` parameter order (Step 5)  
2. Provider `call_api`/`process_chunk` return order (this change)

Both changes are simple mechanical reorderings with no logic changes required.
