# Plan: Modify existing core messages with native history preservation

## Goal

Add a functional "modify" operation in `agent_core.core.AgentCore` that updates the **content** of an existing `system`, `user`, or `assistant` message by index, returning a new `Session`. The operation should:
- Preserve or safely drop provider-native history (`native_messages`) based on `native_indices` when present.
- Never mutate roles, per-message metadata (other than `native_indices` when dropping native history), or session-level metadata beyond native-history bookkeeping.
- Keep the functional / immutable design: all operations return new objects.

## Public API shape

- Introduce a new public method on `AgentCore`:
  - `modify_message(self, session: Session, index: int, content: str, config: Optional[Dict[str, Any]] = None) -> Session`
- Semantics:
  - `index` refers to the core message index in `session.messages` (0-based, negative indices allowed like Python lists).
  - Only `content` is changed; `role` and `metadata` of the target message remain the same.
  - Only accepts messages whose `role` is `"system"`, `"user"`, or `"assistant"`.
  - For unsupported roles (e.g., `"tool"`) or out-of-range indices, raise a clear error (e.g., `IndexError` / `ValueError`).

## Internal helper: native-aware modify

Add a private helper analogous to `_append_single_message_with_native`:
- `_modify_single_message_with_native(self, session: Session, index: int, content: str, config: Optional[Dict[str, Any]]) -> Session`

Responsibilities:
- Perform a **native-preserving** modification when it is safe to do so.
- Fall back to a **core-only** modification that drops native history when safe preservation is not possible.

### 1. Common index and role validation

- Normalize `index` into `[0, len(messages)-1]`, supporting negatives; raise `IndexError` if out of range.
- Fetch the target `Message` and verify `role in {"system", "user", "assistant"}`; otherwise raise `ValueError`.

### 2. Fast path: no native history

If any of these hold:
- `session.metadata` is not a `dict`, or
- `"native_messages"` not in `session.metadata`, or
- No providers are registered (`self._providers` empty),

then:
- Build a new `messages` list where all entries are the same `Message` instances except for `index`, which is replaced by a new `Message` with updated `content` and identical `role` and `metadata`.
- Build new session metadata as `dict(session.metadata)` and **remove** keys `"native_messages"` and `"native_messages_integrity"` if they exist (defensive cleanup for odd inputs).
- Return a new `Session` instance with the updated messages and metadata.

### 3. Native-preserving preconditions

Attempt the native-preserving path only when all are true:
- `session.metadata` is a `dict` and `session.metadata["native_messages"]` is a `list` (`original_native`).
- Exactly one provider is registered **or** `config` is provided and resolves cleanly via `_resolve_plugins_for_config(config)`.
- `_verify_native_integrity(session)` succeeds (otherwise propagate its `RuntimeError`, matching existing behavior of `_append_single_message_with_native`).

If any of these fail, fall back to the **core-only with dropped native history** path described in section 5.

### 4. Build core↔native index mappings

Using logic parallel to `slice_session`:
- Let `messages = list(session.messages)` and `native_len = len(original_native)`.
- For each core index `i` and message `msg`:
  - Extract `metadata` as a dict and look up `native_indices`.
  - If `native_indices` is missing or not a list of ints, or any index is out of `[0, native_len)`, treat this as an unsupported mapping and **fallback** to the core-only path.
  - Build:
    - `core_to_native[i] = normalized_indices` (deduplicated, in-order list of ints).
    - `native_to_core[j]` as a `Set[int]` of owning core indices per native index.

For the target `index`:
- If it has no entry in `core_to_native`, we cannot safely update native history; fallback to the core-only path.
- If **any** `j` in `core_to_native[index]` has `len(native_to_core[j]) > 1` (i.e., that native message is shared across multiple core messages), fallback to the core-only path. This avoids modifying native messages that are logically owned by more than one core message.

### 5. Core-only modification with native history dropped (fallback)

When native-preserving conditions or mappings are not satisfied:
- Create a new list `new_messages`:
  - For each index `i` and message `msg`:
    - Derive `data = msg.to_dict()` and `md = dict(data.get("metadata") or {})`.
    - **Strip** `"native_indices"` from `md` (as in `_slice_session_core_only`).
    - For `i == index`, build a `Message` with updated `content` and same `role`; for other indices, keep original `content`.
- Build `new_metadata = dict(session.metadata) if metadata is dict else {}`.
- Remove `"native_messages"` and `"native_messages_integrity"` from `new_metadata`.
- Return new `Session(session_id=session.session_id, messages=new_messages, metadata=new_metadata)`.

This guarantees that any subsequent `send_request*` call will reconstruct provider-native history from core messages (via the existing `_pre_request` logic) without stale indices.

### 6. Native-preserving modification

If all preconditions pass and mappings are valid:

1. **Determine target native indices**
   - Let `owner_indices = core_to_native[index]` (deduplicated list of ints).

2. **Convert modified core message to native suffix**
   - Build a single-element core message dict:
     - `{ "role": target.role, "content": new_content, "metadata": md_copy }`, where `md_copy` is a shallow copy of the original metadata (including `native_indices`; it is metadata only and not interpreted by the conversion pipeline).
   - Invoke `_core_messages_to_native_for_config([core_msg_dict], config or {})` inside a `try` block.
   - If conversion raises or returns a non-list, fallback to the core-only path.

3. **Cardinality check**
   - Let `new_native_suffix` be the converted list.
   - If `len(new_native_suffix) != len(owner_indices)`, fallback to the core-only path, because we cannot safely remap global indices without re-normalizing all messages.

4. **Patch native history**
   - Create `new_native = list(original_native)`.
   - For each `k, j` in `enumerate(owner_indices)`, assign `new_native[j] = new_native_suffix[k]`.

5. **Patch core messages (content only)**
   - Build `new_messages` as a new list:
     - For `i != index`, reuse the existing `Message` instances from `session.messages`.
     - For `i == index`, create a new `Message(role=target.role, content=new_content, metadata=target.metadata)`.
     - `native_indices` in `target.metadata` remain unchanged (they still point at the same global indices we just updated).

6. **Recompute native integrity and build new session**
   - Compute `new_integrity = self._compute_native_integrity(new_messages)`.
   - Build `new_metadata = dict(session.metadata)`.
   - Set `new_metadata["native_messages"] = new_native`.
   - Set `new_metadata["native_messages_integrity"] = new_integrity`.
   - Return a new `Session` instance of the same type as `session` (e.g. `type(session)(...)`).

## Tests to add

- Unit tests in `core/python/tests/test_core.py`:
  - `test_modify_message_core_only_no_provider`: modify a user message when no provider is registered; verify only that message’s `content` changes, session length unchanged, and no `native_messages` keys appear.
  - `test_modify_message_preserves_native_simple_1_to_1`: with `DummyProvider` and a simple 1:1 mapping (each core message has exactly one native index), modify a user message and assert:
    - The target message’s `content` is updated.
    - `native_messages` length is unchanged; the corresponding native entry’s `content` is updated.
    - `native_indices` for the message and others remain valid and unchanged.
  - `test_modify_message_drops_native_on_shared_indices`: manually construct a session like the existing slice tests where multiple messages share native indices; modify one message and assert that `native_messages`, `native_messages_integrity`, and all per-message `native_indices` are removed.
  - `test_modify_message_rejects_tool_role`: ensure modifying a `tool` message raises `ValueError`.

## Documentation updates

- Update `core/python/README.md` and `docs/api/core-sdk.md`:
  - Add `modify_message` to the documented `AgentCore` methods list.
  - Briefly describe that it updates message `content` by index while preserving provider-native history when safely possible, otherwise dropping native history so it can be reconstructed on the next request.
