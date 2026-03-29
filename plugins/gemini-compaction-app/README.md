# Gemini Compaction App Plugin

Gemini-style context compaction application plugin for the AI Agent Platform.

## Overview

This plugin provides manual context compaction using Gemini's structured XML `<state_snapshot>` prompt format. It exposes session and message actions for compacting conversation history, with an optional verification pass that asks the model to self-critique and improve its summary.

## Features

- **Session Actions**: "Compact range", "Compact full history"
- **Message Action**: "Compact messages up to here"
- **Gemini `<state_snapshot>` prompt**: Structured XML output with sections for goals, constraints, knowledge, artifacts, file state, actions, and task state
- **Optional verification pass**: Second LLM call for self-correction
- **Configurable summarizer agent**: Use a dedicated agent for compaction

## Configuration

```yaml
application:
  gemini_compaction_agent_id: "summarizer"  # Optional dedicated summarizer agent
  gemini_compaction_prompt: null  # Custom prompt (default: Gemini <state_snapshot> prompt)
  gemini_compaction_settings_overrides:
    model: "gpt-4o-mini"  # Optional model override
  gemini_compaction_verification_pass: true  # Enable verification pass (default: true)
```

## Usage

### Session Action: "Compact range"

Select a range of messages to compact using Python-style slice indices (start:end). The selected messages will be replaced with a structured state snapshot.

### Message Action: "Compact messages up to here"

Click on a message and select this action to compact all messages before it.

### Session Action: "Compact full history"

Compact the entire conversation history into a single state snapshot.

## History Injection Shape

After compaction, the history becomes:

```
[system messages...]
user: <state_snapshot>...</state_snapshot>
assistant: Got it. Thanks for the additional context!
[preserved tail messages...]
```

## License

Apache 2.0