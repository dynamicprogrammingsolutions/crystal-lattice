# openai_responses

Plugin bundle scaffold for an OpenAI Responses provider and extension set.

This package intentionally keeps a strict separation of concerns:

- Provider: transport/native-history mechanics
- Tools extension: tool schema/call mapping
- Reasoning extension: reasoning request/metadata behavior
- Usage extension: usage metadata behavior
- Verbosity extension: verbosity request shaping

This scaffold subtask wires packaging, plugin registration, and baseline load tests.
