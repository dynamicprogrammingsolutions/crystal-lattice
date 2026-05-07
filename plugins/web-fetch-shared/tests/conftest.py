"""Test fixtures for web-fetch-shared tests."""

from __future__ import annotations

import pytest
from aiohttp import web


@pytest.fixture
async def mock_http_server(aiohttp_server):
    """Mock HTTP server for testing fetch operations."""

    async def html_handler(request):
        return web.Response(
            text="<html><body><h1>Test Page</h1><p>Test content</p></body></html>",
            content_type="text/html",
        )

    async def text_handler(request):
        return web.Response(
            text="Plain text content",
            content_type="text/plain",
        )

    async def markdown_handler(request):
        return web.Response(
            text="# Title\n\nMarkdown content",
            content_type="text/markdown",
        )

    async def html_with_charset_handler(request):
        return web.Response(
            text="<html><body><p>Content with charset</p></body></html>",
            content_type="text/html; charset=utf-8",
        )

    async def error_404_handler(request):
        return web.Response(status=404, text="Not found", content_type="text/plain")

    async def error_500_handler(request):
        return web.Response(
            status=500, text="Internal server error", content_type="text/plain"
        )

    async def large_handler(request):
        # Returns content larger than default max_size (10MB)
        return web.Response(text="x" * (20 * 1024 * 1024), content_type="text/plain")

    async def redirect_handler(request):
        # Redirect to /html
        raise web.HTTPFound("/html")

    async def redirect_chain_handler(request):
        # Redirect to /redirect for testing max_redirects
        raise web.HTTPFound("/redirect")

    async def slow_handler(request):
        # Handler that never responds (for timeout testing)
        import asyncio

        await asyncio.sleep(100)
        return web.Response(text="Should not reach", content_type="text/plain")

    async def json_handler(request):
        return web.Response(
            text='{"key": "value"}',
            content_type="application/json",
        )

    async def html_complex_handler(request):
        return web.Response(
            text="""<!DOCTYPE html>
<html>
<head><title>Complex Page</title></head>
<body>
    <article>
        <h1>Main Article</h1>
        <p>This is the main content.</p>
        <table>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
        </table>
        <!-- A comment -->
        <p>More content.</p>
    </article>
    <nav>Sidebar content</nav>
</body>
</html>""",
            content_type="text/html",
        )

    app = web.Application()
    app.router.add_get("/html", html_handler)
    app.router.add_get("/text", text_handler)
    app.router.add_get("/markdown", markdown_handler)
    app.router.add_get("/html-charset", html_with_charset_handler)
    app.router.add_get("/404", error_404_handler)
    app.router.add_get("/500", error_500_handler)
    app.router.add_get("/large", large_handler)
    app.router.add_get("/redirect", redirect_handler)
    app.router.add_get("/redirect-chain", redirect_chain_handler)
    app.router.add_get("/slow", slow_handler)
    app.router.add_get("/json", json_handler)
    app.router.add_get("/html-complex", html_complex_handler)

    return await aiohttp_server(app)
