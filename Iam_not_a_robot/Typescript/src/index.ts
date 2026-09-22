/** Entry point: launch browser, run the main loop. */

import { chromium, type Browser, type Page } from "playwright";
import { GAME_URL, SELECTORS, TIMEOUTS, BROWSER } from "./config";
import { LEVEL_HANDLERS, LevelFailed } from "./handlers";
import { logger } from "./logger";

// ══════════════════════════════════════
//  Helpers
// ══════════════════════════════════════
async function getLevel(page: Page): Promise<string> {
  try {
    return await page
      .locator(SELECTORS.level_text)
      .innerText({ timeout: TIMEOUTS.level_text });
  } catch {
    return "unknown";
  }
}

async function screenshot(page: Page, name: string): Promise<void> {
  try {
    await page.screenshot({ path: `error_${name}.png` });
    logger.info(`📸 Screenshot saved: error_${name}.png`);
  } catch {
    /* ignore */
  }
}

// ══════════════════════════════════════
//  Main loop
// ══════════════════════════════════════
async function solve(page: Page): Promise<void> {
  let name = "unknown";

  while (true) {
    try {
      const level = await getLevel(page);
      logger.info(`Current level: ${level}`);

      name = level.includes(":")
        ? level.split(":", 2)[1].trim()
        : level;

      const handler = LEVEL_HANDLERS.get(name);
      if (!handler) {
        logger.warn(`No handler for '${name}', stopping.`);
        break;
      }

      logger.info(`Running handler: ${name}`);
      await handler(page);
      await page.waitForTimeout(TIMEOUTS.loop_wait);
    } catch (e) {
      if (e instanceof LevelFailed) {
        logger.error(`❌ Level failed: ${e.message}`);
        await screenshot(page, name);
        break;
      }

      logger.error(
        `❌ Unexpected error at level '${name}': ${(e as Error).message}`
      );
      // Full stack trace
      // eslint-disable-next-line no-console
      console.error(e);
      await screenshot(page, name);
      break;
    }
  }
}

// ══════════════════════════════════════
//  Bootstrap
// ══════════════════════════════════════
async function main(): Promise<void> {
  const browser: Browser = await chromium.launch({
    headless: BROWSER.headless,
    args: [...BROWSER.args],
  });

  const context = await browser.newContext({
    viewport: {
      width: BROWSER.viewport.width,
      height: BROWSER.viewport.height,
    },
    locale: BROWSER.locale,
  });

  // ══════════════════════════════════════════════════════
  //  Force getUserMedia to reject so that Level 39
  //  (Facial Exam) sets noCamera = true automatically,
  //  and macOS doesn't show the camera permission dialog.
  // ══════════════════════════════════════════════════════
  await context.addInitScript(() => {
    if (
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia
    ) {
      navigator.mediaDevices.getUserMedia = function () {
        return Promise.reject(
          new DOMException(
            "Permission denied by automation",
            "NotAllowedError"
          )
        );
      };
    }
  });

  const page = await context.newPage();

  logger.info(`Opening: ${GAME_URL}`);
  await page.goto(GAME_URL, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(TIMEOUTS.page_load);

  await solve(page);

  // Keep the browser open until the user presses Enter
  await new Promise<void>((resolve) => {
    process.stdin.resume();
    process.stdin.once("data", () => resolve());
  });

  await browser.close();
}

main().catch((err) => {
  logger.error(`Fatal error: ${(err as Error).message}`);
  // eslint-disable-next-line no-console
  console.error(err);
  process.exit(1);
});