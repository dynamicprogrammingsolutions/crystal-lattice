# Read Tool Investigation Notes

Status: initial success and offset/limit fixtures captured.

## Fixtures

- `plugins/claude-tools/investigation/fixtures/read/success-small-file.json`
- `plugins/claude-tools/investigation/fixtures/read/success-offset-limit.json`
- `plugins/claude-tools/investigation/fixtures/read/missing-file-error.json`
- `plugins/claude-tools/investigation/fixtures/read/large-file-truncation.json`
- `plugins/claude-tools/investigation/fixtures/read/empty-file.json`
- `plugins/claude-tools/investigation/fixtures/read/directory-path-error.json`
- `plugins/claude-tools/investigation/fixtures/read/small-image.json`
- `plugins/claude-tools/investigation/fixtures/read/small-pdf.json`
- `plugins/claude-tools/investigation/fixtures/read/large-pdf-requires-pages.json`
- `plugins/claude-tools/investigation/fixtures/read/pdf-pages-range.json`
- `plugins/claude-tools/investigation/fixtures/read/notebook-simple.json`

Raw logs are ignored under `plugins/claude-tools/investigation/raw/read/`.

## Tool Name

Claude Code advertises the file reader as:

```text
Read
```

## Schema

The committed fixture contains the full observed schema and description. Implementation should match:

- `name`: `Read`
- `input_schema.$schema`: `https://json-schema.org/draft/2020-12/schema`
- `input_schema.type`: `object`
- `required`: `["file_path"]`
- `additionalProperties`: `false`

Properties:

- `file_path`: string, required, absolute path to the file.
- `offset`: integer, minimum `0`, maximum `9007199254740991`.
- `limit`: integer, exclusive minimum `0`, maximum `9007199254740991`.
- `pages`: string, PDF page range.

## Observed Calls

Small-file call:

```json
{
  "type": "tool_use",
  "id": "<TOOL_CALL_ID>",
  "name": "Read",
  "input": {
    "file_path": "<WORKSPACE>/small-read.txt"
  }
}
```

Offset/limit call:

```json
{
  "type": "tool_use",
  "id": "<TOOL_CALL_ID>",
  "name": "Read",
  "input": {
    "file_path": "<WORKSPACE>/range-read.txt",
    "offset": 3,
    "limit": 2
  }
}
```

`offset: 3` returned line 3 as the first line, so offset behaves as a one-based displayed line number in the observed Claude Code behavior, despite the schema minimum allowing `0`.

## Result Formatting

Successful text reads are sent back as a user message containing one Anthropic `tool_result` block:

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "<TOOL_CALL_ID>",
      "content": "1\tfirst line\n2\tsecond line",
      "cache_control": {
        "type": "ephemeral"
      }
    }
  ]
}
```

The content string uses `cat -n` style formatting:

```text
<line-number>\t<line-content>
```

For a full small-file read, Claude Code included a numbered empty trailing line when the file ended with a newline:

```text
1\tCLAUDE_READ_SENTINEL first line
2\tsecond line
3\tthird line
4\t
```

For an offset/limit read, Claude Code returned only the requested lines and did not include an extra trailing numbered blank line:

```text
3\trange-line-3
4\trange-line-4
```

Successful tool results did not include `is_error` in the model-facing Anthropic payload.

Missing-file errors are sent back as a `tool_result` block with `is_error: true`:

```json
{
  "type": "tool_result",
  "tool_use_id": "<TOOL_CALL_ID>",
  "content": "File does not exist. Note: your current working directory is <WORKSPACE>.",
  "is_error": true,
  "cache_control": {
    "type": "ephemeral"
  }
}
```

Large file reads are also sent back with `is_error: true` when the file exceeds Claude Code's maximum full-read size. The observed generated fixture used a 667.7KB file and returned:

```text
File content (667.7KB) exceeds maximum allowed size (256KB). Use offset and limit parameters to read specific portions of the file, or search for specific content instead of reading the whole file.
```

This indicates full-file `Read` has a 256KB content cap in the observed setup. The tool description says the default is up to 2000 lines, but the file-size cap can fail first.

Empty files do not set `is_error`. The observed model-facing content is a system reminder:

```xml
<system-reminder>Warning: the file exists but is shorter than the provided offset (1). The file has 1 lines.</system-reminder>
```

Directory paths set `is_error: true`. The observed content is the platform error string:

```text
EISDIR: illegal operation on a directory, read '<WORKSPACE>'
```

## Image Behavior

Reading a PNG returns a native Anthropic image block inside the `tool_result.content` array:

```json
{
  "type": "tool_result",
  "tool_use_id": "<TOOL_CALL_ID>",
  "content": [
    {
      "type": "image",
      "source": {
        "type": "base64",
        "media_type": "image/png",
        "data": "..."
      }
    }
  ],
  "cache_control": {
    "type": "ephemeral"
  }
}
```

The final assistant answer in the Ollama-backed run did not reliably understand the image, but the model-facing tool-result payload was captured successfully. Implementation should preserve the native image block shape.

## PDF Behavior

Reading a PDF without `pages` returned a text tool result:

```text
PDF file read: <WORKSPACE>/small.pdf (562 bytes)
```

and for a larger 12-page generated PDF:

```text
PDF file read: <WORKSPACE>/large.pdf (4KB)
```

These PDF full-read results did not include `cache_control` in the captured payload. The generated PDF text was not surfaced to the model in the observed run; it appears Claude Code reports the file read rather than extracting visible text through this path.

After installing Poppler (`pdftoppm` version 26.04.0), reading a PDF with `pages: "2-3"` returned a mixed native content array:

```json
[
  {
    "type": "tool_result",
    "tool_use_id": "<TOOL_CALL_ID>",
    "content": "PDF pages extracted: 2 page(s) from <WORKSPACE>/large.pdf (4KB)"
  },
  {
    "type": "image",
    "source": {
      "type": "base64",
      "media_type": "image/jpeg",
      "data": "<BASE64 sha256=... length=24136>"
    }
  },
  {
    "type": "image",
    "source": {
      "type": "base64",
      "media_type": "image/jpeg",
      "data": "<BASE64 sha256=... length=24140>"
    },
    "cache_control": {
      "type": "ephemeral"
    }
  }
]
```

The Ollama model used for investigation rejected the follow-up request because it does not support image input, so `claude_returncode` is `1` for `pdf-pages-range`. The model-facing tool result was still captured. PDF page rendering parity should use Poppler/`pdftoppm` when available and return JPEG image blocks in this native Anthropic shape.

Reading the 12-page generated PDF without `pages` now returns an error before rendering:

```text
This PDF has 12 pages, which is too many to read at once. Use the pages parameter to read specific page ranges (e.g., pages: "1-5"). Maximum 20 pages per request.
```

This error sets `is_error: true` and includes `cache_control: {"type": "ephemeral"}`.

## Notebook Behavior

Reading a simple `.ipynb` returns `tool_result.content` as an array with one text block:

```json
{
  "type": "text",
  "text": "<cell id=\"cell-0\"><cell_type>markdown</cell_type># CLAUDE_NOTEBOOK_SENTINEL\nNotebook markdown cell.\n</cell id=\"cell-0\">\n<cell id=\"cell-1\">print('CLAUDE_NOTEBOOK_OUTPUT')\n</cell id=\"cell-1\">\n\nCLAUDE_NOTEBOOK_OUTPUT\n"
}
```

The notebook output includes:

- XML-like `<cell id="cell-N">` wrappers.
- `<cell_type>markdown</cell_type>` for markdown cells.
- Code source for code cells.
- Stream output after the code cell closing tag.

This appears simple enough to implement for common markdown/code/text-output notebooks without heavy dependencies.

## Implementation Direction

Use `tool-compat-shared` reader/path helpers where possible, but add Claude-specific formatting if existing helpers do not exactly match:

- absolute-path-only schema wording
- default read up to 2000 lines
- `cat -n` style numbered output with tab separator
- `offset`/`limit` behavior as captured above
- `cache_control` is handled by providers/tool loop on the Anthropic wire, not by the tool plugin result text itself
- image and notebook reads need native content arrays, not only strings
- PDF full-read behavior may be a simple status string unless richer native attachment behavior is discovered later

The first implementation can support text files only if image/PDF/notebook fidelity is out of scope, but the schema description should not claim behavior that the local tool cannot provide unless implementation catches up. If exact Claude schema is required, document any unsupported modalities clearly in tests or notes before shipping.

## Open Questions

- Exact PDF rendering may vary with Poppler version and fonts. The committed fixture normalizes JPEG base64 to hash/length placeholders.
- More image media types should be sampled before claiming broad image parity.
