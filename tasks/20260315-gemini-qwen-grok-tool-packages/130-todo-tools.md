# 130 - Todo Tools (All Vendors)

Short description: Add vendor-compatible todo/task-list tools to all four vendor packages, sharing a flexible todo data model and per-vendor result formatting from `tool-compat-shared`. Kimi's Python-native implementation serves as the first seed.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/090-kimi-tools.md`

## Goal

Add one tool type (todo/task list management) across all four vendor packages. Each vendor has different tool names, item shapes, status enums, and result patterns. The shared helpers provide a common data model and formatting utilities, while each vendor wrapper preserves its own schema and output format.

## Public package outcome

1. `plugins/gemini-tools/`
- `GeminiWriteTodosTool` (tool name: `write_todos`)
2. `plugins/qwen-tools/`
- `QwenTodoWriteTool` (tool name: `todo_write`)
3. `plugins/grok-tools/`
- `GrokCreateTodoListTool` (tool name: `create_todo_list`)
- `GrokUpdateTodoListTool` (tool name: `update_todo_list`)
4. `plugins/kimi-tools/`
- `KimiSetTodoListTool` (tool name: `SetTodoList`)

## Key source references

### Gemini

- WriteTodos tool implementation:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/write-todos.ts:28` (`class WriteTodosToolInvocation`), line 72 (`class WriteTodosTool`)
- Schema:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts:476`
  - Item shape: `{description: str, status: "pending"|"in_progress"|"completed"|"cancelled"}`
  - Full-list replacement semantics.
  - Schema description includes extensive methodology guidance (when to use, task state definitions, examples).

### Qwen

- TodoWrite tool implementation:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/todoWrite.ts:425` (`class TodoWriteTool`)
- Tool names:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/tool-names.ts` (verify exact tool name)
- Item shape: `{id: str, content: str, status: "pending"|"in_progress"|"completed"}`
- Full-list replacement semantics.
- Requires `id` field for each item.

### Grok

- Tool schemas:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts` (line ~160)
- `create_todo_list`:
  - Item shape: `{id: str, content: str, status: "pending"|"in_progress"|"completed", priority: "high"|"medium"|"low"}`
  - Full-list replacement.
- `update_todo_list`:
  - Update shape: `{id: str, status?: str, content?: str, priority?: str}`
  - `id` required; other fields optional.
  - Updates existing items by ID.
- Two-tool pattern: create replaces full list, update patches individual items.

### Kimi

- SetTodoList implementation:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/todo/__init__.py` (`class SetTodoList`)
- Description template:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/todo/set_todo_list.md`
- Item shape: `{title: str, status: "pending"|"in_progress"|"done"}`
- Full-list replacement semantics.
- Result includes `display: [TodoDisplayBlock(items=...)]` for UI rendering.

## Compatibility findings

### Four different schemas

| Aspect | Gemini | Qwen | Grok | Kimi |
|--------|--------|------|------|------|
| Tool name(s) | `write_todos` | `todo_write` | `create_todo_list` + `update_todo_list` | `SetTodoList` |
| Number of tools | 1 | 1 | 2 | 1 |
| Item description field | `description` | `content` | `content` | `title` |
| Item ID field | (none) | `id` (required) | `id` (required) | (none) |
| Item priority field | (none) | (none) | `priority` (`high`/`medium`/`low`) | (none) |
| Status: pending | `pending` | `pending` | `pending` | `pending` |
| Status: in progress | `in_progress` | `in_progress` | `in_progress` | `in_progress` |
| Status: completed | `completed` | `completed` | `completed` | `done` |
| Status: cancelled | `cancelled` | (none) | (none) | (none) |
| Semantics | Full-list replacement | Full-list replacement | Create: full-list; Update: patch by ID | Full-list replacement |

### Kimi's `SetTodoList` is the simplest seed

Kimi's implementation is minimal: it takes a list of `{title, status}` items and returns a display block. This is a good starting point for the shared helper.

### Grok's two-tool pattern is unique

Grok splits todo management into two tools:
- `create_todo_list`: replaces the entire todo list (like the other vendors).
- `update_todo_list`: patches individual items by `id` (no other vendor has this).

The shared helper should support both full-list replacement and patch-by-ID patterns.

### Gemini's schema has extensive guidance

Gemini's `write_todos` schema description includes:
- Methodology for using the todo list.
- Task state definitions.
- Examples of when to use and when NOT to use.
- Update cadence requirements.

This guidance text should be preserved in the schema description.

## Proposed shared internals in `tool-compat-shared`

### New module: `todo_engine.py`

1. **Flexible todo item model**:
   ```python
   @dataclass
   class TodoItem:
       id: str | None = None
       title: str | None = None       # Kimi name
       description: str | None = None  # Gemini name
       content: str | None = None      # Qwen/Grok name
       status: str = "pending"
       priority: str | None = None     # Grok only
   ```

2. **Status enum normalization**:
   - `normalize_status(status, vendor) -> str` — maps vendor-specific completed status (`"completed"` vs `"done"`) to a canonical form.
   - `validate_status(status, vendor) -> bool` — checks if a status is valid for a given vendor.

3. **Full-list replacement**:
   - `replace_todo_list(new_items, vendor) -> list[TodoItem]` — validates and stores the new list.

4. **Patch by ID**:
   - `update_todo_items(existing_items, updates, vendor) -> list[TodoItem]` — applies partial updates to existing items by ID.

5. **Result formatting per vendor**:
   - `format_gemini_todos_result(items) -> dict`
   - `format_qwen_todos_result(items) -> dict`
   - `format_kimi_todos_result(items) -> dict`
   - `format_grok_create_result(items) -> dict`
   - `format_grok_update_result(updated_items) -> dict`

6. **Schema description builders**:
   - Per-vendor schema descriptions including methodology guidance (especially Gemini's).

## Response formatting requirement

### Gemini

- Result: the updated todo list as structured output.
- Schema description: extensive methodology guidance including task state definitions, when to use/not use, update cadence rules, and examples. This must be preserved verbatim.
- Status values: `pending`, `in_progress`, `completed`, `cancelled`.

### Qwen

- Result: the updated todo list as structured output.
- Verify exact message format from source during implementation.
- Status values: `pending`, `in_progress`, `completed`.
- `id` field required.

### Grok

- `create_todo_list` result: the created list as structured output.
- `update_todo_list` result: the updated items as structured output.
- Status values: `pending`, `in_progress`, `completed`.
- Priority values: `high`, `medium`, `low`.
- Verify exact formatting from source during implementation.

### Kimi

- Result: `{message: "Todo list updated", display: [TodoDisplayBlock(items=[TodoDisplayItem(title=..., status=...)])]}`.
- Status values: `pending`, `in_progress`, `done`.
- The `display` block contains the formatted todo list for UI rendering.

Implementation pattern: shared helpers produce vendor-neutral todo lists; vendor wrappers apply vendor-specific validation, status normalization, and result formatting.

## Behavior requirements

### Gemini (`write_todos`)

1. Tool name: `write_todos`. Param: `todos` (array of `{description, status}`).
2. Full-list replacement semantics.
3. Status validation: `pending`, `in_progress`, `completed`, `cancelled`.
4. No ID field.
5. Schema description includes methodology guidance (preserve verbatim).

### Qwen (`todo_write`)

1. Tool name: `todo_write`. Param: `todos` (array of `{id, content, status}`).
2. Full-list replacement semantics.
3. Status validation: `pending`, `in_progress`, `completed`.
4. `id` required for each item.

### Grok (`create_todo_list` + `update_todo_list`)

1. `create_todo_list`: params `todos` (array of `{id, content, status, priority}`). All fields required.
2. `update_todo_list`: params `updates` (array of `{id, status?, content?, priority?}`). Only `id` required.
3. `create_todo_list` replaces the entire list.
4. `update_todo_list` patches individual items by `id`.
5. Priority validation: `high`, `medium`, `low`.
6. Status validation: `pending`, `in_progress`, `completed`.

### Kimi (`SetTodoList`)

1. Tool name: `SetTodoList`. Param: `todos` (array of `{title, status}`).
2. Full-list replacement semantics.
3. Status validation: `pending`, `in_progress`, `done`.
4. No ID field.
5. Result includes `display` block with `TodoDisplayItem` list.

## Test plan

### Schema tests

1. Assert exact tool names and param names per vendor.
2. Assert status enum values per vendor.
3. Assert required vs optional fields per vendor.
4. Assert Gemini schema description contains methodology guidance.

### Todo operation tests

1. Create new todo list (all vendors).
2. Full-list replacement overwrites existing list.
3. Status validation rejects invalid values per vendor.
4. Kimi: `done` accepted; `completed` rejected.
5. Gemini: `cancelled` accepted.
6. Grok: `priority` field required for create, optional for update.
7. Grok: `update_todo_list` patches individual items by ID.
8. Grok: update with missing ID → validation error.

### Result formatting tests

1. Gemini: result structure matches expected shape.
2. Kimi: `display` block contains correct `TodoDisplayItem` entries.
3. Qwen: result includes `id` fields.
4. Grok: create returns full list; update returns updated items.

### Integration tests

1. Each package loads through plugin manager with todo tool(s) exposed.
2. OpenRouter integration tests (one per vendor with cheap model).

## Deliverables

1. Shared todo engine in `plugins/tool-compat-shared/src/tool_compat_shared/todo_engine.py`.
2. Shared todo tests in `plugins/tool-compat-shared/tests/test_todo_engine.py`.
3. Four vendor-specific todo tool classes (five total including Grok's two tools).
4. Package exports, manifests, and READMEs updated.
5. Tests for schema, behavior, and integration.

## Documentation follow-up

After implementation, update each vendor package README with:

1. Exposed todo tool name(s) and parameter shapes.
2. Vendor-specific status enum values.
3. Grok's two-tool create/update pattern explanation.
4. Gemini's methodology guidance summary.
