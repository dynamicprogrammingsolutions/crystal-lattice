"""WebContextFeature plugin.

Provides inline web page content expansion and URL completions.

Two responsibilities:

- During :meth:`initialize_request`, occurrences of ``@web:`` markers in
  user message content are replaced with the fetched page contents,
  formatted according to ``web_context_format``.
- Via :meth:`get_completions`, the plugin suggests previously fetched
  ``https://`` URLs so they can be quickly completed, with shorter URLs
  appearing first.

The URL cache is kept in a module-level dictionary so that URLs fetched
in one request are available for completions in later requests within
the same process. Content is cached per-URL and re-used when the same
URL is referenced again.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from agent_core.types import FeaturePlugin
from agent_core.utils import get_logger


# Global cache of fetched URLs and their formatted contents.
# Shape: {url: {"downloaded": str, "formats": {format: str}}}
_WEB_CACHE: Dict[str, Dict[str, Any]] = {}


def _normalize_format(config: Dict[str, Any]) -> str:
    raw = str(config.get("web_context_format", "markdown") or "markdown").lower()
    if raw not in {"markdown", "html", "text"}:
        return "markdown"
    return raw


def _get_or_fetch_content(url: str, config: Dict[str, Any]) -> str:
    """Return formatted content for *url*, fetching and caching as needed.

    Uses ``trafilatura`` to download and extract the main content of the
    page. Fetched HTML is cached per-URL and reused across calls. The
    ``web_context_format`` key controls the output format:

    - ``"markdown"`` -> trafilatura ``output_format="markdown"``
    - ``"html"``     -> trafilatura ``output_format="xml"``
    - ``"text"``     -> trafilatura ``output_format="txt"``

    ``web_context_max_bytes`` limits the size of the formatted snippet.
    """

    # Local import so that the plugin can still be imported in
    # environments where trafilatura is not installed, even though
    # actual use of the feature requires it.
    import trafilatura  # type: ignore[import-not-found]

    logger = get_logger("web_context_feature")

    fmt = _normalize_format(config)
    max_bytes = int(config.get("web_context_max_bytes", 65536) or 65536)
    if max_bytes <= 0:
        max_bytes = 65536

    entry = _WEB_CACHE.get(url)
    if entry is not None:
        formats = entry.get("formats") or {}
        cached = formats.get(fmt)
        if isinstance(cached, str) and cached:
            return cached
        downloaded = entry.get("downloaded") or ""
    else:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            logger.warning("web_context_fetch_failed", url=url)
            return ""
        entry = {"downloaded": downloaded, "formats": {}}
        _WEB_CACHE[url] = entry

    # Map our config format to trafilatura's output formats.
    if fmt == "markdown":
        output_format = "markdown"
    elif fmt == "html":
        # trafilatura produces HTML-like XML when output_format="xml".
        output_format = "xml"
    else:  # "text"
        output_format = "txt"

    content = trafilatura.extract(downloaded, output_format=output_format) or ""
    if not isinstance(content, str):
        logger.warning("web_context_extract_failed", url=url, format=output_format)
        return ""

    if len(content) > max_bytes:
        content = content[:max_bytes]

    entry.setdefault("formats", {})[fmt] = content
    return content


class WebContextFeature(FeaturePlugin):
    name: str = "web_context"
    version: str = "0.1.0"

    # ---- Config / UI ----
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "web_context_enabled": {
                "type": "boolean",
                "default": True,
                "description": "Enable @web: URL expansion and web completions.",
            },
            "web_context_format": {
                "type": "string",
                "default": "markdown",
                "description": (
                    "Preferred format for fetched web content. One of "
                    "'markdown', 'html', or 'text'."
                ),
            },
            "web_context_timeout_seconds": {
                "type": "number",
                "default": 15.0,
                "description": "Maximum time in seconds to wait when fetching a URL.",
            },
            "web_context_max_bytes": {
                "type": "integer",
                "default": 65536,
                "description": (
                    "Maximum number of characters of formatted web content "
                    "inserted per @web reference."
                ),
            },
            "web_context_template": {
                "type": "string",
                "default": "{url}\n<content>\n{marker}\n</content>",
                "description": (
                    "Template applied when an @web completion is accepted. "
                    "Supports {url} and {marker} (the @web: URL marker) "
                    "placeholders."
                ),
            },
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "web_context_enabled",
                "label": "Enable @web URL expansion",
            },
            {
                "type": "select",
                "key": "web_context_format",
                "label": "Web context format",
                "options": [
                    {"value": "markdown", "label": "Markdown (default)"},
                    {"value": "html", "label": "HTML"},
                    {"value": "text", "label": "Plain text"},
                ],
                "condition": {"web_context_enabled": True},
            },
            {
                "type": "checkbox",
                "key": "web_context_fetch_on_completion",
                "label": "Fetch web content immediately on completion",
                "condition": {"web_context_enabled": True},
            },
        ]

    # Uses adapter default get_models / get_tags / required_tags

    # ---- Templates ----
    def get_template(self, config: Dict[str, Any]) -> str:
        raw = config.get("web_context_template")
        if isinstance(raw, str) and raw:
            return raw
        return "{url}\n<content>\n{marker}\n</content>"

    # ---- Init ----
    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Merge flat config into shared state for use during requests."""

        return {**state, "config": {**state.get("config", {}), **config}}

    # ---- Completion helpers ----
    def get_completions(self, config: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        enabled = bool(config.get("web_context_enabled", True))
        if not enabled:
            return []

        if not isinstance(text, str) or not text:
            return []

        # Case 1: user is typing an @web: reference (with or without a
        # partial URL/scheme) at the end of the buffer.
        web_match = re.search(r"@web:(?P<rest>[^\s]*)$", text)
        if web_match:
            start = web_match.start()
            rest = web_match.group("rest") or ""
            fragment_lower = rest.lower()

            completions: List[Dict[str, Any]] = []
            added_self = False
            added_scheme = False
            added_cached = False

            # Self-entry: full URL with scheme + plausible TLD.
            marker = text[start:]
            if rest and re.match(r"^https?://[^/\s]+\.[A-Za-z]{2,}(?:/.*)?$", rest):
                completions.append(
                    {
                        "replacement": marker,
                        "start": start,
                        # Display the bare URL without the @web: prefix
                        # to keep the menu clean, while still preserving
                        # the full marker for apply_completion.
                        "display": rest,
                        "display_meta": "web",
                        "url": rest,
                        "marker": marker,
                    }
                )
                added_self = True
            elif rest and not rest.startswith(("http://", "https://")) and re.match(
                r"^\S+\.\S+$", rest
            ):
                # Domain-only fragment (e.g. "example.com"): suggest
                # https:// and http:// variants.
                urls = [f"https://{rest}", f"http://{rest}"]
                for http_url in urls:
                    completions.append(
                        {
                            "replacement": f"@web:{http_url}",
                            "start": start,
                            "display": http_url,
                            "display_meta": "web",
                            "url": http_url,
                            "marker": f"@web:{http_url}",
                        }
                    )

            # Base schemes filtered by the typed fragment.
            for scheme in ("http://", "https://"):
                if scheme.lower().startswith(fragment_lower):
                    replacement = f"@web:{scheme}"
                    completions.append(
                        {
                            "replacement": replacement,
                            "start": start,
                            "display": scheme,
                            "display_meta": "web",
                            "url": scheme,
                            "marker": replacement,
                        }
                    )
                    added_scheme = True

            # Cached URLs appear once the user has typed at least one
            # character after @web:. They are filtered by prefix on the
            # full URL string and ordered by length (shortest first).
            if fragment_lower:
                urls = [
                    u
                    for u in _WEB_CACHE.keys()
                    if u.lower().startswith(fragment_lower)
                ]
                ordered = sorted(set(urls), key=len)
                for url in ordered[:30]:
                    replacement = f"@web:{url}"
                    completions.append(
                        {
                            "replacement": replacement,
                            "start": start,
                            "display": url,
                            "display_meta": "web",
                            "url": url,
                            "marker": replacement,
                        }
                    )
                if ordered:
                    added_cached = True

            # If the only match is the self-entry (no schemes or cached
            # URLs matched by prefix), still offer both base schemes so
            # the user can easily switch protocols.
            if added_self and not added_scheme and not added_cached:
                for scheme in ("http://", "https://"):
                    replacement = f"@web:{scheme}"
                    completions.append(
                        {
                            "replacement": replacement,
                            "start": start,
                            "display": scheme,
                            "display_meta": "web",
                            "url": scheme,
                            "marker": replacement,
                        }
                    )

            return completions

        # Case 2: plain http/https URL at the end of the buffer without a
        # @web: prefix. When matched, completions will insert the @web:
        # prefix so the reference becomes expandable.
        match = re.search(r"(?P<url>https?://[^\s]*)$", text)
        if not match:
            return []

        url_fragment = match.group("url") or ""
        if not url_fragment:
            return []

        start = match.start("url")

        fragment_lower = url_fragment.lower()
        urls = [u for u in _WEB_CACHE.keys() if u.lower().startswith(fragment_lower)]
        if not urls:
            return []

        ordered = sorted(set(urls), key=len)

        completions: List[Dict[str, Any]] = []
        for url in ordered[:30]:
            replacement = f"@web:{url}"
            completions.append(
                {
                    "replacement": replacement,
                    "start": start,
                    "display": url,
                    "display_meta": "web",
                    "url": url,
                    "marker": replacement,
                }
            )

        return completions

    # ---- Completion-accept handling ----
    def apply_completion(
        self,
        config: Dict[str, Any],
        text: str,
        completion: Dict[str, Any],
    ) -> str:
        """Turn an accepted @web completion into a template snippet.

        The returned snippet wraps the original @web: URL marker inside
        the configured template. The marker remains in the text so that
        request-time expansion can later replace it with fetched
        content.
        """

        if not isinstance(completion, dict):
            return ""

        url = completion.get("url")
        if not isinstance(url, str) or not url:
            return ""

        marker = completion.get("marker")
        if not isinstance(marker, str) or not marker:
            raw = completion.get("replacement")
            if not isinstance(raw, str) or "@web:" not in raw:
                return ""
            marker = raw

        template = self.get_template(config)

        fetch_now = bool(config.get("web_context_fetch_on_completion"))

        if fetch_now:
            # Fetch and inline content immediately. The snippet should not
            # contain the @web: marker so that request-time expansion does
            # not re-fetch or double-inline content.
            base = _get_or_fetch_content(url, config)
            if not base:
                # Fall back to marker-based snippet so the user still sees
                # something meaningful.
                try:
                    return template.format(url=url, marker=marker, content=marker)
                except Exception:
                    return f"{url}\n<content>\n{marker}\n</content>"
            try:
                # Use the fetched content for both marker and content so
                # that templates relying on either placeholder are
                # populated, while avoiding any @web: marker in the
                # rendered snippet.
                return template.format(url=url, marker=base, content=base)
            except Exception:
                return f"{url}\n<content>\n{base}\n</content>"

        # Default: defer content expansion to initialize_request by
        # keeping the @web: marker in place.
        try:
            return template.format(url=url, marker=marker, content=marker)
        except Exception:
            return f"{url}\n<content>\n{marker}\n</content>"

    # ---- Request-time expansion ----
    def _expand_web_markers(
        self,
        content: str,
        config: Dict[str, Any],
        fetch_cache: Dict[str, str],
    ) -> str:
        """Expand @web markers in a single message content string.

        ``fetch_cache`` is a per-request mapping from URL to already-fetched
        snippet, reset at the start of :meth:`initialize_request`.
        """

        # Allow optional whitespace between the @web: prefix and the URL so
        # that both "@web:https://..." and "@web: https://..." are
        # supported.
        pattern = re.compile(r"@web:\s*(?P<url>https?://[^\s]+)")

        def _repl(match: re.Match[str]) -> str:
            url = match.group("url")
            if not url:
                return match.group(0)
            # Reuse any snippet already fetched for this URL during the
            # current request before falling back to the global cache.
            if url in fetch_cache:
                snippet = fetch_cache[url]
            else:
                snippet = _get_or_fetch_content(url, config)
                if snippet:
                    fetch_cache[url] = snippet
            if not snippet:
                # Preserve marker when fetch fails.
                return match.group(0)
            return snippet

        return pattern.sub(_repl, content)

    def _expand_messages(
        self,
        messages: List[Dict[str, Any]],
        cfg: Dict[str, Any],
        fetch_cache: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        new_messages: List[Dict[str, Any]] = []
        for msg in messages:
            if not isinstance(msg, dict):
                new_messages.append(msg)
                continue
            role = msg.get("role")
            if role != "user":
                new_messages.append(msg)
                continue
            content = msg.get("content")
            if not isinstance(content, str) or "@web:" not in content:
                new_messages.append(msg)
                continue
            expanded = self._expand_web_markers(content, cfg, fetch_cache)
            new_messages.append({**msg, "content": expanded})

        return new_messages

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:

        config_state = state.get("config", {}) or {}
        enabled = bool(config_state.get("web_context_enabled", True))
        if not enabled:
            return native_messages, state

        cfg = config_state

        # Per-request cache mapping URL -> snippet. Reset at the start of
        # each initialize_request call.
        fetch_cache: Dict[str, str] = {}

        # Always expand provider-native messages and return the expanded
        # copy so the native history carries inlined web contents.
        expanded_native = self._expand_messages(native_messages, cfg, fetch_cache)

        request = state.get("request") or {}
        request_messages = request.get("messages")

        new_state = state
        if isinstance(request_messages, list) and request_messages:
            expanded_request_messages = self._expand_messages(
                request_messages, cfg, fetch_cache
            )
            new_request = {**request, "messages": expanded_request_messages}
            new_state = {**state, "request": new_request}

        return expanded_native, new_state

    def finalize(
        self,
        final_messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        # This feature does not modify responses.
        return final_messages, native_messages, state
