from __future__ import annotations

from mcp.server.fastmcp import FastMCP


BEGIN_SENTINEL = "BEGIN_SENTINEL"
MIDDLE_SENTINEL = "MIDDLE_SENTINEL"
END_SENTINEL = "END_SENTINEL"


def _line(prefix: str, index: int, line_length: int) -> str:
    seed = f"{prefix}-{index:06d} "
    if len(seed) >= line_length:
        return seed[:line_length]
    fill = chr(ord("a") + (index % 26))
    return seed + (fill * (line_length - len(seed)))


def large_text_payload(*, size_chars: int, line_length: int = 80) -> str:
    size_chars = max(0, int(size_chars))
    line_length = max(20, int(line_length))
    header = f"{BEGIN_SENTINEL} size_chars={size_chars}\n"
    middle = f"\n{MIDDLE_SENTINEL} size_chars={size_chars}\n"
    footer = f"\n{END_SENTINEL} size_chars={size_chars}\n"
    budget = max(0, size_chars - len(header) - len(middle) - len(footer))
    half = budget // 2

    first: list[str] = []
    first_chars = 0
    index = 0
    while first_chars < half:
        line = _line("head", index, line_length) + "\n"
        if first_chars + len(line) > half:
            break
        first.append(line)
        first_chars += len(line)
        index += 1

    second: list[str] = []
    second_chars = 0
    index = 0
    remaining = budget - first_chars
    while second_chars < remaining:
        line = _line("tail", index, line_length) + "\n"
        if second_chars + len(line) > remaining:
            break
        second.append(line)
        second_chars += len(line)
        index += 1

    return header + "".join(first) + middle + "".join(second) + footer


def large_error_payload(*, size_chars: int, line_length: int = 80) -> str:
    payload = large_text_payload(size_chars=size_chars, line_length=line_length)
    return "DUMMY_ERROR_START\n" + payload


def create_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8775,
    log_level: str = "warning",
) -> FastMCP:
    server = FastMCP(
        "dummy-mcp-output-server",
        host=host,
        port=port,
        log_level=log_level.upper(),
        streamable_http_path="/mcp",
        stateless_http=True,
    )

    @server.tool()
    def large_text_output(size_chars: int = 65536, line_length: int = 80) -> str:
        """Return deterministic large text with begin/middle/end sentinels."""

        return large_text_payload(size_chars=size_chars, line_length=line_length)

    @server.tool()
    def large_error_output(size_chars: int = 65536, line_length: int = 80) -> str:
        """Raise a deterministic large error payload."""

        raise RuntimeError(
            large_error_payload(size_chars=size_chars, line_length=line_length)
        )

    @server.tool()
    def multi_block_output(block_count: int = 4, block_size: int = 4096) -> str:
        """Return deterministic text representing multiple logical blocks."""

        block_count = max(1, int(block_count))
        block_size = max(128, int(block_size))
        parts = []
        for index in range(block_count):
            parts.append(
                f"BLOCK_{index}_START\n"
                + large_text_payload(size_chars=block_size, line_length=80)
                + f"\nBLOCK_{index}_END"
            )
        return "\n".join(parts)

    return server
