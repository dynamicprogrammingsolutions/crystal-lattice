"""
OpenRouter Provider Plugin

Provides access to multiple LLM providers through OpenRouter's unified API.
Compatible with OpenAI Chat Completions API format.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Tuple
import json

import requests

from agent_core.types import ProviderPlugin
from agent_core.utils import get_logger


class OpenRouterProvider(ProviderPlugin):
    name: str = "openrouter"
    version: str = "0.1.0"
    
    # ---------- Schemas ----------
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "model": {"type": "string", "required": True},
            "api_key": {"type": "string", "required": True},
            "base_url": {
                "type": "string",
                "required": False,
                "default": "https://openrouter.ai/api/v1",
            },
            "timeout": {"type": "number", "required": False, "default": 60},
            "site_url": {
                "type": "string",
                "required": False,
                "description": "Optional URL for ranking/tracking",
            },
            "app_name": {
                "type": "string",
                "required": False,
                "description": "Optional application name for identification",
            },
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "config",
                "type": "string",
                "key": "model",
                "label": "Openrouter Model ID",
            },
        ]

    # ---------- Models / capabilities ----------
    def _fetch_models_from_api(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch model data from OpenRouter /models API.
        
        Returns list of model descriptors with id, name, and supported_parameters.
        Returns empty list on error (logs warning).
        """
        base_url = (config.get("base_url") or "https://openrouter.ai/api/v1").rstrip("/")
        models_url = f"{base_url}/models"
        
        try:
            response = requests.get(models_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract models array from response
            models = data.get("data", [])
            if not isinstance(models, list):
                get_logger("openrouter_provider").warning(
                    "Invalid models response format",
                    response=data
                )
                return []
            
            return models
            
        except requests.RequestException as e:
            get_logger("openrouter_provider").warning(
                "Failed to fetch models from OpenRouter API",
                error=str(e),
                url=models_url
            )
            return []
        except Exception as e:
            get_logger("openrouter_provider").warning(
                "Unexpected error fetching models",
                error=str(e)
            )
            return []
    
    def get_models(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return model descriptors from OpenRouter API.
        
        Fetches all models and filters by config.
        Core framework caches results per config.
        """
        all_models = self._fetch_models_from_api(config)
        model_id = config.get("model")
        if not isinstance(model_id, str) or not model_id:
            return []
        
        if all_models:
            matching_models = [m for m in all_models if m.get("id") == model_id]
            if matching_models:
                return matching_models
        
        # Fallback: return minimal model descriptor
        return [{"id": model_id}]

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Return capability tags based on model's supported_parameters.
        
        Checks the model's supported_parameters array from the OpenRouter API:
        - 'reasoning' → 'supports_reasoning'
        - 'verbosity' → 'supports_verbosity'
        - 'tools' → 'supports_tools'
        
        Always includes: provider:openrouter, openrouter, supports_streaming
        Falls back to hardcoded tags if model data unavailable.
        """
        tags: List[str] = ["provider:openrouter", "openrouter"]
        tags.append("supports_streaming")  # All OpenRouter models support streaming
        
        # Check if we have model capability data
        if models and isinstance(models, list) and len(models) > 0:
            model = models[0]
            supported_params = model.get("supported_parameters", [])
            
            if isinstance(supported_params, list) and len(supported_params) > 0:
                # Map supported_parameters to capability tags
                if "tools" in supported_params or "tool" in supported_params:
                    tags.append("supports_tools")
                if "reasoning" in supported_params:
                    tags.append("supports_reasoning")
                if "verbosity" in supported_params:
                    tags.append("supports_verbosity")
                if "reasoning_effort" in supported_params:
                    tags.append("supports_reasoning_effort")
                
                return tags
        
        # Fallback: assume common capabilities (backward compatibility)
        tags.append("supports_tools")
        tags.append("supports_reasoning")
        return tags

    # ---------- State lifecycle ----------
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:

        config = state["config"]

        base_url = (config.get("base_url") or "https://openrouter.ai/api/v1").rstrip("/")
        api_key = config.get("api_key")
        model = config.get("model")
        timeout = float(config.get("timeout", 60))

        url = f"{base_url}/chat/completions"
        payload: Dict[str, Any] = {"model": model}
        headers = {"Content-Type": "application/json"}

        if not api_key:
            raise ValueError("[openrouter_provider] api_key is required")

        headers["Authorization"] = f"Bearer {api_key}"

        # Add OpenRouter-specific headers
        site_url = config.get("site_url")
        if site_url:
            headers["HTTP-Referer"] = site_url

        app_name = config.get("app_name")
        if app_name:
            headers["X-Title"] = app_name

        return native_messages, {
            **state,
            "request": {
                "url": url,
                "payload": payload,
                "headers": headers,
                "timeout": timeout,
            },
            "partial": None,
        }


    # ---------- Message conversion ----------
    def to_native_messages(
        self, messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        return [{"role": m["role"], "content": m.get("content", "")} for m in messages]

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Convert provider-native finals to core messages.

        Reasoning fields are intentionally ignored here; the
        OpenRouterReasoningExtension is responsible for exposing
        reasoning and reasoning_details via message metadata.
        """
        normalized: List[Dict[str, Any]] = []
        for m in native_messages:
            if not isinstance(m, dict):
                continue
            if not ("role" in m or "content" in m):
                continue
            msg = {
                "role": m.get("role", "assistant"),
                "content": m.get("content", ""),
            }
            normalized.append({**msg, "metadata": {}})
        return normalized

    # ---------- Core API calls ----------
    def _validate_message_list(self, history: List[Dict[str, Any]]) -> None:
        """Validate that every item is a message-shaped dict with role and content.
        Other keys are allowed. Raise with details if invalid.
        """
        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                raise RuntimeError(
                    f"[openrouter_provider] invalid message at index {idx}: expected dict, got {type(item).__name__} -> {item}"
                )
            if "role" not in item or "content" not in item:
                raise RuntimeError(
                    f"[openrouter_provider] invalid message at index {idx}: missing 'role' or 'content' -> {json.dumps(item, ensure_ascii=False)}"
                )

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        request = state["request"]
        payload: Dict[str, Any] = {}
        try:
            self._validate_message_list(native_messages)
            override = request.get("messages")
            messages = override if isinstance(override, list) else native_messages
            payload = {**request["payload"], "messages": messages, "stream": False}
            get_logger("openrouter_provider").info(
                "sending request",
                payload=str(payload),
            )
            r = requests.post(
                request["url"],
                json=payload,
                headers=request["headers"],
                timeout=request["timeout"],
            )
            # OpenRouter responses are JSON and should always be UTF-8. Some
            # environments mis-detect the charset (for example defaulting to
            # ISO-8859-1), which corrupts non-ASCII characters like en/em
            # dashes inside tool arguments. Force UTF-8 before JSON parsing
            # so that we never depend on the response headers for encoding.
            r.encoding = "utf-8"
            obj = r.json()
            # Debug log full non-streaming response for investigation
            try:  # pragma: no cover - debug aid
                get_logger("openrouter_provider").info(
                    "received response",
                    response=obj,
                )
            except Exception:
                # Logging must never break the provider
                pass
        except requests.RequestException as e:
            # Debug payload and error details for investigation (no auth headers included)
            try:  # pragma: no cover - debug aid
                debug_payload = json.dumps(payload, ensure_ascii=False)[:2000]
                print("[openrouter_provider] call_api error payload:", debug_payload)
            except Exception:
                print("[openrouter_provider] call_api error payload: <unserializable>")
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    err_detail = resp.json()
                except Exception:
                    err_detail = resp.text
                print("[openrouter_provider] call_api error response:", err_detail)
            raise RuntimeError(f"OpenRouter API call failed: {e}") from e

        message = obj.get("choices", [{}])[0].get("message", {})

        # TODO: Check why this was added here instead of in ClaudeCachingExtension - maybe an agent wasn't able to make a test working without it?
        # Attach cached_tokens from usage.prompt_tokens_details (when present)
        # as provider-native internal metadata on the assistant message. This
        # is later surfaced into core message metadata by provider extensions
        # (for example, ClaudeCachingExtension).
        # try:  # pragma: no cover - defensive, best-effort only
        #     usage = obj.get("usage") or {}
        #     cached_tokens = None
        #     if isinstance(usage, dict):
        #         details = usage.get("prompt_tokens_details") or {}
        #         if isinstance(details, dict) and "cached_tokens" in details:
        #             cached_tokens = details.get("cached_tokens")
        #     if cached_tokens is not None and isinstance(message, dict):
        #         internal_md = dict(message.get("_metadata") or {})
        #         internal_md["cached_tokens"] = cached_tokens
        #         message["_metadata"] = internal_md
        # except Exception:
        #     # Never allow usage-metadata extraction to break the provider.
        #     pass

        return [message], [], [*native_messages, message], state


    def stream_api(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        request = state["request"]
        payload: Dict[str, Any] = {}
        try:
            self._validate_message_list(native_messages)
            override = request.get("messages")
            messages = override if isinstance(override, list) else native_messages
            payload = {**request["payload"], "messages": messages, "stream": True}
            get_logger('openrouter_provider').info("sending request", payload=str(payload))
            with requests.post(
                request["url"],
                json=payload,
                headers=request["headers"],
                timeout=request["timeout"],
                stream=True,
            ) as r:
                # See call_api above: OpenRouter uses UTF-8 JSON for
                # streaming chunks as well. Force UTF-8 so that
                # iter_lines(decode_unicode=True) does not incorrectly
                # decode bytes as ISO-8859-1 and garble characters like
                # em dashes in tool_call.function.arguments.
                r.encoding = "utf-8"
                if r.status_code != 200:
                    # Get error details before raising
                    try:
                        error_detail = r.json()
                    except Exception:
                        error_detail = r.text
                    raise RuntimeError(
                        f"OpenRouter stream failed: {r.status_code} {r.reason}. "
                        f"Error: {error_detail}"
                    )
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    data_str = line
                    if data_str.startswith("data:"):
                        data_str = data_str[len("data:") :].strip()
                    if not data_str or data_str == "[DONE]":
                        if data_str == "[DONE]":
                            break
                        continue
                    try:
                        obj = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    yield obj
        except requests.RequestException as e:
            raise RuntimeError(f"OpenRouter stream failed: {e}") from e


    # ---------- Helpers (default/general implementations) ----------
    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract a provider-native delta dictionary from a streaming chunk.
        Return the first choice if present.
        """
        if "choices" in native_chunk and native_chunk["choices"]:
            return native_chunk["choices"][0]

        return {}

    def process_delta(self, delta: Dict[str, Any], accumulated) -> Tuple[Dict[str, Any],Dict[str, Any]]:
        """
        Reduce a delta dict into a new partial accumulator, and optionally a final.
        Returns (partial_message_or_none, final_message_or_none, new_accumulated).
        """
        content = delta.get("message") or delta.get("delta") or None
        return content, self._merge_delta_content(
            accumulated or {}, content, override=["role"], accumulate=["content"]
        )

    def _merge_delta_content(
        self,
        current: Dict[str, Any],
        delta: Dict[str, Any],
        override: List[str] = [],
        accumulate: List[str] = [],
    ) -> Dict[str, Any]:
        return {
            **current,
            **{key: delta.get(key, current.get(key, "")) for key in override},
            **{key: ((current.get(key) or "") + (delta.get(key) or "")) for key in accumulate},
        }

    def process_chunk(
        self,
        native_chunk: Dict[str, Any],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        #print("chunk:", native_chunk)
        partial, accumulated = self.process_delta(
            delta=self.extract_delta(native_chunk), accumulated=state.get("partial", {})
        )
        new_state = {**state, "partial": accumulated}
        return_values = [partial] if partial else [], [], native_messages, new_state
        return  return_values

    def finalize(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        current_partial = state.get("partial", None)
        finals = [current_partial] if current_partial else []
        full_history = [*native_messages, current_partial] if current_partial else native_messages
        return finals, full_history, state

    def to_display_format(self, message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return message
