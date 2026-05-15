from __future__ import annotations

"""Gemini-style compaction feature plugin.

This plugin provides manual context compaction using Gemini's structured XML
<state_snapshot> prompt format. It operates at the core level, using layered
context to access LLM capabilities.

Configuration is agent-level with explicit enablement control. The plugin is
only active when the agent's compaction config has:
- enabled: true
- type: "gemini"

This plugin coexists with GeminiCompactionAppPlugin. The AppPlugin is simpler
to use and provides session persistence out of the box. This FeaturePlugin
is useful when:
- Operating at the native-message level
- Provider-specific optimizations are needed
- Integration with core-level workflows is desired

Dependencies:
    This package depends on gemini-compaction-app for shared prompts and helpers.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from agent_core import Message

# Import shared prompts and helpers from the app plugin
from gemini_compaction_app import (
    _GEMINI_COMPRESSION_PROMPT,
    _VERIFICATION_PROMPT,
    _ACKNOWLEDGMENT_MESSAGE,
    _normalize_slice_bounds,
)


# Re-export the prompts for convenience
COMPRESSION_PROMPT = _GEMINI_COMPRESSION_PROMPT
VERIFICATION_PROMPT = _VERIFICATION_PROMPT
ACKNOWLEDGMENT_MESSAGE = _ACKNOWLEDGMENT_MESSAGE


def _collect_final_messages_from_stream(
    core: Any,
    session: Any,
    config: Dict[str, Any],
    *,
    request_id: str | None = None,
) -> List[Dict[str, Any]]:
    """Run an internal request via the streaming path and return final messages."""

    final_messages: List[Dict[str, Any]] = []
    for event in core.send_request_stream(session, config, request_id=request_id):
        if event.get("type") != "final":
            continue
        raw_messages = event.get("messages")
        if isinstance(raw_messages, list):
            final_messages = raw_messages
    return final_messages


class GeminiCompactionFeaturePlugin:
    """Feature-level plugin implementing Gemini-style context compaction.

    This plugin operates at the core level, using the layered context approach:
    - Layer 1 (core): Uses `context["core"]` for session/message operations
    - Layer 2 (app): Optionally uses `context.get("app")` for enhanced features

    Configuration is read from the agent config under the ``compaction`` key:

    ```yaml
    compaction:
      enabled: false          # Must be true to enable
      type: null              # Must be "gemini" for this plugin
      agent_id: null          # Optional dedicated summarizer agent (requires app)
      prompt: null            # Custom prompt override
      settings_overrides: {}  # Model/params for compaction requests
      verification_pass: true # Enable verification pass
    ```

    The plugin is only active when both ``enabled`` is true and ``type`` is
    ``"gemini"``.
    """

    name = "gemini_compaction_feature"
    version = "1.0.0"
    priority = 100

    # Constants for type checking
    COMPACTION_TYPE = "gemini"

    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # FeaturePlugin protocol methods
    # ------------------------------------------------------------------

    def get_config_schema(self) -> Dict[str, Any]:
        """Return empty schema - config is read from agent config, not application config."""
        return {}

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize with application config and shared provider state."""
        return state

    def get_models(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Pass through models unchanged."""
        return list(models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """No tags contributed."""
        return []

    def required_tags(self) -> List[str]:
        """No tags required."""
        return []

    def forbidden_tags(self) -> List[str]:
        """No tags forbidden."""
        return []

    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Pass through native messages unchanged."""
        return list(native_messages)

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Pass through core messages unchanged."""
        return list(messages)

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> tuple[list[Dict[str, Any]], Dict[str, Any]]:
        """No initialization needed."""
        return native_messages, state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]], Dict[str, Any]]:
        """No finalization needed."""
        return final_messages, native_messages, state

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return action definitions for compaction."""
        return [
            {
                "id": "compact_range",
                "label": "Compact range",
                "description": (
                    "Compact a contiguous range of messages into a Gemini-style "
                    "state snapshot."
                ),
                "inputs": {
                    "start": {"type": "integer", "required": False},
                    "end": {"type": "integer", "required": False},
                    "end_inclusive": {"type": "boolean", "required": False, "default": False},
                    "instructions": {"type": "string", "required": False},
                },
            }
        ]

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Return UI schema elements for the compaction actions.

        When config is provided, filter based on compaction.enabled and compaction.type.
        When config is None (global endpoint), return elements unconditionally.

        This mirrors the AppPlugin's UI element behavior, allowing the feature plugin
        to expose UI elements that can be rendered by the application layer.
        """
        # If config is provided, filter based on enablement
        if config is not None and not self._is_compaction_enabled(config):
            return []

        return [
            # Session action: Compact range
            {
                "ui_type": "session_action",
                "id": "compact_range",
                "label": "Compact range",
                "icon": "archive",
                "order": 45,
                "action_id": "compact_range",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "start": "$dialog.start",
                    "end": "$dialog.end",
                    "instructions": "$dialog.instructions",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Compact range",
                    "message": (
                        "Python-style range (start:end). The selected messages "
                        "will be compacted into a structured state snapshot."
                    ),
                    "inputs": [
                        {
                            "name": "start",
                            "type": "integer",
                            "label": "Start index",
                            "required": False,
                            "placeholder": "e.g. 0 or -10 (leave blank for start)",
                        },
                        {
                            "name": "end",
                            "type": "integer",
                            "label": "End index",
                            "required": False,
                            "placeholder": "e.g. 10 or -1 (leave blank for end)",
                        },
                        {
                            "name": "instructions",
                            "type": "multiline",
                            "label": "Instructions",
                            "required": False,
                            "placeholder": "Optional focus instructions for compaction",
                        },
                    ],
                },
            },
            # Message action: Compact up to here
            {
                "ui_type": "message_action",
                "id": "compact_up_to_here",
                "label": "Compact messages up to here",
                "icon": "archive",
                "order": 25,
                "action_id": "compact_range",
                "fixed_params": {"start": 0, "end_inclusive": True},
                "param_map": {
                    "session_id": "$session.session_id",
                    "end": "$message.index",
                    "instructions": "$dialog.instructions",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Compact messages up to here",
                    "message": (
                        "The messages up to here will be compacted into a "
                        "structured state snapshot."
                    ),
                    "inputs": [
                        {
                            "name": "instructions",
                            "type": "multiline",
                            "label": "Instructions",
                            "required": False,
                            "placeholder": "Optional focus instructions for compaction",
                        },
                    ],
                },
            },
            # Session action: Compact full history
            {
                "ui_type": "session_action",
                "id": "compact_full",
                "label": "Compact full history",
                "icon": "archive",
                "order": 46,
                "action_id": "compact_range",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "instructions": "$dialog.instructions",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Compact full history",
                    "message": (
                        "The entire conversation history will be compacted "
                        "into a structured state snapshot."
                    ),
                    "inputs": [
                        {
                            "name": "instructions",
                            "type": "multiline",
                            "label": "Instructions",
                            "required": False,
                            "placeholder": "Optional focus instructions for compaction",
                        },
                    ],
                },
            },
        ]

    def execute_action(
        self,
        action_id: str,
        session: Any,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a compaction action.

        Args:
            action_id: The action to execute.
            session: The current Session object.
            native_messages: Provider-native message history.
            params: Action parameters (start, end, instructions, etc.).
            context: Layered context with core, config, and optionally app.
            state: Plugin state.

        Returns:
            Dict with native_messages, session_metadata, and optional error.
        """
        if action_id != "compact_range":
            return {
                "native_messages": native_messages,
                "error": {"type": "unknown_action", "message": f"Unknown action: {action_id}"},
            }

        # Validate context
        if not isinstance(context, dict):
            return {
                "native_messages": native_messages,
                "error": {"type": "invalid_context", "message": "Context is required"},
            }

        core = context.get("core")
        config = context.get("config", {})

        if core is None:
            return {
                "native_messages": native_messages,
                "error": {"type": "missing_core", "message": "Context must include 'core'"},
            }

        # Get base_config (may be same as config if no app layer)
        base_config = context.get("base_config", config)

        # Check enablement
        if not self._is_compaction_enabled(base_config):
            return {
                "native_messages": native_messages,
                "error": {"type": "disabled", "message": "Gemini compaction is not enabled for this agent."},
            }

        # Get compaction config
        compaction_cfg = self._get_compaction_config(base_config)

        # Parse parameters
        start_raw = params.get("start")
        end_raw = params.get("end")
        instructions = params.get("instructions")
        end_inclusive = params.get("end_inclusive", False)
        start_int = start_raw if isinstance(start_raw, int) else None
        end_int = end_raw if isinstance(end_raw, int) else None
        instructions_str = (
            instructions.strip() if isinstance(instructions, str) else None
        )

        # Get app if available (for agent switching and enhanced features)
        app = context.get("app")

        # Execute compaction
        return self._do_compact_range(
            core=core,
            session=session,
            native_messages=native_messages,
            config=config,
            base_config=base_config,
            compaction_cfg=compaction_cfg,
            start=start_int,
            end=end_int,
            end_inclusive=end_inclusive,
            end_raw=end_raw,
            instructions=instructions_str,
            app=app,
        )

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def _is_compaction_enabled(self, base_config: Dict[str, Any]) -> bool:
        """Check if Gemini compaction is enabled for this agent.

        Returns True only if:
        - compaction.enabled is True
        - compaction.type is "gemini"

        Note: base_config is a flattened config from build_agent_config(),
        so compaction config is at the root level, not nested under 'agent'.
        """
        compaction_cfg = base_config.get("compaction") or {}

        if not isinstance(compaction_cfg, dict):
            return False

        enabled = compaction_cfg.get("enabled", False)
        compaction_type = compaction_cfg.get("type")

        return enabled is True and compaction_type == self.COMPACTION_TYPE

    def _get_compaction_config(
        self,
        base_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract compaction settings from agent base config.

        Returns defaults for any missing keys.

        Note: base_config is a flattened config from build_agent_config(),
        so compaction config is at the root level, not nested under 'agent'.
        """
        compaction_cfg = base_config.get("compaction") or {}

        if not isinstance(compaction_cfg, dict):
            compaction_cfg = {}

        # Extract values with defaults
        agent_id_val = compaction_cfg.get("agent_id")
        prompt_val = compaction_cfg.get("prompt")
        overrides_val = compaction_cfg.get("settings_overrides")
        verification_val = compaction_cfg.get("verification_pass")

        # Use custom prompt if provided, otherwise use Gemini default
        if isinstance(prompt_val, str) and prompt_val.strip():
            prompt = prompt_val.strip()
        else:
            prompt = _GEMINI_COMPRESSION_PROMPT

        agent_id: Optional[str]
        if isinstance(agent_id_val, str) and agent_id_val.strip():
            agent_id = agent_id_val.strip()
        else:
            agent_id = None

        settings_overrides: Dict[str, Any]
        if isinstance(overrides_val, dict):
            settings_overrides = dict(overrides_val)
        else:
            settings_overrides = {}

        # Default to True if not explicitly set
        verification_pass = True
        if isinstance(verification_val, bool):
            verification_pass = verification_val
        elif verification_val is not None:
            verification_pass = bool(verification_val)

        return {
            "enabled": compaction_cfg.get("enabled", False),
            "type": compaction_cfg.get("type"),
            "agent_id": agent_id,
            "prompt": prompt,
            "settings_overrides": settings_overrides,
            "verification_pass": verification_pass,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_compaction_user_message(
        self,
        instructions: Optional[str],
        anchor_instruction: str,
    ) -> str:
        """Build the user message that triggers compaction.

        Args:
            instructions: Optional custom instructions for compaction focus.
            anchor_instruction: The anchor instruction based on whether a previous
                <state_snapshot> exists in the history.

        Returns:
            The complete user message for compaction.
        """
        parts = []
        if instructions and instructions.strip():
            parts.append(instructions.strip())
            parts.append("")
        parts.append(anchor_instruction)
        parts.append("")
        parts.append(
            "First, reason in your scratchpad. Then, generate the updated <state_snapshot>."
        )
        return "\n".join(parts)

    def _build_anchor_instruction(self, has_previous_snapshot: bool) -> str:
        """Build the anchor instruction based on previous snapshot presence.

        Gemini CLI uses different anchor instructions depending on whether
        the history already contains a <state_snapshot> from a previous compaction.

        Args:
            has_previous_snapshot: Whether the history contains a previous snapshot.

        Returns:
            The appropriate anchor instruction string.
        """
        if has_previous_snapshot:
            return (
                "A previous <state_snapshot> exists in the history. "
                "You MUST integrate all still-relevant information from that snapshot into the new one, "
                "updating it with the more recent events. "
                "Do not lose established constraints or critical knowledge."
            )
        else:
            return "Generate a new <state_snapshot> based on the provided history."

    def _has_previous_snapshot(self, messages: List[Any]) -> bool:
        """Check if messages contain a previous <state_snapshot>.

        Args:
            messages: List of message objects with a 'content' attribute or dict.

        Returns:
            True if any message contains <state_snapshot>, False otherwise.
        """
        for msg in messages:
            content = getattr(msg, "content", None)
            if isinstance(content, str) and "<state_snapshot>" in content:
                return True
        return False

    def _extract_snapshot_from_response(
        self,
        messages: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Extract the <state_snapshot> content from assistant response."""
        for msg in reversed(messages):
            if not isinstance(msg, dict):
                continue
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                # Check for <state_snapshot> tag
                if "<state_snapshot>" in content:
                    return content.strip()
                # Return any non-empty assistant content
                return content.strip()
        return None

    def _clone_message_without_native_indices(self, message: Message) -> Message:
        data = message.to_dict()
        md = data.get("metadata") or {}
        if not isinstance(md, dict):
            md = {}
        md.pop("native_indices", None)
        role = data.get("role", "user")
        content = data.get("content", "")
        if md:
            return Message(role=role, content=content, metadata=md)
        return Message(role=role, content=content, metadata=None)

    def _do_compact_range(
        self,
        core: Any,
        session: Any,
        native_messages: List[Dict[str, Any]],
        config: Dict[str, Any],
        base_config: Dict[str, Any],
        compaction_cfg: Dict[str, Any],
        start: Optional[int],
        end: Optional[int],
        end_inclusive: bool,
        end_raw: Any,
        instructions: Optional[str],
        app: Optional[Any],
    ) -> Dict[str, Any]:
        """Execute the compaction range action.

        This method:
        1. Calculates the range to compact
        2. Creates a temporary session for the compaction request
        3. Calls the LLM to generate a state snapshot
        4. Optionally verifies the snapshot
        5. Returns the modified native_messages
        """
        message_count = len(session.messages)

        try:
            start_idx, end_idx = _normalize_slice_bounds(message_count, start, end)
        except ValueError:
            return {
                "native_messages": native_messages,
                "error": {"type": "invalid_range", "message": "Range selects no messages."},
            }

        # Handle inclusive end semantics for "compact up to here"
        if end_inclusive and end_raw is not None:
            end_idx = min(end_idx + 1, message_count)

        # Preserve leading system messages
        system_prefix_end = 0
        for msg in session.messages:
            if msg.role == "system":
                system_prefix_end += 1
            else:
                break

        # Preserve last user message if at end (might be in-progress)
        if end_idx == message_count and message_count > 0:
            last_msg = session.messages[-1]
            if last_msg.role == "user":
                end_idx = message_count - 1

        # Adjust start to skip system prefix
        if start_idx < system_prefix_end:
            start_idx = system_prefix_end

        # Build indices to remove
        remove_indices = list(range(start_idx, end_idx))

        if not remove_indices:
            return {
                "native_messages": native_messages,
                "status": "noop",
                "message": "No messages to compact.",
            }

        # Determine compaction agent and core
        agent_id_cfg = compaction_cfg.get("agent_id")
        session_agent_id = session.metadata.get("agent_id") if isinstance(session.metadata, dict) else None

        if isinstance(agent_id_cfg, str) and agent_id_cfg.strip() and app is not None:
            # Use different agent via app
            target_agent_id = agent_id_cfg.strip()
            if target_agent_id != session_agent_id:
                # Need to switch agent - requires app context
                (
                    core_compact,
                    base_config_compact,
                    session_for_compact,
                ) = app.update_agent(target_agent_id, session)
            else:
                core_compact = core
                base_config_compact = base_config
                session_for_compact = session
        else:
            core_compact = core
            base_config_compact = base_config
            session_for_compact = session

        # Build config for operations
        settings_overrides = compaction_cfg.get("settings_overrides") or {}
        combined_overrides = {**settings_overrides}
        request_overrides = {
            "disable_all_tools": True,
            **combined_overrides,
        }

        # Use core's slice_session to get messages for compaction
        # IMPORTANT: Use start/end to KEEP messages in the range, not remove_indices
        # which would REMOVE them. We need the messages TO BE COMPACTED in the session.
        from agent_app.config import resolve_request_config
        slice_config = resolve_request_config(base_config_compact, request_overrides)

        sliced_session = core_compact.slice_session(
            session_for_compact,
            slice_config,
            start=start_idx,
            end=end_idx,
        )

        # Inject compression prompt as system message
        compression_prompt = compaction_cfg.get("prompt") or _GEMINI_COMPRESSION_PROMPT
        # Check for previous snapshot BEFORE adding compression prompt.
        # The compression prompt template contains '<state_snapshot>' which would
        # incorrectly trigger the detection if we checked after adding it.
        has_previous_snapshot = self._has_previous_snapshot(sliced_session.messages)
        anchor_instruction = self._build_anchor_instruction(has_previous_snapshot)

        session_with_system = core_compact.add_message(
            sliced_session,
            "system",
            compression_prompt,
            metadata={"source": "compaction"},
            config=slice_config,
        )

        # Build compaction instruction
        compaction_instruction = self._build_compaction_user_message(
            instructions,
            anchor_instruction,
        )
        session_with_prompt = core_compact.add_message(
            session_with_system,
            "user",
            compaction_instruction,
            metadata=None,
            config=slice_config,
        )

        # Run compaction request using core.send_request
        try:
            final_messages = _collect_final_messages_from_stream(
                core_compact,
                session_with_prompt,
                slice_config,
            )
        except Exception as exc:
            return {
                "native_messages": native_messages,
                "error": {
                    "type": "compaction_failed",
                    "message": f"Compaction request failed: {exc}",
                },
            }

        # Extract initial snapshot
        initial_snapshot = None
        if final_messages:
            initial_snapshot = self._extract_snapshot_from_response(final_messages)

        if not initial_snapshot:
            return {
                "native_messages": native_messages,
                "error": {
                    "type": "compaction_failed",
                    "message": "Compaction failed (no <state_snapshot> in assistant reply).",
                },
            }

        # Optional verification pass
        final_snapshot = initial_snapshot
        verification_pass = compaction_cfg.get("verification_pass", True)

        if verification_pass:
            # Build verification session (no compaction instruction)
            session_for_verify = core_compact.add_message(
                session_with_system,  # No compaction instruction
                "assistant",
                initial_snapshot,
                metadata=None,
                config=slice_config,
            )
            session_for_verify = core_compact.add_message(
                session_for_verify,
                "user",
                _VERIFICATION_PROMPT,
                metadata=None,
                config=slice_config,
            )

            try:
                verify_final_messages = _collect_final_messages_from_stream(
                    core_compact,
                    session_for_verify,
                    slice_config,
                )
            except Exception:
                verify_final_messages = None

            if verify_final_messages:
                verified_snapshot = self._extract_snapshot_from_response(
                    verify_final_messages
                )
                if verified_snapshot:
                    final_snapshot = verified_snapshot

        # Rebuild the native_messages with the snapshot injected
        # The result should have:
        # - System messages [0:system_prefix_end)
        # - Snapshot user message
        # - Acknowledgment assistant message
        # - Tail messages [end_idx:message_count)

        # Build the new native_messages:
        new_native_messages: List[Dict[str, Any]] = []

        # Add messages before compaction range (including system prefix)
        for i in range(0, start_idx):
            if i < len(native_messages):
                new_native_messages.append(native_messages[i])

        # Add snapshot user message
        snapshot_metadata: Dict[str, Any] = {
            "compacted_range": {
                "start_index": start_idx,
                "end_index": end_idx,
                "verification_pass": verification_pass,
            }
        }
        new_native_messages.append({
            "role": "user",
            "content": final_snapshot,
            "metadata": snapshot_metadata,
        })

        # Add acknowledgment assistant message
        new_native_messages.append({
            "role": "assistant",
            "content": _ACKNOWLEDGMENT_MESSAGE,
            "metadata": None,
        })

        # Add tail messages
        for i in range(end_idx, message_count):
            if i < len(native_messages):
                new_native_messages.append(native_messages[i])

        # Build debug info
        compacted_messages_debug = [
            {
                "index": i,
                "role": session.messages[i].role if i < len(session.messages) else "unknown",
                "content_preview": (
                    session.messages[i].content[:100]
                    if i < len(session.messages) and len(session.messages[i].content) > 100
                    else session.messages[i].content if i < len(session.messages) else ""
                ),
            }
            for i in remove_indices
        ]
        preserved_tail_debug = [
            {
                "index": i,
                "role": session.messages[i].role if i < len(session.messages) else "unknown",
                "content_preview": (
                    session.messages[i].content[:100]
                    if i < len(session.messages) and len(session.messages[i].content) > 100
                    else session.messages[i].content if i < len(session.messages) else ""
                ),
            }
            for i in range(end_idx, message_count)
            if i < len(session.messages)
        ]

        return {
            "native_messages": new_native_messages,
            "session_metadata": {
                "last_compaction": datetime.now().isoformat(),
            },
            "compaction_result": {
                "status": "ok",
                "message": f"Compacted messages [{start_idx}:{end_idx}] into a state snapshot.",
                "verification_pass": verification_pass,
                "original_message_count": message_count,
                "start_idx": start_idx,
                "end_idx": end_idx,
                "remove_indices": remove_indices,
                "compacted_messages": compacted_messages_debug,
                "preserved_tail": preserved_tail_debug,
            },
        }


__all__ = [
    "GeminiCompactionFeaturePlugin",
    "COMPRESSION_PROMPT",
    "VERIFICATION_PROMPT",
    "ACKNOWLEDGMENT_MESSAGE",
]