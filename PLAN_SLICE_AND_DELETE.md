**Request**

I want to implement a slice and remove option in core. This will be used for example when the user want to delete a specific message or want to fork the session at specific point. The problem with this is that the  from_native_messages may return different array size, for example with some native formats, reasoning may come in different messages. Also the conversion from_native_messages and to_native_messages may not preserve everything. At the same time, the slice option should work with the core message index, while it should affect the native messages. I propose the following solution: when converting with from_native_messages, the provider will have to assign the original index to the messages. This could, be done with an optional native_indices array added to the returned messages array. The core must check, and if the plugin returns an array with different size with no original index, the core must throw an error. There are times, when only one messages are converted and it's attached to the end of messages. This time, the native_indices must be adjusted accordingly, for example if native_indices are [0,1] when converted native messages [0,1] and that core message is appended after the message with native_indices 6, it's native_indices value will be adjusted to [7,8].

Additionally: message↔native links can be more complex than identical sets. A more robust solution is:
- When determining messages to keep, start from the core slice (core indices).
- From that, compute a **forward mapping slice** of native indices.
- Then, using a **reverse mapping** native→core, drop any native index whose linked core messages are not all kept.
- Finally, rebuild the core messages list from the adjusted native history using the conversion functions.

Example:
- Message 0: `native_indices = [0,1]`
- Message 1: `native_indices = [1,0]`
  - Native 0 is linked to msg 0 and 1; native 1 is also linked to msg 0 and 1.
  - If the slice keeps only message 0 initially, the reverse mapping shows that natives 0 and 1 are also linked to removed message 1, so both natives are dropped (no consistent native slice for only msg 0).
- Chain example:
  - msg 0 → [0,1]
  - msg 1 → [1,2]
  - msg 2 → [2,3]
  - Removing any of the three core messages forces removal of native segments shared across removed and kept messages; this can cascade and prune most or all native indices for that connected component.

Investigate the existing code, how it works, and how exactly the slice function should be built, what it will do under the hood to get a new session with a modified set of messages. Provide me a plan.

---

**Overview**

- Core already retains provider-native history on the session (`session.metadata.native_messages`) and guards it with `native_messages_integrity` (see `core/python/agent_core/core.py:75` and `ARCHITECTURE.md:102`).
- `AgentCore` currently exposes `create_session`, `add_message`, `send_request*`, export/import, but no remove/slice operations (see `core/python/agent_core/core.py:194` and `core/python/README.md:41`).
- Native history is reused on subsequent turns via `_pre_request`, and integrity is enforced whenever `native_messages` is present (see `core/python/agent_core/core.py:97` and `core/python/tests/test_native_integrity.py:18`).

The goal is to add:
- A **pure slice/remove operation** that works in terms of core message indices but consistently updates provider-native history.
- A precise mapping between core messages and native indices, treated as a bipartite graph and handled via forward+reverse mapping rather than only equal-set grouping.
- A `config`-aware version of both **slice** and **add_message**, so that all conversions respect the active provider, extensions, and features selected for that configuration.

Below is a concrete design/implementation plan.

---

**1. Current Message & Native History Flow**

- Core data types:
  - `Message` and `Session` are frozen dataclasses; `Session` holds `messages` and `metadata` (see `core/python/agent_core/types.py:90` and `core/python/agent_core/types.py:739`).
- Native history retention:
  - After each request, `send_request` and `send_request_stream*` set:
    - `session.metadata["native_messages"]` = full provider-native history for the turn.
    - `session.metadata["native_messages_integrity"]` = checksum over `session.messages` (`core/python/agent_core/core.py:748` and `core/python/agent_core/core.py:764`).
- Integrity rules:
  - Any time core touches a session that has `native_messages`, it verifies the checksum:
    - `_verify_native_integrity` compares `message_count` and a length-based checksum (`core/python/agent_core/core.py:97`).
    - If mismatch, it raises and advises users to remove `native_messages` to modify history (`core/python/agent_core/core.py:117` and `core/python/tests/test_native_integrity.py:18`).
- Reuse vs reconstruction:
  - `_pre_request`:
    - If `native_messages` present and integrity holds, it **trusts** that list as full provider-native history and skips `to_native_messages` (`core/python/agent_core/core.py:655`).
    - Otherwise it reconstructs via provider + extensions + features (`to_native_messages` pipeline, `core/python/agent_core/core.py:672`).
- Adding messages:
  - `add_message` appends a `Message` and, when exactly one provider is registered and `native_messages` exists, converts only the new message to native and appends that suffix (`core/python/agent_core/core.py:245` and `core/python/agent_core/core.py:255`).
  - It then recomputes `native_messages_integrity` (`core/python/agent_core/core.py:266`).

**Implication:** Core already has the concept of “native history belongs to this immutable sequence of messages”. But there is **no explicit mapping from each core message to specific native message indices**, and `from_native_messages` is assumed to be “shape compatible enough” without enforcement.

---

**2. Requirements for Slice/Remove (Updated)**

From the combined requirements and constraints:

- **Functional goals**:
  - Delete arbitrary core messages (e.g. remove a specific user or assistant message).
  - Fork the session at a specific point, i.e. keep only a prefix of the messages and start a new branch from there.

- **Indexing**:
  - Operations are expressed in terms of **core message indices** (0-based positions in `Session.messages`).
  - Under the hood, they must consistently adjust **provider-native messages** and their mapping.

- **Native/core mapping**:
  - `from_native_messages` may:
    - Return a list of core messages of **different length** than its `native_messages` input.
    - Lose or merge reasoning, tool-calls, etc.
  - When that happens, the provider (or extensions/features) must supply **explicit mapping information** so that Core knows which native indices correspond to each core message.
  - If the plugin pipeline changes cardinality and **does not supply mapping**, Core must **raise** (for sessions that keep native retention) rather than silently produce unusable native history.

- **Forward+reverse consistency**:
  - Multiple core messages can share native indices, and vice versa; link patterns can form chains or more complex graphs.
  - We treat mapping as a bipartite graph between core message positions and native indices.
  - Slice/remove logic must:
    - Start from the **core slice** (indices to keep/remove).
    - Use the **forward mapping** (core→native) to propose a native slice.
    - Use the **reverse mapping** (native→core) to retain only native indices that are linked **only** to kept core messages.
    - Rebuild core messages from the final native slice using the provider + extensions + features, then recompute integrity.

- **Config awareness**:
  - Which provider, extensions, and features are active depends on the config (via tags, model selection, etc.).
  - Therefore both:
    - `add_message`, and
    - the new `slice_session`

    must accept a `config` parameter so they can:
    - Resolve the correct provider and enabled plugins (`_resolve_plugins_for_config`).
    - Use the appropriate to/from-native pipelines.

---

**3. Design: Native Index Tracking & Mappings**

Introduce a **per-core-message mapping** from core messages to provider-native indices, plus forward and reverse mappings across the whole session:

- Representation:
  - Use a well-defined key in per-message metadata:
    - `metadata["native_indices"]`: `List[int]`.
    - Each value is a list of **0-based indices into the global `session.metadata.native_messages` list** (after any global adjustment done by core at append time).
  - This keeps mapping attached to messages (and serialized) without changing public dataclass types or plugin protocols.

- Provider/extension contract for from-native pipelines:
  - For the final from-native pipeline (provider → extensions → features) used to convert **final native deltas** to core messages:
    - Let `native_messages` be the provider-native list for this turn’s **finals**:
      - Non-streaming: `final_native = final_native_1 + final_native_2` in `send_request`.
      - Streaming: `combined_native_finals` (aggregated finals + finalize output) in `send_request_stream` / `send_request_stream_async`.
    - Let `messages` be the resulting core messages list after provider, extensions, and features `from_native_messages` have all run.

  - New invariant:
    - If `len(messages) == len(native_messages)`:
      - Core **may** infer a 1:1 mapping by default (`native_indices = [i]`) unless the plugin explicitly sets `native_indices`.
    - If `len(messages) != len(native_messages)`:
      - **Every** message in `messages` must have `metadata["native_indices"]` populated with indices in `range(len(native_messages))`.
      - Otherwise core raises a descriptive error (e.g. “from_native_messages changed message count without providing native_indices mapping”).

  - Providers/extensions/features are free to agree on who sets `native_indices` as long as the final result satisfies the invariant.

- Local vs global indices:
  - Within the from-native pipeline for a single turn, it is convenient for plugins to treat `native_indices` as **local indices into the finals list** that they see (e.g. `final_native` or `combined_native_finals`).
  - Core will then rewrite these local indices into **global indices** into the full `session.metadata.native_messages` list at append time using a baseline offset (see section 4).

- Session-wide forward and reverse mappings:
  - For a given session, core can build:
    - `core_to_native[i] = list of global native indices used by message i`.
    - `native_to_core[j] = set of message indices that reference native index j`.
  - Slice/remove will:
    1. Determine kept core indices `K` from the user’s slice.
    2. Forward mapping: compute `N0 = ⋃_{i∈K} core_to_native[i]`.
    3. Reverse mapping: compute final `N` by keeping only those `j` where `native_to_core[j] ⊆ K`.
    4. `N` becomes the consistent native slice.

---

**4. Where to Populate Native Indices (with Helpers)**

To keep the logic consistent and avoid duplication, introduce two internal helpers on `AgentCore`:

- `_normalize_final_core_with_native_indices(final_core, finals_native, baseline_offset) -> List[Dict[str, Any]]`
  - Inputs:
    - `final_core`: list of core message dicts output by the complete from-native pipeline for this turn.
    - `finals_native`: the **per-turn finals** native list used as context for from-native (`final_native` or `combined_native_finals`).
    - `baseline_offset`: integer offset into the full `native_messages` history where these finals will be appended.
  - Behavior:
    - If `len(final_core) == len(finals_native)`:
      - For each message `i` lacking `metadata["native_indices"]`, set local `[i]`.
    - If `len(final_core) != len(finals_native)`:
      - Verify **every** message has `metadata["native_indices"]`.
      - If any is missing, raise an error explaining that plugins that change cardinality must provide `native_indices`.
    - Normalize per-message `native_indices` so they are valid local indices in `range(len(finals_native))`.
    - Rewrite them to **global indices** into `session.metadata.native_messages`:
      - `global_indices = [baseline_offset + j for j in local_indices]`.
      - Store back under `metadata["native_indices"]`.
    - Return the updated core message dicts.

- `_append_single_message_with_native(session, message_dict, config) -> Tuple[Session, Optional[List[int]]]`
  - Used by `add_message` when native history is present and we want to preserve mapping.
  - Inputs:
    - `session`: existing Session.
    - `message_dict`: core dict for the new message (`{"role", "content", "metadata"}`).
    - `config`: current config used to resolve provider & plugins.
  - Behavior (high level):
    - If there is not exactly one provider registered **or** `session.metadata["native_messages"]` is not a list:
      - Return a Session with the message appended but **without** modifying or creating native history (mapping not available).
    - Otherwise:
      - Resolve provider and enabled features/extensions from `config` using `_resolve_plugins_for_config`.
      - Initialize provider and features with this config (similar to `_pre_request`, but only for a single-message suffix).
      - Convert the single new core message to native using the **same provider + extensions + features pipeline** as `_pre_request` would use for a suffix.
      - Let `retained_native` be the existing `session.metadata["native_messages"]` and `suffix_native` be the converted list.
      - Append `suffix_native` to `retained_native` to produce `new_native`.
      - Compute `base_len = len(retained_native)` and `suffix_len = len(suffix_native)`.
      - Set `message_dict["metadata"]["native_indices"] = list(range(base_len, base_len + suffix_len))`.
      - Build the new `Session` with:
        - Messages: old messages + new `Message` built from `message_dict`.
        - Metadata: `native_messages = new_native`, and updated `native_messages_integrity`.
      - Return the new `Session` and the list of global indices just assigned.

With these helpers in place, we can specify where they are used.

***4a. In `AgentCore.add_message` (config-aware)***

- Change signature to accept an optional `config` parameter:

  ```python
  def add_message(
      self,
      session: Session,
      role: MessageRole,
      content: str,
      metadata: Optional[Dict[str, Any]] = None,
      config: Optional[Dict[str, Any]] = None,
  ) -> Session:
  ```

- Behavior:
  - Construct `message_dict = {"role": role, "content": content, "metadata": metadata or {}}`.
  - If `config` is **None**:
    - Preserve current behavior as a compatibility mode:
      - Append the core `Message`.
      - If there is a single provider and native history, perform the current approximate native-suffix append (using all registered features without tag filtering).
      - Do **not** attempt to compute `native_indices` (native-preserving slicing will later have to drop native history for such sessions).
  - If `config` is provided:
    - If there is a single provider and native history is a list:
      - Use `_append_single_message_with_native(session, message_dict, config)`.
    - Else:
      - Append purely at core level (no native, no mapping).

***4b. In `AgentCore.send_request` (non-streaming)***

- After `_pre_request`, store `baseline_native_len = len(native_messages)`.
- After provider.call_api + provider.finalize + feature.finalize, you have:
  - `final_native` (provider-native finals for this turn).
  - `native_messages` (full, post-turn native history).
- Convert to core via provider.from_native_messages and the extension/feature from-native pipeline as today, resulting in `final_core`.
- Before constructing dataclass `Message` objects:
  - Call `_normalize_final_core_with_native_indices(final_core, final_native, baseline_native_len)`.
  - Then convert each dict to `Message` and append; `session.metadata["native_messages"]` is set to the full `native_messages` and integrity is recomputed as today.

***4c. In `AgentCore.send_request_stream` and `send_request_stream_async`***

- After `_pre_request`, store `baseline_native_len = len(native_messages)`.
- At the end of streaming + finalize you have:
  - `combined_native_finals` (aggregated streaming finals + provider.finalize finals).
  - Updated full `native_messages`.
- Convert to core via provider.from_native_messages and the extension/feature from-native pipeline, resulting in `final_core`.
- Call `_normalize_final_core_with_native_indices(final_core, combined_native_finals, baseline_offset=baseline_native_len)`.
- Then construct `Message` dataclasses, update `session.metadata["native_messages"]` and `native_messages_integrity` as today.

---

**5. Slice/Remove API Surface (Config-Aware)**

Define a **pure functional** slice API on `AgentCore` that is config-aware:

- Proposed method signatures (names can be refined):

  ```python
  def slice_session(
      self,
      session: Session,
      config: Optional[Dict[str, Any]] = None,
      *,
      start: Optional[int] = None,
      end: Optional[int] = None,
      remove_indices: Optional[List[int]] = None,
  ) -> Session:
  ```

  - Returns a new `Session` whose logical `messages` list equals:
    - `session.messages[start:end]` with `remove_indices` excluded,
    - but which may be **reconstructed** from adjusted native history when mapping is available.

- Optional convenience fork helper:

  ```python
  def fork_session(
      self,
      session: Session,
      config: Optional[Dict[str, Any]] = None,
      upto_index: int,
      new_session_id: Optional[str] = None,
  ) -> Session:
  ```

  - Internally computes `start=0, end=upto_index + 1`, then calls `slice_session` with those bounds and the same config.
  - If `new_session_id` is provided, uses it for the returned Session; otherwise reuses the original session_id.

- API semantics:
  - Indices are 0-based like Python lists.
  - Negative indices follow Python semantics (resolved against `len(session.messages)`).
  - `remove_indices` are interpreted relative to the **original** `session.messages` indices, not the sliced subset.
  - When `config` is **None**:
    - Slice/remove operates purely on core messages.
    - `native_messages` and `native_messages_integrity` are dropped from metadata (see fallback section).
  - When `config` is provided and mapping is available, core will try to preserve and adjust native history using the forward+reverse algorithm.

---

**6. Slice Algorithm with Forward + Reverse Mapping & Reconstruction**

Given a session `S`, a config (possibly `None`), and user parameters, we compute a new Session as follows.

1. **Resolve final kept/remove index sets**

   - Normalize `start`/`end` to concrete indices for the original message list (respecting negative indices).
   - Compute the initial set of indices to keep/remove:
     - Let `all_indices = range(len(S.messages))`.
     - If `start`/`end` provided:
       - `range_indices = set(range(start, end))`.
     - If `remove_indices` provided:
       - `remove_set_0 = set(remove_indices)`.
     - Define `keep_set_0` as:
       - If `range_indices` is not None: `keep_set_0 = range_indices - remove_set_0`.
       - Else: `keep_set_0 = set(all_indices) - remove_set_0`.

2. **If no config → core-only slice with dropped native history**

   - If `config` is `None`:
     - Build `kept_messages = [S.messages[i] for i in sorted(keep_set_0)]`.
     - `new_metadata = dict(S.metadata)`.
     - Remove `"native_messages"` and `"native_messages_integrity"` from `new_metadata`.
     - Also remove any stale `native_indices` from per-message metadata to avoid confusion.
     - Return `Session(session_id=S.session_id, messages=kept_messages, metadata=new_metadata)`.
     - This is functionally equivalent to the current documented “bypass by removing native history” pattern.

3. **Config provided: verify native history & mapping availability**

   - If `config` not `None` and `"native_messages"` not in `S.metadata` or not a list:
     - We cannot preserve mapping; fall back to core-only slice as in step 2.
   - Otherwise, call `_verify_native_integrity(S)`; if it raises, propagate the error.

   - Build forward and reverse maps:
     - Initialize `core_to_native: Dict[int, List[int]] = {}` and `native_to_core: Dict[int, Set[int]] = {}`.
     - For each original message index `i` in `all_indices`:
       - Let `m = S.messages[i]` and `md = m.metadata or {}`.
       - `native_indices_i = md.get("native_indices")`.
       - If `native_indices_i` is a list of ints:
         - `core_to_native[i] = list(native_indices_i)`.
         - For each `j` in `native_indices_i`:
           - Add `i` to `native_to_core.setdefault(j, set())`.
   - If any message in `keep_set_0` has invalid/non-int `native_indices` while claiming to use native history, we cannot safely preserve mapping; fall back to step 2.

4. **Forward mapping: candidate native indices**

   - Let `K = keep_set_0`.
   - Compute initial candidate native set:

     ```python
     N0: Set[int] = set()
     for i in K:
         for j in core_to_native.get(i, []):
             N0.add(j)
     ```

   - `N0` is the union of all native indices referenced by kept core messages.

5. **Reverse mapping: prune natives used by removed messages**

   - Let `R = set(all_indices) - K` be the set of removed core indices.
   - Define final native set `N` as:

     ```python
     N = {
         j for j in N0
         if native_to_core.get(j, set()).issubset(K)
     }
     ```

   - Intuition:
     - We keep only those native indices such that **every** core message referencing them is kept.
     - Any native index shared between a kept and a removed core message is dropped.
   - In highly interconnected mappings (e.g. chains), this can cause a large contiguous block of native history to be dropped when even a single core message is removed.

6. **Build new native history**

   - Let `original_native = S.metadata["native_messages"]`.
   - Validate every `j in N` is in `range(len(original_native))`; if any is out of range, fall back to core-only slice.
   - Let `used_native_indices_sorted = sorted(N)`.
   - Build `new_native = [original_native[j] for j in used_native_indices_sorted]`.
   - Build mapping `old_to_new = {old_idx: new_idx for new_idx, old_idx in enumerate(used_native_indices_sorted)}` (mainly useful for diagnostics or future enhancements).

7. **Reconstruct core messages from adjusted native history**

   Treat `new_native` as the canonical provider-native history for the sliced session and reconstruct the entire core message sequence from it using the configured provider and plugins.

   - Resolve provider and enabled plugins for this config:
     - Call `_resolve_plugins_for_config(config)` to obtain `provider`, `enabled_extensions`, `enabled_features`, `tools`, `tags`.
   - Initialize provider state similar to `_pre_request`, but skip `to_native_messages` (we already have native):
     - `provider_config = config` (optionally extended with tool schemas if desired).
     - `state = provider.init(provider_config)`.
     - For each feature in `enabled_features`: `state = feature.init(provider_config, state)` and `provider.set_state(state)`.
   - Optionally run `initialize_request` on `new_native` to let features/extensions adjust state:
     - `state = provider.initialize_request(new_native, state)`.
     - For each feature: `state = feature.initialize_request(new_native, state)` and `provider.set_state(state)`.
   - Convert provider-native to core using the full from-native pipeline over the entire adjusted history:
     - `core_from_provider = provider.from_native_messages(new_native, state)`.
     - `pipe = pipeline(new_native)`.
     - `core_full = pipe(
           [ext.from_native_messages for ext in enabled_extensions]
           + [feat.from_native_messages for feat in enabled_features],
           core_from_provider,
       )`.
   - `core_full` is now the canonical core message list for the sliced native history; it may differ from the original `S.messages`.

8. **Re-attach global native_indices for reconstructed messages**

   - The new global native index space is simply `range(len(new_native))`.
   - Call `_normalize_final_core_with_native_indices(core_full, new_native, baseline_offset=0)`.
     - This enforces cardinality/mapping rules and rewrites `native_indices` to `0..len(new_native)-1`.
   - Convert each dict in the returned list to `Message` dataclasses: `new_messages`.

9. **Build new session metadata and return**

   - `new_metadata = dict(S.metadata)`.
   - Set:
     - `new_metadata["native_messages"] = new_native`.
     - `new_metadata["native_messages_integrity"] = self._compute_native_integrity(new_messages)`.
   - Return `Session(session_id=S.session_id, messages=new_messages, metadata=new_metadata)` (or use a new session_id for `fork_session` if requested).

This algorithm:
- Starts from the user’s choice about which **core messages** to keep.
- Derives a native slice via forward mapping, then prunes any native indices that belong to removed core messages via reverse mapping.
- Rebuilds the full core message sequence from the adjusted native history, so the final session is self-consistent.
- Naturally handles special linking patterns (including chains and overlapping groups), often causing entire connected chunks of native history to be removed when any part of them is removed.

---

**7. Fallback & Compatibility Behavior**

We need clear fallbacks when native history cannot be safely preserved:

- Cases when **fallback** is triggered:
  - `config` is `None`.
  - `session.metadata["native_messages"]` is missing or not a list.
  - Integrity verification fails (`_verify_native_integrity` raises).
  - Any kept message uses native indices but has invalid/non-integer `native_indices`.
  - Any `native_indices` value is out of bounds for `native_messages`.

- Fallback behavior:
  - Return a new session with:
    - `messages` sliced purely at the core level (based on `start`/`end`/`remove_indices`).
    - Session metadata copied from original, but with:
      - `native_messages` removed.
      - `native_messages_integrity` removed.
  - Also strip `native_indices` from per-message metadata of the new session to avoid stale mappings.

- Next request after fallback:
  - `_pre_request` sees no `native_messages`, so it reconstructs native history from core messages via the `to_native_messages` pipeline.
  - Round-tripping provider-native details may be lossy, but behavior remains correct and predictable.

- Multiple providers:
  - Because preserving native history across unknown providers is ambiguous, we treat multi-provider setups conservatively:
    - If `len(self._providers) != 1`, slice/remove should default to the fallback behavior (drop native history), even if `native_messages` is present.
    - Document that **native-preserving** slice/remove requires a single provider.

---

**8. Internal Helpers Summary**

To avoid duplication and make the implementation maintainable, we rely on internal helpers:

- `_normalize_final_core_with_native_indices(final_core, finals_native, baseline_offset)`
  - Used in:
    - `send_request`.
    - `send_request_stream` / `send_request_stream_async`.
    - `slice_session` reconstruction.

- `_append_single_message_with_native(session, message_dict, config)`
  - Used only in `add_message` when:
    - Exactly one provider is registered.
    - `native_messages` is present and valid.

- (Optional) `_rebuild_core_from_native(new_native, config)`
  - Encapsulates the reconstruction logic from steps 7–8 so it can be unit-tested in isolation.

---

**9. Plugin & Docs Updates**

To make this robust, we need corresponding updates:

- **Provider plugins**:
  - Document that if `from_native_messages` collapses or expands `native_messages` (different length), it must attach `metadata["native_indices"]` for each core message.
  - Recommended pattern:
    - Treat indices as local to the finals list passed in (the same list used by extensions and features in the from-native pipeline).
    - For simple cases where there is 1:1 mapping, nothing extra is required; Core will infer `[i]`.

- **Extensions & features**:
  - If an extension/feature’s `from_native_messages` changes cardinality, it must also populate `metadata["native_indices"]` according to the same rule.
  - Extensions/features that leave cardinality unchanged can rely on:
    - Provider-level `native_indices` (if provided), or
    - The core’s default mapping when `len(messages) == len(native_messages)`.

- **SDK docs**:
  - Update `docs/plugins/development.md` to describe:
    - The `metadata["native_indices"]` convention.
    - Cardinality rules & Core’s error behavior when they are violated.
    - The fact that slicing/removal uses a forward+reverse mapping algorithm over the core↔native graph.
  - Update `TYPES_AND_PROTOCOLS.md` “Session Metadata Retention” to mention the mapping and the behavior of slice/remove.

---

**10. Tests to Add**

Add tests under `core/python/tests` to validate both happy paths and fallbacks.

- **test_slice_drops_native_without_indices**:
  - Build a session with a dummy provider that doesn’t set `native_indices`.
  - Call `slice_session(session, config=None, remove_indices=[...])`.
  - Assert:
    - `new_session.metadata` has no `native_messages` and no `native_messages_integrity`.
    - Per-message metadata in `new_session` has no `native_indices`.
    - Core can still `add_message` and `send_request` on the sliced session.

- **test_slice_preserves_native_with_indices_single_turn**:
  - Build a custom provider that:
    - Returns 1:1 finals and sets `metadata["native_indices"] = [i]` explicitly.
  - After one turn, call `slice_session(session, config, start=0, end=k)` to fork at a point.
  - Assert:
    - `native_messages` has been truncated appropriately by the forward+reverse algorithm.
    - Reconstructed messages are consistent with the truncated native history.
    - Per-message `native_indices` are contiguous and match the new native list.
    - Integrity passes and the next `send_request` uses retained native history.

- **test_slice_forward_reverse_mapping_on_chain**:
  - Construct a mapping like `msg0 -> [0,1]`, `msg1 -> [1,2]`, `msg2 -> [2,3]` via a custom provider.
  - Remove one of the core messages using `slice_session(session, config, remove_indices=[...])`.
  - Assert:
    - Any native indices referenced by removed messages are excluded from `new_native`.
    - No native index remains that is referenced by both a kept and a removed core message.
    - Reconstructed core history reflects the reduced native history (possibly fewer or no messages in that connected component).

- **test_slice_with_cardinality_mismatch_requires_indices**:
  - Provider `from_native_messages` merges two native messages into one core message but does **not** set `native_indices`.
  - `send_request` should raise due to the new cardinality+no-indices check when building finals.

- **test_fork_session_convenience** (if added):
  - Ensure `fork_session(session, config, upto_index=n)` produces the same result as `slice_session(session, config, start=0, end=n+1)`.

- **test_add_message_config_aware_suffix_native**:
  - Use a provider and feature that mark native messages when `to_native_messages` is called.
  - Call `add_message` with and without `config` on a session that retains native history.
  - Assert:
    - With `config`, the new native suffix and `native_indices` reflect the configured provider + features.
    - Without `config`, behavior falls back to the legacy path and either leaves native history untouched or does not set `native_indices`.

---

**11. How This Supports Your Use-Cases**

- **Delete a specific message**:
  - Application calls `core.slice_session(session, config, remove_indices=[idx])`.
  - Core:
    - Computes `K` (kept core indices) from `start`/`end`/`remove_indices`.
    - Uses forward mapping to get candidate native slice `N0` from `K`.
    - Uses reverse mapping to drop any native index shared with removed messages.
    - Rebuilds the full core history from `new_native` and recomputes integrity.
  - Result: the targeted message is removed; any native segments shared with removed messages are also removed, and remaining native history is consistent with the kept messages.

- **Fork at a specific point**:
  - Application calls `core.fork_session(session, config, upto_index=fork_idx)` (or `slice_session(session, config, start=0, end=fork_idx + 1)`).
  - Core:
    - Identifies which core indices form the prefix, then derives `N0` from them and prunes `N` using reverse mapping.
    - Drops any native entries that are shared with messages outside the prefix.
    - Rebuilds core messages from this truncated native history.
    - Recomputes `native_indices` and `native_messages_integrity` for the new session.
  - Result: a new session that represents a clean fork of conversation history at the specified point, with native history preserved exactly where it remains consistent with the fork.

This updated plan replaces equal-set grouping with a robust **forward+reverse mapping** algorithm over the core↔native graph, keeps config-aware `slice_session`/`add_message`, and always reconstructs the core message list from the adjusted native history to maintain integrity.