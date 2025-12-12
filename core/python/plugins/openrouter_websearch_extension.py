"""OpenRouter web search extension.

Enables OpenRouter's built-in web search plugin and extracts URL
citations from responses into message metadata.

Responsibilities:

- Add the OpenRouter ``web`` plugin configuration to the request
  payload when enabled.
- Accumulate ``url_citation`` annotations from streaming chunks.
- Surface URL citations on core messages via ``metadata.url_citations``.

The provider-native annotation shape (simplified) is::

    {
      "message": {
        "role": "assistant",
        "content": "Here's the latest news I found: ...",
        "annotations": [
          {
            "type": "url_citation",
            "url_citation": {
              "url": "https://example.com/",
              "title": "Example",
              "content": "Snippet, when available",
              "start_index": 100,
              "end_index": 140,
            },
          },
        ],
      }
    }

This extension treats annotations as provider-native data and exposes
them in a normalized form under ``metadata.url_citations`` so that UIs
can render citation lists or footnotes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


class OpenRouterWebSearchExtension(ProviderExtensionPlugin):
    """Provider extension to enable OpenRouter web search.

    When enabled, this extension:

    - Adds a ``plugins`` entry to the OpenRouter request payload with
      ``{"id": "web", "engine": "native"}`` (configurable).
    - Accumulates ``url_citation`` annotations from streaming deltas in
      provider-native chunks.
    - Attaches normalized citation metadata to core messages via
      ``metadata.url_citations``.
    """

    name: str = "openrouter_websearch"
    version: str = "0.1.0"

    # ---- Config / UI ----
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enable_web_search": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Enable OpenRouter web search plugin.",
            },
            "web_search_plugin_id": {
                "type": "string",
                "required": False,
                "default": "web",
                "description": "OpenRouter plugin id for web search.",
            },
            "web_search_engine": {
                "type": "string",
                "required": False,
                "default": "native",
                "description": "Engine name for OpenRouter web search.",
            },
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "enable_web_search",
                "label": "Enable Web Search (OpenRouter)",
            }
        ]

    # Uses adapter default get_models (no-op on models)

    def get_tags(
        self,
        config: Dict[str, Any],
        models: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify this extension for dependency resolution."""

        return ["ext:openrouter_websearch"]

    def required_tags(self) -> List[str]:
        """Require the OpenRouter provider."""

        return ["openrouter"]

    # ---- Init / state ----
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        enabled = config.get("enable_web_search")
        # Default is enabled unless explicitly set to False.
        if enabled is False:
            return state

        plugin_id = config.get("web_search_plugin_id") or "web"
        engine = config.get("web_search_engine") or "native"
        return {
            **state,
            "openrouter_websearch": {
                "enabled": True,
                "plugin_id": str(plugin_id),
                "engine": str(engine),
            },
        }

    # ---- Stateless transforms ----
    def to_native_messages(
        self, messages: List[Dict[str, Any]], native_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Leave provider-native messages unchanged.

        Web search annotations are provider-native metadata that are
        extracted during streaming/finalization only and should not be
        written back into new provider-native requests.
        """

        return native_messages

    def from_native_messages(
        self, native_messages: List[Dict[str, Any]], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Surface URL citations from provider-native messages.

        For each core message, if the corresponding provider-native
        message includes ``annotations`` with ``type == "url_citation"``,
        the extension extracts them and exposes a normalized list under
        ``metadata.url_citations``.
        """

        if len(messages) != len(native_messages):
            return messages

        enhanced: List[Dict[str, Any]] = []
        for msg, native in zip(messages, native_messages):
            metadata = dict(msg.get("metadata") or {})
            citations = self._extract_citations_from_native(native)

            if citations:
                metadata["url_citations"] = citations

            if metadata:
                enhanced.append({**msg, "metadata": metadata})
            else:
                enhanced.append(msg)

        return enhanced

    # ---- Request init ----
    def initialize_request(
        self, native_messages: List[Dict[str, Any]], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Inject OpenRouter web search plugin config into request.

        Adds a ``plugins`` array entry equivalent to::

            {
              "plugins": [
                {"id": "web", "engine": "native"}
              ]
            }

        when web search is enabled.
        """

        cfg = state.get("openrouter_websearch") or {}
        if not cfg.get("enabled"):
            return state

        request = state.get("request") or {}
        payload = dict(request.get("payload", {}))

        plugin_id = cfg.get("plugin_id") or "web"
        engine = cfg.get("engine") or "native"

        plugins_value = payload.get("plugins")
        if isinstance(plugins_value, list):
            plugins: List[Any] = list(plugins_value)
        elif plugins_value is None:
            plugins = []
        else:
            # Non-list value should not break the request; start fresh.
            plugins = []

        entry = {"id": plugin_id, "engine": engine}
        if not any(
            isinstance(p, dict)
            and p.get("id") == entry["id"]
            and p.get("engine") == entry["engine"]
            for p in plugins
        ):
            plugins.append(entry)

        payload["plugins"] = plugins

        return {
            **state,
            "request": {**request, "payload": payload},
        }

    # ---- Streaming helpers ----
    def extract_delta(self, native_chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a provider-native delta dictionary from a streaming chunk.

        Returns the first choice object when present, or an empty dict.
        """

        if "choices" in native_chunk and native_chunk["choices"]:
            return native_chunk["choices"][0]
        return {}

    def process_delta(
        self,
        delta: Dict[str, Any],
        current_partial: Optional[Dict[str, Any]] = None,
        accumulated: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """Accumulate URL citations across streaming deltas.

        Citations are collected into the shared accumulator under the
        ``url_citations`` key. The provider's own partial/final message
        construction remains unchanged.
        """

        acc = accumulated or {}
        base_list: List[Dict[str, Any]] = []
        existing = acc.get("url_citations")
        if isinstance(existing, list):
            base_list = list(existing)

        d = delta.get("message") or delta.get("delta") or {}
        new_items = self._extract_citations_from_native(d)
        if new_items:
            combined = self._merge_citation_lists(base_list, new_items)
            acc = {**acc, "url_citations": combined}

        return current_partial, acc

    def process_chunk(
        self,
        native_chunk: Optional[Dict[str, Any]],
        partial_messages: List[Dict[str, Any]],
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        delta = self.extract_delta(native_chunk or {})
        accumulated = state.get("partial") or {}
        _partial, accumulated = self.process_delta(delta, None, accumulated)

        return (
            partial_messages,
            final_messages,
            native_messages,
            {**state, "partial": accumulated},
        )

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Attach accumulated citations to provider-native finals.

        During streaming, URL citations are accumulated into
        ``state["partial"]["url_citations"]`` from deltas. This
        method attaches those citations as ``annotations`` on the final
        provider-native messages so that :meth:`from_native_messages`
        can surface them into core metadata.
        """

        partial = state.get("partial") or {}
        citations = None
        if isinstance(partial, dict):
            val = partial.get("url_citations")
            if isinstance(val, list) and val:
                citations = list(val)

        if not citations:
            return final_messages, native_messages, state

        annotations = [
            {
                "type": "url_citation",
                "url_citation": {
                    **(
                        {
                            k: v
                            for k, v in item.items()
                            if k
                            in {
                                "url",
                                "title",
                                "content",
                                "start_index",
                                "end_index",
                            }
                        }
                    ),
                },
            }
            for item in citations
            if isinstance(item, dict)
        ]

        def _attach(msg: Any) -> Any:
            if not isinstance(msg, dict):
                return msg
            existing = msg.get("annotations")
            if isinstance(existing, list) and existing:
                merged = self._merge_annotation_lists(existing, annotations)
            else:
                merged = annotations
            return {**msg, "annotations": merged}

        new_finals = [_attach(m) for m in final_messages]

        if native_messages:
            updated_native = list(native_messages)
            updated_native[-1] = _attach(updated_native[-1])
        else:
            updated_native = native_messages

        return new_finals, updated_native, state

    # ---- Internal helpers ----
    def _extract_citations_from_native(self, native: Any) -> List[Dict[str, Any]]:
        """Extract normalized URL citations from a provider-native message.

        The returned list has items with the following keys when
        available: ``url``, ``title``, ``content``, ``start_index``,
        ``end_index``.
        """

        if not isinstance(native, dict):
            return []

        annotations = native.get("annotations")
        if not isinstance(annotations, list) or not annotations:
            return []

        citations: List[Dict[str, Any]] = []
        for ann in annotations:
            if not isinstance(ann, dict):
                continue
            if ann.get("type") != "url_citation":
                continue
            payload = ann.get("url_citation") or {}
            if not isinstance(payload, dict):
                continue

            url = payload.get("url")
            title = payload.get("title")
            content = payload.get("content")
            start_index = payload.get("start_index")
            end_index = payload.get("end_index")

            item: Dict[str, Any] = {}
            if isinstance(url, str) and url:
                item["url"] = url
            if isinstance(title, str) and title:
                item["title"] = title
            if isinstance(content, str) and content:
                item["content"] = content
            if isinstance(start_index, int):
                item["start_index"] = start_index
            if isinstance(end_index, int):
                item["end_index"] = end_index

            if item:
                citations.append(item)

        return citations

    def _merge_citation_lists(
        self,
        existing: List[Dict[str, Any]],
        new_items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge two citation lists, avoiding simple duplicates.

        Duplicates are detected by matching on the ``url`` and
        ``start_index``/``end_index`` pair when present.
        """

        out: List[Dict[str, Any]] = list(existing)

        for item in new_items:
            url = item.get("url")
            start = item.get("start_index")
            end = item.get("end_index")

            if any(
                url
                and url == e.get("url")
                and start == e.get("start_index")
                and end == e.get("end_index")
                for e in out
            ):
                continue
            out.append(item)

        return out

    def _merge_annotation_lists(
        self,
        existing: List[Any],
        new_items: List[Any],
    ) -> List[Any]:
        """Merge annotation objects, avoiding duplicate url_citation entries."""

        out: List[Any] = list(existing)

        def _key(ann: Any) -> Optional[tuple]:
            if not isinstance(ann, dict) or ann.get("type") != "url_citation":
                return None
            payload = ann.get("url_citation") or {}
            if not isinstance(payload, dict):
                return None
            return (
                payload.get("url"),
                payload.get("start_index"),
                payload.get("end_index"),
            )

        existing_keys = {_key(a) for a in out if _key(a) is not None}

        for ann in new_items:
            k = _key(ann)
            if k is not None and k in existing_keys:
                continue
            out.append(ann)

        return out
