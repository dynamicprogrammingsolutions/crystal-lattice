#!/usr/bin/env python3
"""Smoke-test the locally served landing and documentation sites."""

from __future__ import annotations

import argparse
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright


IGNORED_EXTERNAL_RESPONSE_PREFIXES = (
    "https://api.github.com/repos/dynamicprogrammingsolutions/crystal-lattice",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--landing-url",
        default="http://127.0.0.1:4321",
    )
    parser.add_argument(
        "--docs-url",
        default="http://127.0.0.1:8001",
    )
    return parser.parse_args()


def require_success(page: Page, url: str) -> None:
    response = page.goto(url, wait_until="load")
    if response is None or not response.ok:
        status = "no response" if response is None else response.status
        raise AssertionError(f"{url} did not load successfully: {status}")


def record_console_error(browser_errors: list[str], prefix: str, message: object) -> None:
    message_type = getattr(message, "type", None)
    text = getattr(message, "text", str(message))
    if message_type == "error" and not text.startswith("Failed to load resource:"):
        browser_errors.append(f"{prefix} console: {text}")


def record_failed_response(browser_errors: list[str], prefix: str, response: object) -> None:
    status = getattr(response, "status", 0)
    url = getattr(response, "url", "<unknown>")
    if status >= 400 and not any(
        url.startswith(ignored) for ignored in IGNORED_EXTERNAL_RESPONSE_PREFIXES
    ):
        browser_errors.append(
            f"{prefix} response: {status} {url}"
        )


def main() -> None:
    args = parse_args()
    landing_url = args.landing_url.rstrip("/") + "/"
    docs_url = args.docs_url.rstrip("/") + "/"
    browser_errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        landing_page = context.new_page()
        landing_page.on(
            "console",
            lambda message: record_console_error(browser_errors, "landing", message),
        )
        landing_page.on(
            "response",
            lambda response: record_failed_response(browser_errors, "landing", response),
        )
        landing_page.on(
            "pageerror",
            lambda error: browser_errors.append(f"pageerror: {error}"),
        )

        require_success(landing_page, landing_url)
        docs_link = landing_page.locator("header a:visible", has_text="Docs")
        if docs_link.count() != 1:
            raise AssertionError("landing page must expose one visible Docs link")
        href = docs_link.get_attribute("href")
        if href != docs_url.rstrip("/"):
            raise AssertionError(
                f"landing Docs link is {href!r}, expected {docs_url.rstrip('/')!r}"
            )
        if docs_link.get_attribute("target") is not None:
            raise AssertionError("landing Docs link must remain in the current tab")

        with landing_page.expect_navigation(wait_until="load"):
            docs_link.click()
        docs_page = landing_page
        docs_page.on(
            "console",
            lambda message: record_console_error(browser_errors, "docs", message),
        )
        docs_page.on(
            "response",
            lambda response: record_failed_response(browser_errors, "docs", response),
        )
        docs_page.on(
            "pageerror",
            lambda error: browser_errors.append(f"docs pageerror: {error}"),
        )
        docs_page.wait_for_load_state("load")
        if docs_page.url.rstrip("/") != docs_url.rstrip("/"):
            raise AssertionError(
                f"Docs link opened {docs_page.url!r}, expected {docs_url!r}"
            )
        docs_page.get_by_role(
            "heading",
            name="Crystal Lattice Docs",
            exact=True,
        ).wait_for()
        privacy_link = docs_page.get_by_role(
            "link",
            name="Privacy Policy",
            exact=True,
        )
        if privacy_link.count() != 1:
            raise AssertionError("docs footer must expose one Privacy Policy link")
        expected_privacy_url = urljoin(landing_url, "privacy")
        if privacy_link.get_attribute("href") != expected_privacy_url:
            raise AssertionError(
                "docs Privacy Policy link is "
                f"{privacy_link.get_attribute('href')!r}, expected {expected_privacy_url!r}"
            )
        privacy_response = context.request.get(expected_privacy_url)
        if not privacy_response.ok:
            raise AssertionError(
                f"Privacy Policy failed: {privacy_response.status} {expected_privacy_url}"
            )
        if docs_page.get_by_role(
            "link",
            name="Package documentation",
            exact=False,
        ).count() != 1:
            raise AssertionError("docs overview must link the package catalog")
        if docs_page.locator(".md-tabs__link:visible", has_text="Packages").count() != 1:
            raise AssertionError("desktop docs navigation must expose Packages")
        search = docs_page.locator("input.md-search__input:visible")
        search.click()
        search.press_sequentially("Core Python SDK", delay=20)
        docs_page.wait_for_timeout(800)
        if docs_page.locator(
            '[data-md-component="search-result"] '
            'a[href*="packages/core-python/"]'
        ).count() == 0:
            raise AssertionError("search must discover the Core package page")

        packages_url = urljoin(docs_url, "packages/")
        require_success(docs_page, packages_url)
        docs_page.get_by_role(
            "heading",
            name="Package Documentation",
            exact=True,
        ).wait_for()
        if docs_page.locator("article h2").count() != 4:
            raise AssertionError("package catalog must expose four package groups")

        package_links = docs_page.locator("article ul li a[href]")
        package_routes: list[tuple[str, str]] = []
        for index in range(package_links.count()):
            link = package_links.nth(index)
            href = link.get_attribute("href")
            text = link.inner_text().strip()
            if href:
                package_routes.append((text, urljoin(packages_url, href)))
        if len(package_routes) != 11:
            raise AssertionError(
                f"package catalog exposed {len(package_routes)} package links, expected 11"
            )

        for title, package_url in package_routes:
            response = context.request.get(package_url)
            if not response.ok:
                raise AssertionError(
                    f"package route for {title!r} failed: "
                    f"{response.status} {package_url}"
                )

        core_link = docs_page.get_by_role(
            "link",
            name="Core Python SDK",
            exact=True,
        )
        core_href = core_link.get_attribute("href")
        if not core_href:
            raise AssertionError("Core Python SDK catalog link has no href")
        require_success(docs_page, urljoin(packages_url, core_href))
        docs_page.get_by_role(
            "heading",
            name="AI Agent Platform - Core SDK (Python)",
            exact=True,
        ).wait_for()
        if docs_page.locator(
            ".md-tabs__item--active .md-tabs__link",
            has_text="Packages",
        ).count() != 1:
            raise AssertionError("package pages must retain active Packages context")

        mobile_page = context.new_page()
        mobile_page.set_viewport_size({"width": 390, "height": 844})
        require_success(mobile_page, landing_url)
        mobile_docs_link = mobile_page.locator("header a:visible", has_text="Docs")
        if mobile_docs_link.count() != 1:
            raise AssertionError("mobile landing header must expose Docs")
        if mobile_docs_link.get_attribute("href") != docs_url.rstrip("/"):
            raise AssertionError("mobile landing Docs link uses the wrong URL")

        require_success(mobile_page, docs_url)
        navigation_toggle = mobile_page.get_by_role(
            "button",
            name="Open navigation",
            exact=True,
        )
        navigation_toggle.focus()
        mobile_page.keyboard.press("Enter")
        if not mobile_page.locator("#__drawer").is_checked():
            raise AssertionError("mobile navigation must support keyboard activation")
        if mobile_page.locator(
            ".md-sidebar--primary",
            has_text="application-config-app",
        ).count():
            raise AssertionError(
                "mobile primary navigation must not enumerate every built-in plugin"
            )
        palette_toggle = mobile_page.locator(
            '.md-header label[for^="__palette_"]:visible'
        )
        palette_input_id = palette_toggle.get_attribute("for")
        if not palette_toggle.get_attribute("aria-label"):
            raise AssertionError("visible theme toggle must have an accessible name")
        palette_toggle.press("Enter")
        if not palette_input_id or not mobile_page.locator(
            f"#{palette_input_id}"
        ).is_checked():
            raise AssertionError("visible theme toggle must support keyboard activation")

        plugin_docs_url = urljoin(
            docs_url,
            "built-in-plugins/cloud-agent-app/docs/",
        )
        require_success(mobile_page, plugin_docs_url)
        mobile_page.get_by_role(
            "heading",
            name="cloud-agent-app documentation",
            exact=True,
        ).wait_for()
        require_success(
            mobile_page,
            urljoin(plugin_docs_url, "cloud-script-authoring/"),
        )
        mobile_page.get_by_role(
            "heading",
            name="Cloud Script Authoring Guide",
            exact=True,
        ).wait_for()

        browser.close()

    if browser_errors:
        raise AssertionError("\n".join(browser_errors))
    print("Landing and documentation site smoke test passed.")


if __name__ == "__main__":
    main()