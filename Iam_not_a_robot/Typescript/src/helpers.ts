/** Shared helpers for handlers and main. */

import type { Page } from "playwright";
import { SELECTORS, TIMEOUTS } from "./config";
import { logger } from "./logger";

/**
 * Read $data of a Vue child component that has the given key.
 *
 * @param page - Playwright page object.
 * @param key - A key present in the target component's $data.
 * @returns The component's $data object, or null if not found.
 */
export async function readVueChild<T = Record<string, unknown>>(
  page: Page,
  key: string
): Promise<T | null> {
  return page.evaluate(
    ({ pageContainer, dataKey }) => {
      const el = document.querySelector(pageContainer);
      const pageVm = (el as any)?.__vue__;
      if (!pageVm) return null;
      const inst = pageVm.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data()[dataKey] !== undefined
      );
      return inst ? inst.$data : null;
    },
    { pageContainer: SELECTORS.page_container, dataKey: key }
  );
}

/**
 * Wait until the level text actually CHANGES (not just exists).
 *
 * Falls back to a short fixed wait if the level text is unavailable.
 */
export async function waitForLevelChange(
  page: Page,
  timeout: number = TIMEOUTS.click_wait
): Promise<void> {
  let oldLevel = "";
  try {
    oldLevel = await page
      .locator(SELECTORS.level_text)
      .innerText({ timeout: 500 });
  } catch {
    oldLevel = "";
  }

  try {
    await page.waitForFunction(
      ({ selector, oldText }) => {
        const el = document.querySelector(selector);
        if (!el) return false;
        const text = (el.textContent ?? "").trim();
        return text.length > 0 && text !== oldText;
      },
      { selector: SELECTORS.level_text, oldText: oldLevel },
      { timeout }
    );
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }
}

/**
 * Click the Verify button and wait for the next level to load.
 */
export async function clickVerify(
  page: Page,
  levelName: string
): Promise<void> {
  await page.locator(SELECTORS.verify_btn).click();
  await waitForLevelChange(page);
  logger.info(`[${levelName}] Verify clicked.`);
}

/**
 * Wait for the first element matching the selector to be visible.
 */
export async function waitForGrid(
  page: Page,
  selector: string,
  timeout: number = TIMEOUTS.vue_condition
): Promise<void> {
  await page.locator(selector).first().waitFor({ state: "visible", timeout });
}

/**
 * Wait until a Vue condition is true.
 *
 * @param page - Playwright page object.
 * @param key - A key present in the target component's $data.
 * @param condition - JS expression using `inst` (the component).
 */
export async function waitForVue(
  page: Page,
  key: string,
  condition: string,
  timeout: number = TIMEOUTS.vue_condition
): Promise<void> {
  await page.waitForFunction(
    ({ pageContainer, dataKey, cond }) => {
      const el = document.querySelector(pageContainer);
      const pageVm = (el as any)?.__vue__;
      if (!pageVm) return false;
      const inst = pageVm.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data()[dataKey] !== undefined
      );
      // eslint-disable-next-line no-new-func
      return inst && new Function("inst", `return (${cond});`)(inst);
    },
    { pageContainer: SELECTORS.page_container, dataKey: key, cond: condition },
    { timeout }
  );
}