"""Configuration for the integration scaffolds in this test suite.

These tests are meant to be copied into a real provider repo.

Defaults keep the suite offline:

- Integration tests are marked with ``@pytest.mark.integration`` and are
  excluded by default via this repo's pytest configuration.
- To run them, pass ``-m integration`` and fill in the settings below.

All integration tests also skip unless the configured API key environment
variable is present.
"""

from __future__ import annotations

from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Provider under test
# ---------------------------------------------------------------------------

# Dotted path to the ProviderPlugin class.
# Example: "my_provider.provider.MyProvider"
PROVIDER_CLASS_PATH: str = ""

# Model identifier to use for integration tests.
MODEL: str = ""

# Name of the environment variable that holds the API key/token.
# Example: "OPENAI_API_KEY"
API_KEY_ENV_VAR: str = ""

# Optional base URL for providers that support it.
BASE_URL: str = ""

# Optional request timeout (seconds).
TIMEOUT: int = 60

# Additional provider-specific config fields.
EXTRA_CONFIG: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Optional plugin components (dotted class paths)
# ---------------------------------------------------------------------------

REASONING_EXTENSION_CLASS_PATH: str = ""
TOOLS_EXTENSION_CLASS_PATH: str = ""
USAGE_EXTENSION_CLASS_PATH: str = ""

# Optional feature plugins to register (e.g. request options/routing features).
FEATURE_CLASS_PATHS: List[str] = []

# Tool plugins to register for tool-calling integration tests.
# Defaults point at the built-in tools shipped with ``agent-core``.
TOOL_CLASS_PATHS: List[str] = [
    "plugins.math_tools.MathTools",
    "plugins.file_reader_tool.FileReaderTool",
    "plugins.file_writer_tool.FileWriterTool",
]
