"""Entry point: launch browser, run the main loop."""

import logging
import traceback

from playwright.sync_api import sync_playwright, Page

from config import GAME_URL, SELECTORS, TIMEOUTS, BROWSER
from handlers import LEVEL_HANDLERS, LevelFailed


# ══════════════════════════════════════
#  Logging
# ══════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ══════════════════════════════════════
#  Helpers
# ══════════════════════════════════════
def get_level(page: Page) -> str:
    """Read the current level name, e.g. 'Level 1: Checkbox'."""
    try:
        return page.locator(SELECTORS["level_text"]).inner_text(
            timeout=TIMEOUTS["level_text"]
        )
    except Exception:
        return "unknown"


def _screenshot(page: Page, name: str) -> None:
    """Try to take a screenshot for debugging; ignore if page is closed."""
    try:
        page.screenshot(path=f"error_{name}.png")
        logger.info(f"📸 Screenshot saved: error_{name}.png")
    except Exception:
        pass  # Page may already be closed


# ══════════════════════════════════════
#  Main loop
# ══════════════════════════════════════
def solve(page: Page) -> None:
    """Keep solving levels until no handler is found."""
    name = "unknown"

    while True:
        try:
            level = get_level(page)
            logger.info(f"Current level: {level}")

            name = level.split(":", 1)[-1].strip() if ":" in level else level

            handler = LEVEL_HANDLERS.get(name)
            if not handler:
                logger.warning(f"No handler for '{name}', stopping.")
                break

            logger.info(f"Running handler: {name}")
            handler(page)
            page.wait_for_timeout(TIMEOUTS["loop_wait"])

        except LevelFailed as e:
            logger.error(f"❌ Level failed: {e}")
            _screenshot(page, name)
            break

        except Exception as e:
            logger.error(f"❌ Unexpected error at level '{name}': {e}")
            traceback.print_exc()
            _screenshot(page, name)
            break


# ══════════════════════════════════════
#  Entry point
# ══════════════════════════════════════
def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=BROWSER["headless"],
            args=BROWSER["args"],
        )
        context = browser.new_context(
            viewport=BROWSER["viewport"],
            locale=BROWSER["locale"],
        )
        page = context.new_page()

        logger.info(f"Opening: {GAME_URL}")
        page.goto(GAME_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(TIMEOUTS["page_load"])

        solve(page)

        input("\nPress Enter to close the browser...")
        browser.close()


if __name__ == "__main__":
    main()