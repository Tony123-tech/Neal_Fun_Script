"""Shared helpers for handlers and main."""

import logging

from playwright.sync_api import Page

from Iam_not_a_robot.Python.config import SELECTORS, TIMEOUTS

logger = logging.getLogger(__name__)

__all__ = [
    "read_vue_child",
    "wait_for_level_change",
    "click_verify",
    "wait_for_grid",
    "wait_for_vue",
]


def read_vue_child(page: Page, key: str):
    """Read $data of a Vue child component that has the given key.

    Args:
        page: Playwright page object.
        key: A key present in the target component's $data.

    Returns:
        The component's $data dict, or None if not found.

    Example:
        data = read_vue_child(page, "puzzle")
        words = data["words"]
    """
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
    """Wait until the level text actually CHANGES (not just exists).

    Args:
        page: Playwright page object.
        timeout: Max wait time in ms (defaults to TIMEOUTS["click_wait"]).

    Note:
        Falls back to a short fixed wait if the level text is unavailable.
    """
    timeout = timeout or TIMEOUTS["click_wait"]

    # Snapshot the current level text before waiting
    try:
        old_level = page.locator(SELECTORS["level_text"]).inner_text(timeout=500)
    except Exception:
        old_level = ""

    try:
        page.wait_for_function(
            f"""() => {{
                const el = document.querySelector('{SELECTORS["level_text"]}');
                if (!el) return false;
                const text = el.textContent.trim();
                return text.length > 0 && text !== {repr(old_level)};
            }}""",
            timeout=timeout,
        )
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])


def click_verify(page: Page, level_name: str) -> None:
    """Click the Verify button and wait for the next level to load.

    Args:
        page: Playwright page object.
        level_name: Level name for logging.
    """
    page.locator(SELECTORS["verify_btn"]).click()
    wait_for_level_change(page)
    logger.info(f"[{level_name}] Verify clicked.")


def wait_for_grid(page: Page, selector: str, timeout: int | None = None) -> None:
    """Wait for the first element matching the selector to be visible.

    Args:
        page: Playwright page object.
        selector: CSS selector.
        timeout: Max wait time in ms (defaults to TIMEOUTS["vue_condition"]).
    """
    timeout = timeout or TIMEOUTS["vue_condition"]
    page.locator(selector).first.wait_for(state="visible", timeout=timeout)


def wait_for_vue(page: Page, key: str, condition: str, timeout: int | None = None) -> None:
    """Wait until a Vue condition is true.

    Args:
        page: Playwright page object.
        key: A key present in the target component's $data.
        condition: JS expression using `inst` (the component).
        timeout: Max wait time in ms (defaults to TIMEOUTS["vue_condition"]).

    Example:
        wait_for_vue(page, "grid", "inst.$data.grid.every(x => x === null)")
    """
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

