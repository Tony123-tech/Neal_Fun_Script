"""Shared helpers for handlers and main."""

import logging

from playwright.sync_api import Page

from config import SELECTORS, TIMEOUTS

logger = logging.getLogger(__name__)


def read_vue_child(page: Page, key: str):
    """Read $data of a Vue child component that has the given key."""
    return page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return null;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().{key} !== undefined
            );
            return inst ? inst.$data : null;
        }}
    """)


def wait_for_level_change(page: Page, timeout: int | None = None) -> None:
    """Wait until the level text changes (or timeout)."""
    timeout = timeout or TIMEOUTS["click_wait"]
    try:
        page.wait_for_function(
            """() => {
                const el = document.querySelector('.site-level span');
                return el && el.textContent.startsWith('Level');
            }""",
            timeout=timeout,
        )
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])


def click_verify(page: Page, level_name: str) -> None:
    """Click the Verify button and wait for the next level to load."""
    page.locator(SELECTORS["verify_btn"]).click()
    wait_for_level_change(page)
    logger.info(f"[{level_name}] Verify clicked.")


def wait_for_grid(page: Page, selector: str) -> None:
    """Wait for the first element matching the selector to be visible."""
    page.locator(selector).first.wait_for(state="visible")


def wait_for_vue(page: Page, key: str, condition: str, timeout: int | None = None) -> None:
    """Wait until a Vue condition is true."""
    timeout = timeout or TIMEOUTS["vue_condition"]
    page.wait_for_function(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return false;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().{key} !== undefined
            );
            return inst && ({condition});
        }}
    """, timeout=timeout)