# OpenRouter Tools Tests – Sample curl Requests

This document shows how to call OpenRouter's `chat/completions` endpoint
with curl for the same scenarios covered in
`core/python/tests/test_openrouter_tools_comprehensive.py`.

These examples assume:

- You have `OPENROUTER_API_KEY` exported in your shell
- You are using the OpenRouter base URL: `https://openrouter.ai/api/v1`
- You are targeting `openai/gpt-5-mini`
- You want **non-streaming** responses (no `stream: true`)
- You optionally route via a specific backend using the
  `provider` block (e.g. `openai` or `azure`), matching how the
  tests use `RequestOptionsFeature` and `OPENAI_PROVIDER`.

> Note: The `tools` blocks below mirror the schemas provided by
> `FileReaderTool` and `MathTools`. Tool execution and tool result
> handling are done by your application; OpenRouter just returns
> tool calls.

---

## 1. Single math tool call (15 + 27)

Equivalent to `test_single_tool_call_math`.

```bash
curl -X POST "$OPENROUTER_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-5-mini",
    "reasoning_effort": "low",
    "include_reasoning": true,
    "provider": {
      "order": ["openai"],
      "allow_fallbacks": false
    }
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "add",
          "description": "Add two numbers",
          "parameters": {
            "type": "object",
            "properties": {
              "a": {"type": "number", "description": "First number"},
              "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
          }
        }
      }
    ],
    "tool_choice": "auto",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant. When asked to perform calculations, you MUST use the provided math tools (add, multiply, square). Never calculate manually."
      },
      {
        "role": "user",
        "content": "Use the add tool to calculate 15 + 27. Return only the result."
      }
    ]
  }'
```

After you receive an assistant message with `tool_calls`, you
should:

1. Execute the indicated tool(s) in your application
2. Append a `tool` role message with the tool results
3. Send a **second** `chat/completions` request with the augmented
   `messages` array to get the final natural-language answer.

Only the **first** call is shown here.

---

## 2. Single file read using `read_file`

Equivalent to `test_single_tool_call_file_read`.

This example assumes you have a file `numbers.txt` in a working
directory on your backend. OpenRouter itself does **not** read
files; it only issues tool calls.

```bash
curl -X POST "$OPENROUTER_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-5-mini",
    "reasoning_effort": "low",
    "include_reasoning": true,
    "provider": {
      "order": ["openai"],
      "allow_fallbacks": false
    }
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "read_file",
          "description": "Read contents of a text file.",
          "parameters": {
            "type": "object",
            "properties": {
              "file_path": {
                "type": "string",
                "description": "Path to the file to read"
              }
            },
            "required": ["file_path"]
          }
        }
      }
    ],
    "tool_choice": "auto",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant. When asked about file contents, you MUST use the read_file tool. Never guess."
      },
      {
        "role": "user",
        "content": "Use the read_file tool to read numbers.txt and tell me its exact content."
      }
    ]
  }'
```

Again, after receiving `tool_calls`, your application runs the
`read_file` tool, appends a `tool` message with the result, and
sends a follow-up `chat/completions` request to obtain the final
answer.

---

## 3. Parallel math tool calls

Equivalent to `test_parallel_tool_calls_math` (three calculations
in one turn).

```bash
curl -X POST "$OPENROUTER_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-5-mini",
    "reasoning_effort": "low",
    "include_reasoning": true,
    "provider": {
      "order": ["openai"],
      "allow_fallbacks": false
    }
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "add",
          "description": "Add two numbers",
          "parameters": {
            "type": "object",
            "properties": {
              "a": {"type": "number"},
              "b": {"type": "number"}
            },
            "required": ["a", "b"]
          }
        }
      },
      {
        "type": "function",
        "function": {
          "name": "multiply",
          "description": "Multiply two numbers",
          "parameters": {
            "type": "object",
            "properties": {
              "a": {"type": "number"},
              "b": {"type": "number"}
            },
            "required": ["a", "b"]
          }
        }
      },
      {
        "type": "function",
        "function": {
          "name": "square",
          "description": "Square a number (multiply it by itself)",
          "parameters": {
            "type": "object",
            "properties": {
              "x": {"type": "number"}
            },
            "required": ["x"]
          }
        }
      }
    ],
    "tool_choice": "auto",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant. When asked to perform multiple calculations, issue multiple tool calls in parallel. Use the math tools provided."
      },
      {
        "role": "user",
        "content": "Calculate three values using tools in parallel: (1) add 10 and 5, (2) multiply 3 and 7, (3) square 6. Return all three results."
      }
    ]
  }'
```

The first assistant response should contain multiple `tool_calls`,
which your application executes (possibly in parallel) before
sending a follow-up request with the tool results.

---

## 4. Parallel file reads

Equivalent to `test_parallel_tool_calls_file_read`.

```bash
curl -X POST "$OPENROUTER_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-5-mini",
    "reasoning_effort": "low",
    "include_reasoning": true,
    "provider": {
      "order": ["openai"],
      "allow_fallbacks": false
    }
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "read_file",
          "description": "Read contents of a text file.",
          "parameters": {
            "type": "object",
            "properties": {
              "file_path": {"type": "string"}
            },
            "required": ["file_path"]
          }
        }
      }
    ],
    "tool_choice": "auto",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant. When asked to read multiple files, issue multiple read_file calls in parallel."
      },
      {
        "role": "user",
        "content": "Read both files in parallel: numbers.txt and data.txt. Then tell me the sum of the numbers they contain."
      }
    ]
  }'
```

Your application will receive multiple `tool_calls` to `read_file`
with different `file_path` arguments, run them, append `tool`
messages, and then send a second `chat/completions` request.

---

## 5. Tool chain: file then math

Equivalent to `test_tool_chain_file_then_math`.

```bash
curl -X POST "$OPENROUTER_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-5-mini",
    "reasoning_effort": "low",
    "include_reasoning": true,
    "provider": {
      "order": ["openai"],
      "allow_fallbacks": false
    }
    "tools": [
      {"type": "function", "function": {"name": "read_file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}},
      {"type": "function", "function": {"name": "square", "parameters": {"type": "object", "properties": {"x": {"type": "number"}}, "required": ["x"]}}}
    ],
    "tool_choice": "auto",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant. Use tools to read a number from a file, then square it."
      },
      {
        "role": "user",
        "content": "First read the number from numbers.txt, then square that number using the square tool. Report the final result."
      }
    ]
  }'
```

The model should first call `read_file`, then (after you send a
follow-up request with the tool result) call `square`, and finally
produce a natural-language answer.

---

## 6. Complex tool chain (two files, add, then square)

Equivalent to `test_tool_chain_complex_multi_step`.

```bash
curl -X POST "$OPENROUTER_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-5-mini",
    "reasoning_effort": "low",
    "include_reasoning": true,
    "provider": {
      "order": ["openai"],
      "allow_fallbacks": false
    }
    "tools": [
      {"type": "function", "function": {"name": "read_file", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]}}},
      {"type": "function", "function": {"name": "add", "parameters": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}, "required": ["a", "b"]}}},
      {"type": "function", "function": {"name": "square", "parameters": {"type": "object", "properties": {"x": {"type": "number"}}, "required": ["x"]}}}
    ],
    "tool_choice": "auto",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant. Use tools to read two numbers from files, add them, then square the result. Show your work step by step."
      },
      {
        "role": "user",
        "content": "Read numbers from numbers.txt and data.txt, add them together, then square the result."
      }
    ]
  }'
```

You will typically see a sequence of tool calls:

1. `read_file` for each file
2. `add` with the two numbers
3. `square` with the sum

Between each step you execute the tools, append `tool` messages,
and send follow-up `chat/completions` requests until the model
returns a final assistant message without further `tool_calls`.

---

These examples can be adapted for **streaming** by adding
`"stream": true` to the JSON body and handling the
Server-Sent Events (SSE) responses as demonstrated in the
Python tests.
