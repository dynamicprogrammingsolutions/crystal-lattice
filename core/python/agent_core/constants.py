"""
Shared constants for the core SDK.

"""

from typing import Final


class UIConfigKeys:
    """Config key names that control whether plugin UI elements are shown.

    Plugins use these in get_ui_elements_for_config(config). Session overrides
    (session.metadata["overrides"]) and base agent config may set them;
    effective config is passed to the core when building the UI schema.

    When present in effective config, plugins may hide or show their UI
    elements accordingly. All keys are optional; absence means "use plugin
    default" (typically show).

    Example (plugin):
        from agent_core.constants import UIConfigKeys
        if config.get(UIConfigKeys.SHOW_USAGE) is False:
            return []

    Example (session override):
        PATCH /sessions/{id}/overrides with {"key": "show_usage", "value": false}
    """

    # Usage / cost display (e.g. openrouter_usage extension)
    # When False: hide message_footer and status_bar elements for usage/cost.
    SHOW_USAGE: Final[str] = "show_usage"

    # Verbosity control visibility (e.g. openrouter_verbosity extension)
    # When False: hide the verbosity select from session config UI.
    SHOW_VERBOSITY_UI: Final[str] = "show_verbosity_ui"

    # Reasoning (e.g. openrouter_reasoning extension)
    # When False: show only "Enable Reasoning" checkbox; hide effort dropdown.
    # When True or absent: show checkbox and reasoning effort select.
    ENABLE_REASONING: Final[str] = "enable_reasoning"
