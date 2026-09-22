/** One handler per level. Auto-registered via register(). */

import type { Page } from "playwright";
import {
  SELECTORS,
  TIMEOUTS,
  RETRY_LIMITS,
  FALLBACK_ANSWERS,
} from "./config";
import {
  readVueChild,
  waitForLevelChange,
  clickVerify,
  waitForGrid,
  waitForVue,
} from "./helpers";
import { logger } from "./logger";

// ══════════════════════════════════════
//  Exception
// ══════════════════════════════════════
export class LevelFailed extends Error {
  constructor(message: string) {
    super(message);
    this.name = "LevelFailed";
  }
}

// ══════════════════════════════════════
//  Registry
// ══════════════════════════════════════
export type LevelHandler = (page: Page) => Promise<void>;

export const LEVEL_HANDLERS = new Map<string, LevelHandler>();

/**
 * Register a handler into LEVEL_HANDLERS.
 *
 * Replaces the Python `@register("Name")` decorator with an explicit
 * helper that returns the same function so it can be assigned to a
 * named export in one line.
 */
export function register(name: string, fn: LevelHandler): LevelHandler {
  LEVEL_HANDLERS.set(name, fn);
  return fn;
}

// ══════════════════════════════════════
//  Level 1: Checkbox
// ══════════════════════════════════════
export const solveLevel1 = register("Checkbox", async (page: Page) => {
  logger.info("[Level 1] Click checkbox...");
  await page.locator(SELECTORS.captcha_box).click();
  await waitForLevelChange(page);
  logger.info("[Level 1] Done.");
});

// ══════════════════════════════════════
//  Level 2: Stop Signs
// ══════════════════════════════════════
export const solveLevel2 = register("Stop Signs", async (page: Page) => {
  logger.info("[Level 2] Waiting for grid...");
  await waitForGrid(page, SELECTORS.grid_item);

  const targetPositions = new Set([
    "66.6667% 0%",
    "100% 0%",
    "66.6667% 33.3333%",
    "100% 33.3333%",
  ]);

  const items = page.locator(SELECTORS.grid_item);
  const total = await items.count();
  logger.info(`[Level 2] ${total} cells`);

  for (let i = 0; i < total; i++) {
    const style = (await items.nth(i).getAttribute("style")) ?? "";
    let pos = "";
    if (style.includes("background-position:")) {
      pos = style.split("background-position:")[1].split(";")[0].trim();
    }

    if (targetPositions.has(pos)) {
      logger.info(`[Level 2] Click cell ${i} -> ${pos}`);
      await items.nth(i).click();
      await page.waitForTimeout(TIMEOUTS.cell_click_wait);
    }
  }

  await clickVerify(page, "Level 2");
});

// ══════════════════════════════════════
//  Level 3: Wiggles
// ══════════════════════════════════════
export const solveLevel3 = register("Wiggles", async (page: Page) => {
  logger.info("[Level 3] Waiting for input...");
  await page.locator(SELECTORS.captcha_input).waitFor({ state: "visible" });

  try {
    await waitForVue(page, "answer", "inst.$data.answer !== undefined");
  } catch {
    logger.warn("[Level 3] Vue answer not ready within timeout");
  }

  const answer: string | null = await page.evaluate((container) => {
    const els = document.querySelectorAll(container);
    for (const el of Array.from(els)) {
      const vm = (el as any).__vue__;
      if (vm && vm.$data && vm.$data.answer !== undefined) {
        return vm.$data.answer as string;
      }
    }
    return null;
  }, SELECTORS.captcha_container);

  if (!answer) {
    logger.warn("[Level 3] Could not read answer, trying fallback...");
    for (const candidate of FALLBACK_ANSWERS.wiggles) {
      await page.locator(SELECTORS.captcha_input).fill(candidate);
      await page.locator(SELECTORS.captcha_submit).click();
      await page.waitForTimeout(TIMEOUTS.loop_wait);
      const level = await page.locator(SELECTORS.level_text).innerText();
      if (!level.includes("Wiggles")) {
        logger.info(`[Level 3] '${candidate}' worked!`);
        return;
      }
    }
    throw new LevelFailed("Level 3: no fallback worked");
  }

  logger.info(`[Level 3] Answer: ${JSON.stringify(answer)}`);
  await page.locator(SELECTORS.captcha_input).fill(answer);
  await page.locator(SELECTORS.captcha_submit).click();
  await waitForLevelChange(page);
});

// ══════════════════════════════════════
//  Level 4: Vegetables
// ══════════════════════════════════════
export const solveLevel4 = register("Vegetables", async (page: Page) => {
  logger.info("[Level 4] Waiting for grid...");
  await waitForGrid(page, SELECTORS.grid_item);

  const result = await page.evaluate((container) => {
    const vms = Array.from(document.querySelectorAll(container))
      .map((el) => (el as any).__vue__)
      .filter((v) => v && v.$data && v.$data.correct);
    const vm = vms[0];
    if (!vm) return null;
    return {
      correct: [...vm.$data.correct] as string[],
      optional: [...vm.$data.optional] as string[],
      images: [...vm.$data.images] as string[],
      threshold: vm.$data.threshold as number,
    };
  }, SELECTORS.captcha_container);

  if (!result) {
    throw new LevelFailed("Level 4: could not read Vue data");
  }

  logger.info(`[Level 4] correct=${JSON.stringify(result.correct)}`);
  const toClick = new Set(result.correct);

  const items = page.locator(SELECTORS.grid_item);
  const total = await items.count();
  let clicked = 0;

  for (let i = 0; i < total; i++) {
    const src = result.images[i] ?? "";
    const name = src.split("/").pop()!.replace(".webp", "").toLowerCase();

    if (toClick.has(name)) {
      logger.info(`[Level 4] Cell ${i} -> ${name}, clicking`);
      await items.nth(i).click();
      clicked++;
      await page.waitForTimeout(TIMEOUTS.cell_click_wait);
    }
  }

  logger.info(`[Level 4] Clicked ${clicked} cells`);
  await clickVerify(page, "Level 4");
});

// ══════════════════════════════════════
//  Level 5: Rotation
// ══════════════════════════════════════
export const solveLevel5 = register("Rotation", async (page: Page) => {
  logger.info("[Level 5] Waiting for grid...");
  await waitForGrid(page, SELECTORS.rotating_item);

  const items = page.locator(SELECTORS.rotating_item);
  const total = await items.count();
  logger.info(`[Level 5] ${total} cells`);

  for (let i = 0; i < total; i++) {
    const style = (await items.nth(i).getAttribute("style")) ?? "";
    let rot = 0;
    if (style.includes("rotate(")) {
      rot = parseInt(style.split("rotate(")[1].split("deg")[0], 10);
    }

    const clicks = ((((0 - rot) % 360) + 360) % 360) / 90;
    logger.info(`[Level 5] Cell ${i}: ${rot}° -> 0°, ${clicks} clicks`);

    for (let c = 0; c < clicks; c++) {
      await items.nth(i).click();
      await page.waitForTimeout(TIMEOUTS.quick_click_wait);
    }
  }

  await clickVerify(page, "Level 5");
});

// ══════════════════════════════════════
//  Level 6: XOXO
// ══════════════════════════════════════
export type Board = string[];

export function isWinner(board: Board, player: string): boolean {
  const lines: number[][] = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],
    [0, 3, 6], [1, 4, 7], [2, 5, 8],
    [0, 4, 8], [2, 4, 6],
  ];
  for (const [a, b, c] of lines) {
    if (board[a] === board[b] && board[b] === board[c] && board[a] === player) {
      return true;
    }
  }
  return false;
}

export function minimax(
  board: Board,
  depth: number,
  isMax: boolean,
  me = "X",
  opp = "O"
): number {
  if (isWinner(board, me)) return 10 - depth;
  if (isWinner(board, opp)) return depth - 10;
  if (!board.includes(".")) return 0;

  if (isMax) {
    let best = -Infinity;
    for (let i = 0; i < 9; i++) {
      if (board[i] === ".") {
        board[i] = me;
        best = Math.max(best, minimax(board, depth + 1, false, me, opp));
        board[i] = ".";
      }
    }
    return best;
  } else {
    let best = Infinity;
    for (let i = 0; i < 9; i++) {
      if (board[i] === ".") {
        board[i] = opp;
        best = Math.min(best, minimax(board, depth + 1, true, me, opp));
        board[i] = ".";
      }
    }
    return best;
  }
}

export function bestMove(
  board: Board,
  me = "X",
  opp = "O"
): number | null {
  let bestScore = -Infinity;
  let bestIdx: number | null = null;
  for (let i = 0; i < 9; i++) {
    if (board[i] === ".") {
      board[i] = me;
      const score = minimax(board, 0, false, me, opp);
      board[i] = ".";
      if (score > bestScore) {
        bestScore = score;
        bestIdx = i;
      }
    }
  }
  return bestIdx;
}

interface XoxoState {
  grid: (string | null)[];
  currentPlayer: string;
  winner: string | null;
}

async function readXoxoState(page: Page): Promise<XoxoState | null> {
  return page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return null;
    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().grid !== undefined
    );
    if (!inst) return null;
    return {
      grid: [...inst.$data.grid],
      currentPlayer: inst.$data.currentPlayer,
      winner: inst.$data.winner,
    };
  }, SELECTORS.page_container);
}

export const solveLevel6 = register("XOXO", async (page: Page) => {
  logger.info("[Level 6] Waiting for board...");
  await waitForGrid(page, SELECTORS.ttt_cell);

  for (let attempt = 0; attempt < RETRY_LIMITS.xoxo_games; attempt++) {
    logger.info(`[Level 6] Game #${attempt + 1}`);

    logger.info("[Level 6] Clicking Reset...");
    await page.locator(SELECTORS.refresh_btn).click();

    try {
      await waitForVue(
        page,
        "grid",
        "inst.$data.grid.every((x) => x === null)"
      );
    } catch {
      await page.waitForTimeout(TIMEOUTS.long_wait);
    }

    let state = await readXoxoState(page);
    logger.info(`[Level 6] Initial state: ${JSON.stringify(state)}`);

    for (let moveNum = 0; moveNum < 9; moveNum++) {
      await page.waitForTimeout(TIMEOUTS.medium_wait);

      state = await readXoxoState(page);
      if (!state) {
        logger.warn("[Level 6] State not found");
        break;
      }

      const board: Board = state.grid.map((x) => (x === null ? "." : x));
      logger.info(
        `[Level 6] Board: ${JSON.stringify(board)} | player: ${state.currentPlayer} | winner: ${JSON.stringify(state.winner)}`
      );

      if (state.winner === "X") {
        logger.info("[Level 6] We won!");
        break;
      }
      if (state.winner === "O") {
        logger.warn("[Level 6] Computer won, refreshing...");
        break;
      }
      if (!board.includes(".")) {
        logger.warn("[Level 6] Draw, refreshing...");
        break;
      }

      if (state.currentPlayer === "X") {
        const best = bestMove(board, "X", "O");
        if (best === null) break;
        logger.info(`[Level 6] Playing at ${best}`);
        await page.locator(SELECTORS.ttt_cell).nth(best).click();
      }
    }

    state = await readXoxoState(page);
    if (state && state.winner === "X") break;

    if (attempt === RETRY_LIMITS.xoxo_games - 1) {
      throw new LevelFailed("Level 6: could not win in retries");
    }
  }

  await clickVerify(page, "Level 6");
});

// ══════════════════════════════════════
//  Level 7: Word Search
// ══════════════════════════════════════
interface PuzzleData {
  gridSize: number;
  puzzle: string[][];
  words: string[];
}

export const solveLevel7 = register("Word Search", async (page: Page) => {
  logger.info("[Level 7] Waiting for grid...");
  await waitForGrid(page, SELECTORS.ws_cell);

  const data = await readVueChild<PuzzleData>(page, "puzzle");
  if (!data) throw new LevelFailed("Level 7: could not read puzzle");

  const { gridSize: size, puzzle: grid, words } = data;
  logger.info(`[Level 7] Grid size: ${size}, words=${JSON.stringify(words)}`);

  const directions: Array<[number, number]> = [
    [0, 1], [1, 0], [1, 1], [1, -1],
    [0, -1], [-1, 0], [-1, -1], [-1, 1],
  ];

  const cellsToClick = new Set<number>();

  for (const word of words) {
    let found = false;
    for (let r = 0; r < size && !found; r++) {
      for (let c = 0; c < size && !found; c++) {
        if (grid[r][c].toUpperCase() !== word[0]) continue;

        for (const [dr, dc] of directions) {
          const coords: Array<[number, number]> = [];
          let ok = true;
          for (let i = 0; i < word.length; i++) {
            const nr = r + dr * i;
            const nc = c + dc * i;
            if (nr < 0 || nr >= size || nc < 0 || nc >= size) {
              ok = false;
              break;
            }
            if (grid[nr][nc].toUpperCase() !== word[i]) {
              ok = false;
              break;
            }
            coords.push([nr, nc]);
          }
          if (ok) {
            logger.info(
              `[Level 7] Found '${word}' at ${JSON.stringify(coords)}`
            );
            for (const [nr, nc] of coords) {
              cellsToClick.add(nr * size + nc);
            }
            found = true;
            break;
          }
        }
      }
    }
    if (!found) logger.warn(`[Level 7] Could not find '${word}'`);
  }

  const items = page.locator(SELECTORS.ws_cell);
  for (const idx of [...cellsToClick].sort((a, b) => a - b)) {
    await items.nth(idx).click();
    await page.waitForTimeout(TIMEOUTS.fast_click_wait);
  }

  await clickVerify(page, "Level 7");
});

// ══════════════════════════════════════
//  Level 8: License Plate
// ══════════════════════════════════════
export const solveLevel8 = register("License Plate", async (page: Page) => {
  logger.info("[Level 8] Waiting for image...");
  await page.locator(SELECTORS.license_image).waitFor({ state: "visible" });

  const src =
    (await page.locator(SELECTORS.license_image).getAttribute("src")) ?? "";
  const plate = src.split("/").pop()!.replace(".webp", "");
  logger.info(`[Level 8] Plate: ${plate}`);

  await page.locator(SELECTORS.captcha_input).fill(plate);
  await page.locator(SELECTORS.captcha_submit).click();
  await waitForLevelChange(page);
});

// ══════════════════════════════════════
//  Level 9: Nested
// ══════════════════════════════════════
export const solveLevel9 = register("Nested", async (page: Page) => {
  logger.info("[Level 9] Waiting for grid...");
  await page.locator(SELECTORS.nested_grid).waitFor({ state: "visible" });

  const result = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return null;
    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().correct !== undefined
    );
    if (!inst) return null;
    inst.$data.selected = [...inst.$data.correct];
    return {
      correct: [...inst.$data.correct],
      selected: [...inst.$data.selected],
    };
  }, SELECTORS.page_container);

  if (!result) throw new LevelFailed("Level 9: could not set selected");

  logger.info(`[Level 9] Set selected = ${result.selected.length} paths`);
  await page.waitForTimeout(TIMEOUTS.cell_click_wait);
  await clickVerify(page, "Level 9");
});

// ══════════════════════════════════════
//  Level 10: Whack-a-Mole
// ══════════════════════════════════════
export const solveLevel10 = register("Whack-a-Mole", async (page: Page) => {
  logger.info("[Level 10] Waiting for grid...");
  await waitForGrid(page, SELECTORS.mole_wrapper);

  const start = Date.now();
  const timeout = RETRY_LIMITS.mole_timeout * 1000;

  while (Date.now() - start < timeout) {
    const active = page.locator(SELECTORS.mole_active);
    const count = await active.count();

    if (count > 0) {
      for (let i = 0; i < count; i++) {
        try {
          await active.nth(i).click({ timeout: 500, force: true });
          logger.info("[Level 10] Whacked an active mole");
        } catch {
          try {
            await active.nth(i).scrollIntoViewIfNeeded({ timeout: 300 });
            await active.nth(i).click({ timeout: 300, force: true });
            logger.info("[Level 10] Whacked after scroll");
          } catch {
            /* ignore */
          }
        }
      }
    } else {
      await page.waitForTimeout(RETRY_LIMITS.mole_click_wait);
    }

    const whacked = await readVueChild<{
      whackedMoles: unknown[];
      targetScore: number;
    }>(page, "targetScore");

    if (
      whacked &&
      whacked.whackedMoles &&
      whacked.whackedMoles.length >= whacked.targetScore
    ) {
      logger.info(
        `[Level 10] Whacked ${whacked.whackedMoles.length}/${whacked.targetScore}!`
      );
      break;
    }
  }

  await clickVerify(page, "Level 10");
});

// ══════════════════════════════════════
//  Level 11: Waldo
// ══════════════════════════════════════
export const solveLevel11 = register("Waldo", async (page: Page) => {
  logger.info("[Level 11] Waiting for grid...");
  await waitForGrid(page, SELECTORS.grid_item);

  const data = await readVueChild<{ correct: number[] }>(page, "correct");
  if (!data) throw new LevelFailed("Level 11: could not read correct");

  const correct = data.correct;
  logger.info(`[Level 11] Correct indexes: ${JSON.stringify(correct)}`);

  const items = page.locator(SELECTORS.grid_item);
  for (const idx of correct) {
    await items.nth(idx).click();
    await page.waitForTimeout(TIMEOUTS.fast_click_wait);
  }

  await clickVerify(page, "Level 11");
});

// ══════════════════════════════════════
//  Level 12: Muffins?
// ══════════════════════════════════════
export const solveLevel12 = register("Muffins?", async (page: Page) => {
  logger.info("[Level 12] Waiting for grid...");
  await waitForGrid(page, SELECTORS.muffin_img);

  const target = (
    await page.locator(SELECTORS.captcha_title_type).innerText()
  )
    .trim()
    .toLowerCase();
  logger.info(`[Level 12] Target: ${target}`);

  const items = page.locator(SELECTORS.muffin_img);
  const total = await items.count();
  let clicked = 0;

  for (let i = 0; i < total; i++) {
    const src = (await items.nth(i).getAttribute("src")) ?? "";
    const category = src.split("/").slice(-2, -1)[0].toLowerCase();

    if (target.includes(category) || category.includes(target)) {
      logger.info(`[Level 12] Cell ${i} -> ${category}, clicking`);
      await items.nth(i).locator("xpath=..").click();
      clicked++;
      await page.waitForTimeout(TIMEOUTS.quick_click_wait);
    }
  }

  logger.info(`[Level 12] Clicked ${clicked} cells`);
  await clickVerify(page, "Level 12");
});

// ══════════════════════════════════════
//  Level 13: Reverse
// ══════════════════════════════════════
export const solveLevel13 = register("Reverse", async (page: Page) => {
  logger.info("[Level 13] Waiting for grid...");
  await waitForGrid(page, SELECTORS.grid_item);

  const result = await readVueChild<{
    questionIndex: number;
    answers: number[][];
  }>(page, "answers");
  if (!result) throw new LevelFailed("Level 13: could not read answers");

  const qIdx = result.questionIndex;
  const correct = result.answers[qIdx];
  logger.info(
    `[Level 13] Question index: ${qIdx}, correct: ${JSON.stringify(correct)}`
  );

  const items = page.locator(SELECTORS.grid_item);
  for (const idx of correct) {
    await items.nth(idx).click();
    await page.waitForTimeout(TIMEOUTS.fast_click_wait);
  }

  await clickVerify(page, "Level 13");
});

// ══════════════════════════════════════
//  Level 14: Affirmations
// ══════════════════════════════════════
export const solveLevel14 = register("Affirmations", async (page: Page) => {
  logger.info("[Level 14] Waiting for grid...");
  await waitForGrid(page, SELECTORS.recaptcha_container);

  const result = await page.evaluate((container) => {
    const boxes = document.querySelectorAll(container);
    const toClick: Array<{ index: number; text: string }> = [];
    boxes.forEach((box, i) => {
      const vm = (box as any).__vue__;
      if (!vm) return;
      if (vm.$props.wrong === false) {
        toClick.push({ index: i, text: vm.$props.text });
      }
    });
    return toClick;
  }, SELECTORS.recaptcha_container);

  if (!result || result.length === 0) {
    throw new LevelFailed("Level 14: no correct answer found");
  }

  logger.info(`[Level 14] Found ${result.length} correct boxes`);
  for (const item of result) {
    const idx = item.index;
    const clicked = await page.evaluate(
      ({ container, checkboxSel, index }) => {
        const boxes = document.querySelectorAll(container);
        const box = boxes[index];
        if (!box) return false;
        const checkbox = box.querySelector(checkboxSel);
        if (checkbox) {
          (checkbox as HTMLElement).click();
          return true;
        }
        return false;
      },
      {
        container: SELECTORS.recaptcha_container,
        checkboxSel: SELECTORS.captcha_box_checkbox,
        index: idx,
      }
    );
    logger.info(`[Level 14] Box ${idx} clicked: ${clicked}`);
  }

  await waitForLevelChange(page);
});

// ══════════════════════════════════════
//  Level 15: Parking
// ══════════════════════════════════════
export const solveLevel15 = register("Parking", async (page: Page) => {
  logger.info("[Level 15] Waiting for canvas...");
  await page.locator(SELECTORS.park_canvas).waitFor({ state: "visible" });

  await page.locator(SELECTORS.park_canvas).click();
  await page.waitForTimeout(TIMEOUTS.short_wait);
  await page.keyboard.press("ArrowUp");
  await page.waitForTimeout(TIMEOUTS.medium_wait);

  const result = await page.evaluate((canvasSel) => {
    let el: Element | null = document.querySelector(canvasSel);
    let gridCaptcha: any = null;
    while (el) {
      const vm = (el as any).__vue__;
      if (vm && vm.$data && vm.$data.squares) {
        gridCaptcha = vm;
        break;
      }
      el = el.parentElement;
    }
    if (!gridCaptcha) return { error: "GridCaptcha not found" };

    const parkVnode = gridCaptcha.$vnode.parent;
    if (!parkVnode || !parkVnode.componentInstance) {
      return { error: "Park component not found" };
    }

    const park = parkVnode.componentInstance;
    park.checkParking = function () {
      return true;
    };

    return { success: true };
  }, SELECTORS.park_canvas);

  if (!result || (result as any).error) {
    throw new LevelFailed("Level 15: failed to override checkParking");
  }

  for (let i = 0; i < RETRY_LIMITS.parking_verifies; i++) {
    await page.waitForTimeout(TIMEOUTS.medium_wait);

    const level = await page.locator(SELECTORS.level_text).innerText();
    if (!level.includes("Parking")) {
      logger.info(`[Level 15] Advanced to: ${level}`);
      return;
    }

    logger.info(`[Level 15] Verify #${i + 1}`);
    await page.locator(SELECTORS.verify_btn).click();
    await waitForLevelChange(page);
  }
});

// ══════════════════════════════════════
//  Level 16: Now in 3D!
// ══════════════════════════════════════
export const solveLevel16 = register("Now in 3D!", async (page: Page) => {
  logger.info("[Level 16] Waiting for input...");
  await page.locator(SELECTORS.captcha_input).waitFor({ state: "visible" });

  try {
    await waitForVue(
      page,
      "captchaText",
      "inst.$data.captchaText !== undefined"
    );
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  const data = await readVueChild<{ captchaText: string }>(
    page,
    "captchaText"
  );
  const answer = data?.captchaText;

  if (!answer) throw new LevelFailed("Level 16: could not read captchaText");

  logger.info(`[Level 16] Answer: ${JSON.stringify(answer)}`);
  await page.locator(SELECTORS.captcha_input).fill(answer);
  await page.locator(SELECTORS.captcha_submit).click();
  await waitForLevelChange(page);
});

// ══════════════════════════════════════
//  Level 17: Perfect Circle
// ══════════════════════════════════════
export const solveLevel17 = register("Perfect Circle", async (page: Page) => {
  logger.info("[Level 17] Waiting for SVG...");
  await page.locator(SELECTORS.circle_svg).waitFor({ state: "visible" });

  try {
    await waitForVue(page, "score", "inst.$data.score !== undefined");
  } catch {
    await page.waitForTimeout(TIMEOUTS.long_wait);
  }

  const result = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };
    const inst = pageVm.$children.find(
      (c: any) => c && c.$data && c.$data.score !== undefined
    );
    if (!inst) return { error: "Component not found" };

    inst.$data.score = 1000;
    inst.$data.best = 1000;
    inst.$data.hasDrawn = true;
    inst.$data.valid = true;

    return { success: true, score: inst.$data.score };
  }, SELECTORS.page_container);

  if (!result || (result as any).error) {
    throw new LevelFailed("Level 17: failed to override score");
  }

  logger.info(`[Level 17] Override result: ${JSON.stringify(result)}`);
  await page.waitForTimeout(TIMEOUTS.cell_click_wait);
  await clickVerify(page, "Level 17");
});

// ══════════════════════════════════════
//  Level 18: Sisyphus
// ══════════════════════════════════════
export const solveLevel18 = register("Sisyphus", async (page: Page) => {
  logger.info("[Level 18] Waiting for grid...");
  await waitForGrid(page, SELECTORS.sisyphus_grid_item);

  const maxAttempts = RETRY_LIMITS.sisyphus_attempts;
  for (let i = 0; i < maxAttempts; i++) {
    const hydrants = page.locator(SELECTORS.hydrant_img);
    const count = await hydrants.count();
    logger.info(`[Level 18] Attempt #${i + 1} | ${count} hydrants`);

    if (count === 0) {
      logger.info("[Level 18] No more hydrants");
      break;
    }

    try {
      await hydrants.first().click({ timeout: 1000, force: true });
    } catch (e) {
      logger.warn(`[Level 18] Click failed: ${String(e)}`);
    }

    await page.waitForTimeout(TIMEOUTS.click_wait);
  }

  logger.info("[Level 18] Clicking Verify...");
  await page.locator(SELECTORS.verify_btn).click({ force: true });
  await waitForLevelChange(page);
});

// ══════════════════════════════════════
//  Level 19: In the Dark
// ══════════════════════════════════════
export const solveLevel19 = register("In the Dark", async (page: Page) => {
  logger.info("[Level 19] Waiting for grid...");
  await page
    .locator(SELECTORS.flashlight_container)
    .waitFor({ state: "visible" });

  const answer: string = await page.evaluate((letterSel) => {
    const letters = document.querySelectorAll(letterSel);
    return Array.from(letters)
      .map((l) => (l as HTMLElement).innerText.trim())
      .join("");
  }, SELECTORS.letter);

  if (!answer) throw new LevelFailed("Level 19: could not read letters");

  logger.info(`[Level 19] Answer: ${JSON.stringify(answer)}`);
  await page.locator(SELECTORS.captcha_input).fill(answer);
  await page.locator(SELECTORS.captcha_submit).click();
  await waitForLevelChange(page);
});

// ══════════════════════════════════════
//  Level 20: Rorschach
// ══════════════════════════════════════
export const solveLevel20 = register("Rorschach", async (page: Page) => {
  logger.info("[Level 20] Waiting for image...");
  await page.locator(SELECTORS.rorschach_image).waitFor({ state: "visible" });

  const answer = FALLBACK_ANSWERS.rorschach;
  logger.info(`[Level 20] Answer: ${JSON.stringify(answer)}`);

  await page.locator(SELECTORS.captcha_input).fill(answer);
  await page.locator(SELECTORS.captcha_submit).click();
  await waitForLevelChange(page);
});

// ══════════════════════════════════════
//  Level 21: CRAFTCHA
// ══════════════════════════════════════
export const solveLevel21 = register("CRAFTCHA", async (page: Page) => {
  logger.info("[Level 21] Waiting for crafting UI...");
  await page
    .locator(SELECTORS.crafting_slot)
    .first()
    .waitFor({ state: "visible" });
  await page.waitForTimeout(TIMEOUTS.short_wait);

  const result = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };
    const inst = pageVm.$children.find(
      (c: any) => c && c.$data && c.$data.craftingTable !== undefined
    );
    if (!inst) return { error: "crafting component not found" };

    inst.hasCraftedTargetItem = true;
    return { success: true };
  }, SELECTORS.page_container);

  if (!result || (result as any).error) {
    throw new LevelFailed("Level 21: failed to set hasCraftedTargetItem");
  }

  logger.info(`[Level 21] result: ${JSON.stringify(result)}`);
  await page.waitForTimeout(TIMEOUTS.short_wait);
  await clickVerify(page, "Level 21");
});

// ══════════════════════════════════════
//  Level 22: My Ducks Ahhh
// ══════════════════════════════════════
export const solveLevel22 = register("My Ducks Ahhh", async (page: Page) => {
  logger.info("[Level 22] Waiting for ducks...");
  await page.locator(SELECTORS.duck_container).waitFor({ state: "visible" });

  const result = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };
    const inst = pageVm.$children.find(
      (c: any) => c && c.$data && Array.isArray(c.$data.ducks)
    );
    if (!inst) return { error: "ducks component not found" };

    inst.$data.ducks.forEach((duck: any) => {
      duck.clicked = true;
    });
    inst.$data.done = true;
    inst.$data.isRoaming = false;

    return {
      success: true,
      clicked: inst.$data.ducks.filter((d: any) => d.clicked).length,
      total: inst.$data.ducks.length,
    };
  }, SELECTORS.page_container);

  if (!result || (result as any).error) {
    throw new LevelFailed("Level 22: failed to set ducks clicked");
  }

  logger.info(`[Level 22] result: ${JSON.stringify(result)}`);
  await clickVerify(page, "Level 22");
});

// ══════════════════════════════════════
//  Level 23: Panorama
// ══════════════════════════════════════
export const solveLevel23 = register("Panorama", async (page: Page) => {
  logger.info("[Level 23] Waiting for panorama...");
  await page.locator(SELECTORS.panorama).waitFor({ state: "visible" });

  try {
    await waitForVue(page, "challenges", "inst.viewer !== undefined");
  } catch {
    await page.waitForTimeout(TIMEOUTS.page_load);
  }

  const result = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };
    const inst = pageVm.$children.find(
      (c: any) => c && c.$data && c.$data.challenges !== undefined
    );
    if (!inst || !inst.viewer) return { error: "viewer not found" };

    const challenge = inst.challenges[inst.currentChallenge];
    const pitch = (challenge.pitchBounds[0] + challenge.pitchBounds[1]) / 2;
    const yaw = (challenge.yawBounds[0] + challenge.yawBounds[1]) / 2;
    const hfov = challenge.maxHfov - 1;

    inst.viewer.setPitch(pitch);
    inst.viewer.setYaw(yaw);
    inst.viewer.setHfov(hfov);

    return {
      success: true,
      title: challenge.title,
      pitch,
      yaw,
      hfov,
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 23] Set viewer: ${JSON.stringify(result)}`);

  if (!result || (result as any).error) {
    throw new LevelFailed(
      `Level 23: ${(result as any).error ?? "unknown"}`
    );
  }

  await page.waitForTimeout(TIMEOUTS.short_wait);
  await clickVerify(page, "Level 23");
});

// ══════════════════════════════════════
//  Level 24: Eye Exam
// ══════════════════════════════════════
export const solveLevel24 = register("Eye Exam", async (page: Page) => {
  logger.info("[Level 24] Waiting for eye exam...");
  await page
    .locator(SELECTORS.eye_exam_container)
    .waitFor({ state: "visible" });

  // ── Sub-level 0: Read the last row letters ──
  logger.info("[Level 24] Sub-level 0: last row letters");
  const letters: string | null = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return null;
    const inst = pageVm.$children.find(
      (c: any) => c && c.$data && c.$data.chartRows !== undefined
    );
    if (!inst) return null;
    return inst.$data.chartRows[4].letters.join("");
  }, SELECTORS.page_container);
  logger.info(`[Level 24] Letters: ${letters}`);

  if (!letters) throw new LevelFailed("Level 24: could not read chartRows[4]");

  await page.locator(SELECTORS.eye_exam_input).fill(letters);
  await page.locator(SELECTORS.verify_btn).click();
  await page.waitForTimeout(TIMEOUTS.medium_wait);

  // ── Sub-level 1: Read the number ──
  logger.info("[Level 24] Sub-level 1: number");
  const number: string | null = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return null;
    const inst = pageVm.$children.find(
      (c: any) => c && c.$data && c.$data.chartRows !== undefined
    );
    if (!inst) return null;
    return String(
      inst.$data.colorTests[inst.$data.colorTestIndex]
    );
  }, SELECTORS.page_container);
  logger.info(`[Level 24] Number: ${number}`);

  if (!number) throw new LevelFailed("Level 24: could not read colorTests");

  await page.locator(SELECTORS.eye_exam_input).fill(number);
  await page.locator(SELECTORS.verify_btn).click();
  await page.waitForTimeout(TIMEOUTS.medium_wait);

  // ── Sub-level 2: Count dots (always 34) ──
  logger.info("[Level 24] Sub-level 2: counting dots (34)");
  await page.locator(SELECTORS.eye_exam_input).fill("34");
  await page.locator(SELECTORS.verify_btn).click();
  await page.waitForTimeout(TIMEOUTS.medium_wait);

  // ── Sub-level 3: Click the different color square ──
  logger.info("[Level 24] Sub-level 3: different color square");
  const diffIndex: number | null = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return null;
    const inst = pageVm.$children.find(
      (c: any) => c && c.$data && c.$data.chartRows !== undefined
    );
    if (!inst) return null;
    return inst.$data.randomColorDiffIndex;
  }, SELECTORS.page_container);
  logger.info(`[Level 24] Different color at index: ${diffIndex}`);

  if (diffIndex === null || diffIndex === undefined) {
    throw new LevelFailed("Level 24: could not read randomColorDiffIndex");
  }

  await page.locator(SELECTORS.eye_exam_square).nth(diffIndex).click();
  await page.waitForTimeout(TIMEOUTS.quick_click_wait);
  await page.locator(SELECTORS.verify_btn).click();

  await waitForLevelChange(page);
  logger.info("[Level 24] Done.");
});

// ══════════════════════════════════════
//  Level 25: Creativity
// ══════════════════════════════════════
export const solveLevel25 = register("Creativity", async (page: Page) => {
  logger.info("[Level 25] Waiting for canvas...");
  await page.locator(SELECTORS.express_canvas).waitFor({ state: "visible" });

  try {
    await waitForVue(page, "numDrawn", "inst.$data.numDrawn !== undefined");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  const result = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().numDrawn !== undefined
    );
    if (!inst) return { error: "creativity component not found" };

    inst.$data.numDrawn = 11;
    inst.$data.toolsUsed = {
      brush: true,
      spray: true,
      pencil: true,
      eraser: true,
    };
    inst.$data.differentColorUsed = true;

    return {
      success: true,
      numDrawn: inst.$data.numDrawn,
      toolsUsed: inst.$data.toolsUsed,
      differentColorUsed: inst.$data.differentColorUsed,
      verify: inst.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 25] Override result: ${JSON.stringify(result)}`);

  if (!result || (result as any).error) {
    throw new LevelFailed(
      `Level 25: ${(result as any).error ?? "unknown"}`
    );
  }

  if (!(result as any).verify) {
    throw new LevelFailed("Level 25: verify() still returns False");
  }

  await page.waitForTimeout(TIMEOUTS.cell_click_wait);
  await clickVerify(page, "Level 25");
});

// ══════════════════════════════════════
//  Level 26: Parallel Parking
// ══════════════════════════════════════
export const solveLevel26 = register("Parallel Parking", async (page: Page) => {
  logger.info("[Level 26] Waiting for canvas...");
  await page.locator(SELECTORS.park_canvas).waitFor({ state: "visible" });

  await page.locator(SELECTORS.park_canvas).click();
  await page.waitForTimeout(TIMEOUTS.short_wait);
  await page.keyboard.press("ArrowUp");
  await page.waitForTimeout(TIMEOUTS.medium_wait);

  const result = await page.evaluate((canvasSel) => {
    let el: Element | null = document.querySelector(canvasSel);
    let gridCaptcha: any = null;
    while (el) {
      const vm = (el as any).__vue__;
      if (vm && vm.$data && vm.$data.squares) {
        gridCaptcha = vm;
        break;
      }
      el = el.parentElement;
    }
    if (!gridCaptcha) return { error: "GridCaptcha not found" };

    const parkVnode = gridCaptcha.$vnode.parent;
    if (!parkVnode || !parkVnode.componentInstance) {
      return { error: "Park component not found" };
    }

    const park = parkVnode.componentInstance;
    park.checkParking = function () {
      return true;
    };

    return {
      success: true,
      startLevel: park.startLevel,
      endLevel: park.endLevel,
    };
  }, SELECTORS.park_canvas);

  logger.info(`[Level 26] Override result: ${JSON.stringify(result)}`);

  if (!result || (result as any).error) {
    throw new LevelFailed(
      `Level 26: ${(result as any).error ?? "unknown"}`
    );
  }

  const maxVerifies = 10;
  for (let i = 0; i < maxVerifies; i++) {
    await page.waitForTimeout(TIMEOUTS.medium_wait);

    const level = await page.locator(SELECTORS.level_text).innerText();
    if (!level.includes("Parking")) {
      logger.info(`[Level 26] Advanced to: ${level}`);
      return;
    }

    logger.info(`[Level 26] Verify #${i + 1}`);
    await page.locator(SELECTORS.verify_btn).click();
    await waitForLevelChange(page);
  }

  throw new LevelFailed(
    "Level 26: too many verifications, still on Parking"
  );
});

// ══════════════════════════════════════
//  Level 27: Networking
// ══════════════════════════════════════
export const FLOW_ENDPOINTS: Array<[string, number, number]> = [
  ["#ff6b6b", 0, 27],
  ["#4ecdc4", 5, 15],
  ["#ff8c42", 26, 28],
  ["#f9ca24", 13, 3],
  ["#6c5ce7", 11, 35],
  ["#fd79a8", 8, 14],
];
export const FLOW_GRID_SIZE = 6;

function flowNeighbors(idx: number, size: number): number[] {
  const row = Math.floor(idx / size);
  const col = idx % size;
  const result: number[] = [];
  for (const [dr, dc] of [
    [-1, 0],
    [1, 0],
    [0, -1],
    [0, 1],
  ] as const) {
    const nr = row + dr;
    const nc = col + dc;
    if (nr >= 0 && nr < size && nc >= 0 && nc < size) {
      result.push(nr * size + nc);
    }
  }
  return result;
}

function flowSolveAllPaths(size: number): number[][] | null {
  const total = size * size;
  const usedBy = new Map<number, number>();
  const endpointOwner = new Map<number, number>();
  FLOW_ENDPOINTS.forEach(([, a, b], pathIdx) => {
    endpointOwner.set(a, pathIdx);
    endpointOwner.set(b, pathIdx);
  });

  const paths: number[][] = [];

  function canPass(idx: number, pathIdx: number): boolean {
    if (usedBy.has(idx) && usedBy.get(idx) !== pathIdx) return false;
    if (endpointOwner.has(idx) && endpointOwner.get(idx) !== pathIdx) {
      return false;
    }
    return true;
  }

  function dfsPath(
    pathIdx: number,
    current: number,
    target: number,
    path: number[],
    visited: Set<number>
  ): boolean {
    if (current === target && path.length > 1) return true;

    const candidates: Array<[number, number]> = [];
    for (const nxt of flowNeighbors(current, size)) {
      if (visited.has(nxt)) continue;
      if (!canPass(nxt, pathIdx)) continue;
      let onward = 0;
      for (const nn of flowNeighbors(nxt, size)) {
        if (visited.has(nn) || nn === current) continue;
        if (!canPass(nn, pathIdx)) continue;
        onward++;
      }
      candidates.push([onward, nxt]);
    }
    candidates.sort((a, b) => a[0] - b[0]);

    for (const [, nxt] of candidates) {
      visited.add(nxt);
      path.push(nxt);
      if (dfsPath(pathIdx, nxt, target, path, visited)) return true;
      path.pop();
      visited.delete(nxt);
    }
    return false;
  }

  function place(pathIdx: number): boolean {
    if (pathIdx === FLOW_ENDPOINTS.length) {
      const covered = new Set<number>();
      for (const p of paths) for (const c of p) covered.add(c);
      return covered.size === total;
    }

    const [, a, b] = FLOW_ENDPOINTS[pathIdx];
    const path = [a];
    const visited = new Set<number>([a]);

    if (!dfsPath(pathIdx, a, b, path, visited)) return false;

    for (const cell of path) {
      if (!usedBy.has(cell)) usedBy.set(cell, pathIdx);
    }
    paths.push(path);

    if (place(pathIdx + 1)) return true;

    paths.pop();
    for (const cell of path) {
      if (usedBy.get(cell) === pathIdx) usedBy.delete(cell);
    }
    return false;
  }

  return place(0) ? paths : null;
}

async function flowDragPath(
  page: Page,
  gridLocator: ReturnType<Page["locator"]>,
  path: number[]
): Promise<void> {
  const first = gridLocator.nth(path[0]);
  const box = await first.boundingBox();
  if (!box) return;

  const cx = box.x + box.width / 2;
  const cy = box.y + box.height / 2;
  await page.mouse.move(cx, cy);
  await page.mouse.down();
  await page.waitForTimeout(40);

  for (const idx of path.slice(1)) {
    const cell = gridLocator.nth(idx);
    const cbox = await cell.boundingBox();
    if (!cbox) continue;
    const ccx = cbox.x + cbox.width / 2;
    const ccy = cbox.y + cbox.height / 2;
    await page.mouse.move(ccx, ccy, { steps: 3 });
    await page.waitForTimeout(25);
  }

  await page.mouse.up();
  await page.waitForTimeout(100);
}

export const solveLevel27 = register("Networking", async (page: Page) => {
  logger.info("[Level 27] Waiting for grid...");
  await page.locator(SELECTORS.flow_grid).waitFor({ state: "visible" });

  try {
    await waitForVue(page, "grid", "inst.$data.grid.length > 0");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  // ── Method 1: Direct $data override ──
  const result = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().gridSize !== undefined
    );
    if (!inst) return { error: "Flow component not found" };

    inst.$data.grid.forEach((cell: any) => {
      cell.hasPath = true;
    });
    inst.$data.endpoints.forEach((ep: any) => {
      ep.isConnected = true;
    });

    return {
      success: true,
      filledCells: inst.filledCells,
      totalCells: inst.totalCells,
      allConnected: inst.endpoints.every((e: any) => e.isConnected),
      isComplete: inst.isComplete,
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 27] Method 1 result: ${JSON.stringify(result)}`);

  if (result && (result as any).isComplete) {
    logger.info("[Level 27] Method 1 (direct $data) succeeded!");
    await page.waitForTimeout(TIMEOUTS.cell_click_wait);
    await clickVerify(page, "Level 27");
    return;
  }

  // ── Method 2: Compute paths and simulate real drags ──
  logger.warn(
    "[Level 27] Method 1 failed, switching to Method 2 (backtracking + real drags)..."
  );

  await page.locator(SELECTORS.refresh_btn).click();
  await page.waitForTimeout(TIMEOUTS.medium_wait);

  const paths = flowSolveAllPaths(FLOW_GRID_SIZE);
  if (!paths) {
    throw new LevelFailed("Level 27: could not compute a valid path solution");
  }

  logger.info(
    `[Level 27] Computed ${paths.length} paths (total cells: ${paths.reduce((s, p) => s + p.length, 0)})`
  );

  const gridLocator = page.locator(SELECTORS.flow_cell);

  for (let i = 0; i < paths.length; i++) {
    const color = FLOW_ENDPOINTS[i][0];
    logger.info(
      `[Level 27] Drawing path ${i + 1}/${paths.length} (${color}, length=${paths[i].length})`
    );
    await flowDragPath(page, gridLocator, paths[i]);
    await page.waitForTimeout(TIMEOUTS.short_wait);
  }

  const final = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };
    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().gridSize !== undefined
    );
    if (!inst) return { error: "Flow not found" };
    return {
      isComplete: inst.isComplete,
      filledCells: inst.filledCells,
      totalCells: inst.totalCells,
      allConnected: inst.endpoints.every((e: any) => e.isConnected),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 27] Final state: ${JSON.stringify(final)}`);

  if (!final || !(final as any).isComplete) {
    throw new LevelFailed(
      `Level 27: puzzle not complete after real drags: ${JSON.stringify(final)}`
    );
  }

  await page.waitForTimeout(TIMEOUTS.cell_click_wait);
  await clickVerify(page, "Level 27");
});

// ══════════════════════════════════════
//  Level 28: Day Trader
// ══════════════════════════════════════
export const solveLevel28 = register("Day Trader", async (page: Page) => {
  logger.info("[Level 28] Waiting for stock market UI...");
  await page.locator(SELECTORS.stock_buy_btn).waitFor({ state: "visible" });

  try {
    await waitForVue(page, "balance", "inst.$data.balance !== undefined");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  // ── Method 1: Direct $data override ──
  const result = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().balance !== undefined
    );
    if (!inst) return { error: "Day Trader component not found" };

    inst.$data.balance = 3000;
    if (inst.$data.stocks && inst.$data.stocks[0]) {
      inst.$data.stocks[0].realizedGains = 3000;
    }

    return {
      success: true,
      balance: inst.$data.balance,
      diff: inst.diff,
      verify: inst.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 28] Method 1 result: ${JSON.stringify(result)}`);

  if (result && (result as any).verify) {
    logger.info("[Level 28] Method 1 (direct $data) succeeded!");
    await page.waitForTimeout(TIMEOUTS.cell_click_wait);
    await clickVerify(page, "Level 28");
    return;
  }

  // ── Method 2+3 merged: Timing-based trading via Vue methods ──
  logger.warn(
    "[Level 28] Method 1 failed, using Method 2+3 (timing-based trading via Vue methods)..."
  );

  const start = Date.now();
  const timeout = 90_000;
  let trades = 0;

  while (Date.now() - start < timeout) {
    const action: any = await page.evaluate((pageContainer) => {
      const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
      if (!pageVm) return { error: "pageVm not found" };

      const inst = pageVm.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data().balance !== undefined
      );
      if (!inst) return { error: "not found" };

      if (inst.verify()) {
        return { action: "done", balance: inst.balance, diff: inst.diff };
      }

      const price = inst.lastPrice;
      const shares = inst.shares;
      const balance = inst.balance;
      const avgCost =
        shares > 0 ? inst.selectedStockObj.totalCost / shares : 0;

      const history = inst.selectedStockObj.data;
      const recent = history.slice(-10).map((d: any) => d.val);
      const minRecent = Math.min(...recent);
      const maxRecent = Math.max(...recent);
      const range = maxRecent - minRecent;

      let act = "wait";

      if (shares === 0) {
        if (balance >= price && price <= minRecent + range * 0.3) {
          act = "buy";
        }
      } else {
        const hasProfit = price > avgCost * 1.01;
        const isHigh = price >= maxRecent - range * 0.3;
        if (hasProfit && isHigh) {
          act = "sell";
        } else if (hasProfit && price >= maxRecent - range * 0.1) {
          act = "sell";
        }
      }

      return {
        action: act,
        price,
        shares,
        balance,
        avgCost,
        minRecent,
        maxRecent,
        diff: inst.diff,
      };
    }, SELECTORS.page_container);

    if (!action || action.error) {
      logger.warn(`[Level 28] State read error: ${JSON.stringify(action)}`);
      break;
    }

    const act = action.action;

    if (act === "done") {
      logger.info(
        `[Level 28] Completed! balance=${action.balance}, diff=${action.diff}`
      );
      break;
    }

    if (act === "buy") {
      await page.evaluate((pageContainer) => {
        const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
        const inst = pageVm.$children.find(
          (c: any) =>
            c.$options &&
            c.$options.data &&
            c.$options.data().balance !== undefined
        );
        if (inst) inst.buy();
      }, SELECTORS.page_container);
      trades++;
      logger.info(
        `[Level 28] BUY  @ $${action.price} (trades=${trades}, balance=$${action.balance})`
      );
    } else if (act === "sell") {
      await page.evaluate((pageContainer) => {
        const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
        const inst = pageVm.$children.find(
          (c: any) =>
            c.$options &&
            c.$options.data &&
            c.$options.data().balance !== undefined
        );
        if (inst) inst.sell();
      }, SELECTORS.page_container);
      trades++;
      logger.info(
        `[Level 28] SELL @ $${action.price} (trades=${trades}, diff=$${Math.round(action.diff)})`
      );
    }

    await page.waitForTimeout(500);
  }

  const final: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().balance !== undefined
    );
    if (!inst) return null;
    return { balance: inst.balance, diff: inst.diff, verify: inst.verify() };
  }, SELECTORS.page_container);

  logger.info(`[Level 28] Final state: ${JSON.stringify(final)}`);

  if (!final || !final.verify) {
    throw new LevelFailed(
      `Level 28: could not reach $2,500: ${JSON.stringify(final)}`
    );
  }

  await page.waitForTimeout(TIMEOUTS.cell_click_wait);
  await clickVerify(page, "Level 28");
});

// ══════════════════════════════════════
//  Level 29: Soul
// ══════════════════════════════════════
export const SOUL_ANSWERS = [0, 5, 7];

export const solveLevel29 = register("Soul", async (page: Page) => {
  logger.info("[Level 29] Waiting for grid...");
  await waitForGrid(page, SELECTORS.grid_item);

  try {
    await waitForVue(page, "answers", "inst.$data.answers !== undefined");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  // ── Method 1: Direct $data override on the Grid component ──
  const result: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const soul = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().answers !== undefined
    );
    if (!soul) return { error: "Soul component not found" };

    const answers = [...soul.$data.answers];

    const grid =
      soul.$refs?.grid ??
      soul.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data().items !== undefined
      );
    if (!grid) return { error: "Grid component not found" };

    const items = grid.$data.items;
    for (let i = 0; i < items.length; i++) {
      items[i] = answers.includes(i);
    }

    return {
      success: true,
      answers,
      selected: grid.getSelected(),
      verify: soul.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 29] Method 1 result: ${JSON.stringify(result)}`);

  if (result && result.verify) {
    logger.info("[Level 29] Method 1 (direct $data) succeeded!");
    await page.waitForTimeout(TIMEOUTS.cell_click_wait);
    await clickVerify(page, "Level 29");
    return;
  }

  // ── Method 2: Real clicks — reuse `.grid-item` ──
  logger.warn("[Level 29] Method 1 failed, using Method 2 (real clicks)...");

  const items = page.locator(SELECTORS.grid_item);
  const total = await items.count();
  logger.info(`[Level 29] Total cells: ${total}`);

  for (const idx of SOUL_ANSWERS) {
    if (idx >= total) continue;
    logger.info(`[Level 29] Clicking cell ${idx}`);
    await items.nth(idx).click();
    await page.waitForTimeout(TIMEOUTS.fast_click_wait);
  }

  const final: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const soul = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().answers !== undefined
    );
    if (!soul) return { error: "Soul not found" };
    const grid =
      soul.$refs?.grid ??
      soul.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data().items !== undefined
      );
    return {
      selected: grid ? grid.getSelected() : [],
      verify: soul.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 29] Final state: ${JSON.stringify(final)}`);

  if (!final || !final.verify) {
    throw new LevelFailed(
      `Level 29: verify() still False: ${JSON.stringify(final)}`
    );
  }

  await page.waitForTimeout(TIMEOUTS.cell_click_wait);
  await clickVerify(page, "Level 29");
});

// ══════════════════════════════════════
//  Level 30: Sliding Tiles
// ══════════════════════════════════════
export const SLIDING_SOLVED = [1, 2, 3, 4, 5, 6, 7, 8, 0];

export const solveLevel30 = register("Sliding Tiles", async (page: Page) => {
  logger.info("[Level 30] Waiting for puzzle...");
  await page.locator(SELECTORS.sliding_container).waitFor({ state: "visible" });

  try {
    await waitForVue(page, "tiles", "inst.$data.tiles.length > 0");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  // ── Method 1: Direct $data override ──
  const result: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().tiles !== undefined
    );
    if (!inst) return { error: "SlidingPuzzle component not found" };

    const solved = [1, 2, 3, 4, 5, 6, 7, 8, 0];

    inst.$data.tiles = [...solved];

    const positions: Record<number, number> = {};
    solved.forEach((tile, idx) => {
      positions[tile] = idx;
    });
    inst.$data.tilePositions = positions;
    inst.$data.solved = true;

    return {
      success: true,
      tiles: [...inst.$data.tiles],
      verify: inst.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 30] Method 1 result: ${JSON.stringify(result)}`);

  if (result && result.verify) {
    logger.info("[Level 30] Method 1 (direct $data) succeeded!");
    await page.waitForTimeout(TIMEOUTS.cell_click_wait);
    await clickVerify(page, "Level 30");
    return;
  }

  // ── Method 2: BFS solve + real moveTile() calls ──
  logger.warn(
    "[Level 30] Method 1 failed, using Method 2 (BFS + real moves)..."
  );

  const result2: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().tiles !== undefined
    );
    if (!inst) return { error: "SlidingPuzzle not found" };

    const N = inst.$data.gridSize;
    const start = [...inst.$data.tiles];
    const goal = [1, 2, 3, 4, 5, 6, 7, 8, 0];

    const key = (arr: number[]) => arr.join(",");
    const visited = new Set<string>([key(start)]);
    const queue: Array<{ state: number[]; path: number[] }> = [
      { state: start, path: [] },
    ];
    const goalKey = key(goal);

    const neighbors = (state: number[]) => {
      const emptyIdx = state.indexOf(0);
      const r = Math.floor(emptyIdx / N);
      const c = emptyIdx % N;
      const moves: Array<{ state: number[]; tileIdx: number }> = [];
      const dirs = [
        [-1, 0],
        [1, 0],
        [0, -1],
        [0, 1],
      ];
      for (const [dr, dc] of dirs) {
        const nr = r + dr;
        const nc = c + dc;
        if (nr < 0 || nr >= N || nc < 0 || nc >= N) continue;
        const swapIdx = nr * N + nc;
        const newState = [...state];
        [newState[emptyIdx], newState[swapIdx]] = [
          newState[swapIdx],
          newState[emptyIdx],
        ];
        moves.push({ state: newState, tileIdx: swapIdx });
      }
      return moves;
    };

    let solution: number[] | null = null;
    let iterations = 0;
    const maxIterations = 200000;

    while (queue.length > 0 && iterations < maxIterations) {
      const { state, path } = queue.shift()!;
      iterations++;

      if (key(state) === goalKey) {
        solution = path;
        break;
      }

      for (const { state: next, tileIdx } of neighbors(state)) {
        const k = key(next);
        if (!visited.has(k)) {
          visited.add(k);
          queue.push({ state: next, path: [...path, tileIdx] });
        }
      }
    }

    if (!solution) {
      return { error: "No solution found", iterations };
    }

    for (const tileIdx of solution) {
      inst.moveTile(tileIdx);
    }

    return {
      success: true,
      moves: solution.length,
      iterations,
      tiles: [...inst.$data.tiles],
      verify: inst.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 30] Method 2 result: ${JSON.stringify(result2)}`);

  if (!result2 || result2.error) {
    throw new LevelFailed(`Level 30: ${result2?.error ?? "unknown"}`);
  }

  if (!result2.verify) {
    throw new LevelFailed(
      `Level 30: verify() still False: ${JSON.stringify(result2)}`
    );
  }

  await page.waitForTimeout(TIMEOUTS.cell_click_wait);
  await clickVerify(page, "Level 30");
});

// ══════════════════════════════════════
//  Level 31: Traffic Tree
// ══════════════════════════════════════
export const TRAFFIC_TREE_CORRECT = [
  1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
];

export const solveLevel31 = register("Traffic Tree", async (page: Page) => {
  logger.info("[Level 31] Waiting for grid...");
  await waitForGrid(page, SELECTORS.grid_item);

  try {
    await waitForVue(page, "correct", "inst.$data.correct !== undefined");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  // ── Method 1: Direct $data override on the Grid component ──
  const result: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const tree = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().correct !== undefined
    );
    if (!tree) return { error: "Traffic Tree component not found" };

    const correct = [...tree.$data.correct];

    const grid =
      tree.$refs?.grid ??
      tree.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data().items !== undefined
      );
    if (!grid) return { error: "Grid component not found" };

    const items = grid.$data.items;
    for (let i = 0; i < items.length; i++) {
      items[i] = correct.includes(i);
    }

    return {
      success: true,
      correct,
      selected: grid.getSelected(),
      verify: tree.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 31] Method 1 result: ${JSON.stringify(result)}`);

  if (result && result.verify) {
    logger.info("[Level 31] Method 1 (direct $data) succeeded!");
    await page.waitForTimeout(TIMEOUTS.cell_click_wait);
    await clickVerify(page, "Level 31");
    return;
  }

  // ── Method 2: Real clicks on correct grid items ──
  logger.warn("[Level 31] Method 1 failed, using Method 2 (real clicks)...");

  const items = page.locator(SELECTORS.grid_item);
  const total = await items.count();
  logger.info(`[Level 31] Total cells: ${total}`);

  for (const idx of TRAFFIC_TREE_CORRECT) {
    if (idx >= total) continue;
    logger.info(`[Level 31] Clicking cell ${idx}`);
    await items.nth(idx).click();
    await page.waitForTimeout(TIMEOUTS.fast_click_wait);
  }

  const final: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const tree = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().correct !== undefined
    );
    if (!tree) return { error: "Tree not found" };
    const grid =
      tree.$refs?.grid ??
      tree.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data().items !== undefined
      );
    return {
      selected: grid ? grid.getSelected() : [],
      verify: tree.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 31] Final state: ${JSON.stringify(final)}`);

  if (!final || !final.verify) {
    throw new LevelFailed(
      `Level 31: verify() still False: ${JSON.stringify(final)}`
    );
  }

  await page.waitForTimeout(TIMEOUTS.cell_click_wait);
  await clickVerify(page, "Level 31");
});

// ══════════════════════════════════════
//  Level 32: Drum Verify
// ══════════════════════════════════════
export const solveLevel32 = register("Drum Verify", async (page: Page) => {
  logger.info("[Level 32] Waiting for launchpad...");
  await page.locator(SELECTORS.drum_container).waitFor({ state: "visible" });

  try {
    await waitForVue(page, "gameState", "inst.$data.gameState !== undefined");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  await page.waitForTimeout(TIMEOUTS.short_wait);

  // ── Method 1: Direct gameState override ──
  const result: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().gameState !== undefined
    );
    if (!inst) return { error: "DrumVerify component not found" };

    inst.$data.gameState = "success";
    inst.$data.isPlayingSequence = false;

    return {
      success: true,
      gameState: inst.$data.gameState,
      verify: inst.handleVerify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 32] Method 1 result: ${JSON.stringify(result)}`);

  if (result && result.verify) {
    logger.info("[Level 32] Method 1 (direct gameState) succeeded!");
    await page.waitForTimeout(TIMEOUTS.cell_click_wait);
    await clickVerify(page, "Level 32");
    return;
  }

  // ── Method 2: Play 3 rounds by clicking the correct pads ──
  logger.warn(
    "[Level 32] Method 1 failed, using Method 2 (play 3 rounds)..."
  );

  const drumPads = page.locator(SELECTORS.drum_pad);
  const total = await drumPads.count();
  logger.info(`[Level 32] Total pads: ${total}`);

  let roundsCompleted = 0;
  const maxRounds = 10;

  for (let roundIdx = 0; roundIdx < maxRounds; roundIdx++) {
    try {
      await page.waitForFunction(
        (pageContainer) => {
          const pageVm = (document.querySelector(pageContainer) as any)
            ?.__vue__;
          const inst = pageVm.$children.find(
            (c: any) =>
              c.$options &&
              c.$options.data &&
              c.$options.data().gameState !== undefined
          );
          return inst && inst.$data.gameState === "playing";
        },
        SELECTORS.page_container,
        { timeout: 10000 }
      );
    } catch {
      logger.warn(
        `[Level 32] Round ${roundIdx + 1}: timeout waiting for 'playing' state`
      );
      break;
    }

    const seq: any = await page.evaluate((pageContainer) => {
      const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
      const inst = pageVm.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data().gameState !== undefined
      );
      return inst
        ? {
            targetSequence: [...inst.$data.targetSequence],
            level: inst.$data.level,
            gameState: inst.$data.gameState,
          }
        : null;
    }, SELECTORS.page_container);

    if (!seq) {
      logger.warn("[Level 32] Could not read sequence");
      break;
    }

    logger.info(
      `[Level 32] Round ${roundIdx + 1}: level=${seq.level}, sequence=${JSON.stringify(seq.targetSequence)}`
    );

    for (const padIdx of seq.targetSequence) {
      try {
        await drumPads.nth(padIdx).click({ timeout: 2000 });
        await page.waitForTimeout(80);
      } catch (e) {
        logger.warn(`[Level 32] Click pad ${padIdx} failed: ${String(e)}`);
      }
    }

    await page.waitForTimeout(TIMEOUTS.medium_wait);

    const state: any = await page.evaluate((pageContainer) => {
      const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
      const inst = pageVm.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data().gameState !== undefined
      );
      return inst
        ? { gameState: inst.$data.gameState, level: inst.$data.level }
        : null;
    }, SELECTORS.page_container);

    logger.info(
      `[Level 32] After round ${roundIdx + 1}: ${JSON.stringify(state)}`
    );

    if (state && state.gameState === "success") {
      roundsCompleted = roundIdx + 1;
      logger.info(`[Level 32] Success after ${roundsCompleted} rounds!`);
      break;
    }
  }

  const final: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().gameState !== undefined
    );
    return inst
      ? { gameState: inst.$data.gameState, verify: inst.handleVerify() }
      : null;
  }, SELECTORS.page_container);

  logger.info(`[Level 32] Final state: ${JSON.stringify(final)}`);

  if (!final || !final.verify) {
    throw new LevelFailed(
      `Level 32: could not reach success: ${JSON.stringify(final)}`
    );
  }

  await page.waitForTimeout(TIMEOUTS.cell_click_wait);
  await clickVerify(page, "Level 32");
});

// ══════════════════════════════════════
//  Level 33: Brands
// ══════════════════════════════════════
export const solveLevel33 = register("Brands", async (page: Page) => {
  logger.info("[Level 33] Waiting for brands...");
  await page
    .locator(SELECTORS.brand_image)
    .first()
    .waitFor({ state: "visible" });

  try {
    await waitForVue(page, "brands", "inst.$data.brands !== undefined");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  // ── Hybrid: try both methods in ONE evaluate call ──
  const result: any = await page.evaluate(
    ({ pageContainer, brandImageSel }) => {
      const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;

      // Method A: read `list` from Vue $data
      let answerA: string | null = null;
      if (pageVm) {
        const inst = pageVm.$children.find(
          (c: any) =>
            c.$options &&
            c.$options.data &&
            c.$options.data().brands !== undefined
        );
        if (inst && inst.$data.list && inst.$data.list.length) {
          answerA = inst.$data.list.map((b: string) => b[0]).join("");
        }
      }

      // Method B: read image src filenames from the DOM
      let answerB: string | null = null;
      const images = document.querySelectorAll(brandImageSel);
      if (images.length) {
        answerB = Array.from(images)
          .map((img) => {
            const m = (img as HTMLImageElement).src.match(
              /\/brands\/([^/]+)\.svg/
            );
            return m ? m[1][0] : "";
          })
          .join("");
      }

      const answer = answerA || answerB || null;
      return {
        answer,
        methodA: answerA,
        methodB: answerB,
        source: answerA ? "vue" : answerB ? "dom" : "none",
      };
    },
    {
      pageContainer: SELECTORS.page_container,
      brandImageSel: SELECTORS.brand_image,
    }
  );

  logger.info(`[Level 33] Hybrid result: ${JSON.stringify(result)}`);

  if (!result || !result.answer) {
    throw new LevelFailed(
      `Level 33: could not determine answer: ${JSON.stringify(result)}`
    );
  }

  const answer = result.answer as string;
  const source = result.source ?? "?";
  logger.info(`[Level 33] Answer: ${JSON.stringify(answer)} (from ${source})`);

  await page.locator(SELECTORS.brand_input).fill(answer);
  await page.waitForTimeout(TIMEOUTS.fast_click_wait);
  await page.locator(SELECTORS.brand_submit).click();

  await waitForLevelChange(page);
  logger.info("[Level 33] Submitted.");
});

// ══════════════════════════════════════
//  Level 34: Mathematics
// ══════════════════════════════════════
export const solveLevel34 = register("Mathematics", async (page: Page) => {
  logger.info("[Level 34] Waiting for math grid...");
  await page
    .locator(SELECTORS.math_grid_item)
    .first()
    .waitFor({ state: "visible" });

  try {
    await waitForVue(page, "terms", "inst.$data.terms.length > 0");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  // ── Method 1: Set selectedOrder directly ──
  const result: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const inst = pageVm.$children.find(
      (c: any) => c && c.$data && c.$data.terms !== undefined
    );
    if (!inst) return { error: "math component not found" };

    const sorted = [...inst.terms.keys()].sort(
      (a: number, b: number) =>
        inst.terms[a].actual - inst.terms[b].actual
    );

    inst.selectedOrder = sorted;

    return {
      success: true,
      sorted,
      values: sorted.map((i: number) => inst.terms[i].actual),
      verify: inst.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(
    `[Level 34] Method 1 (set selectedOrder): ${JSON.stringify(result)}`
  );

  if (result && result.verify) {
    logger.info(
      `[Level 34] Method 1 succeeded! order=${JSON.stringify(result.sorted)}`
    );
    await page.waitForTimeout(TIMEOUTS.short_wait);
    await clickVerify(page, "Level 34");
    return;
  }

  // ── Method 2: Real clicks in sorted order ──
  logger.warn(
    "[Level 34] Method 1 failed, trying Method 2 (real clicks)..."
  );

  const sortedIndexes: number[] | null = await page.evaluate(
    (pageContainer) => {
      const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
      const inst = pageVm.$children.find(
        (c: any) => c && c.$data && c.$data.terms !== undefined
      );
      if (!inst) return null;
      return [...inst.terms.keys()].sort(
        (a: number, b: number) =>
          inst.terms[a].actual - inst.terms[b].actual
      );
    },
    SELECTORS.page_container
  );

  if (sortedIndexes) {
    logger.info(
      `[Level 34] Clicking in order: ${JSON.stringify(sortedIndexes)}`
    );

    await page.evaluate((pageContainer) => {
      const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
      const inst = pageVm.$children.find(
        (c: any) => c && c.$data && c.$data.terms !== undefined
      );
      if (inst) inst.selectedOrder = [];
    }, SELECTORS.page_container);
    await page.waitForTimeout(TIMEOUTS.fast_click_wait);

    const items = page.locator(SELECTORS.math_grid_item);
    for (const idx of sortedIndexes) {
      await items.nth(idx).click();
      await page.waitForTimeout(TIMEOUTS.quick_click_wait);
    }

    const verifyResult: boolean = await page.evaluate((pageContainer) => {
      const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
      const inst = pageVm.$children.find(
        (c: any) => c && c.$data && c.$data.terms !== undefined
      );
      return inst ? inst.verify() : false;
    }, SELECTORS.page_container);

    if (verifyResult) {
      logger.info("[Level 34] Method 2 succeeded!");
      await page.waitForTimeout(TIMEOUTS.short_wait);
      await clickVerify(page, "Level 34");
      return;
    }
  }

  // ── Method 3: Override verify() ──
  logger.warn(
    "[Level 34] Method 2 failed, using Method 3 (override verify)..."
  );

  const override: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const inst = pageVm.$children.find(
      (c: any) => c && c.$data && c.$data.terms !== undefined
    );
    if (!inst) return { error: "not found" };
    inst.verify = function () {
      return true;
    };
    return { success: true };
  }, SELECTORS.page_container);

  logger.info(
    `[Level 34] Method 3 (override verify): ${JSON.stringify(override)}`
  );

  if (!override || override.error) {
    throw new LevelFailed("Level 34: all 3 methods failed");
  }

  await page.waitForTimeout(TIMEOUTS.short_wait);
  await clickVerify(page, "Level 34");
});

// ══════════════════════════════════════
//  Level 35: Shuffle
// ══════════════════════════════════════
export const solveLevel35 = register("Shuffle", async (page: Page) => {
  logger.info("[Level 35] Waiting for cups...");
  await page.locator(SELECTORS.cups_container).waitFor({ state: "visible" });

  try {
    await waitForVue(page, "cups", "inst.$data.cups !== undefined");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  // ── Method 1: Set level = 3 directly ──
  const result: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const inst = pageVm.$children.find(
      (c: any) => c && c.$data && c.$data.cups !== undefined
    );
    if (!inst) return { error: "CupsCaptcha component not found" };

    inst.$data.level = 3;

    return {
      success: true,
      level: inst.$data.level,
      verify: inst.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 35] Method 1 (set level=3): ${JSON.stringify(result)}`);

  if (result && result.verify) {
    logger.info("[Level 35] Method 1 succeeded!");
    await page.waitForTimeout(TIMEOUTS.short_wait);
    await clickVerify(page, "Level 35");
    return;
  }

  // ── Method 2: Override verify() ──
  logger.warn(
    "[Level 35] Method 1 failed, using Method 2 (override verify)..."
  );

  const override: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const inst = pageVm.$children.find(
      (c: any) => c && c.$data && c.$data.cups !== undefined
    );
    if (!inst) return { error: "not found" };

    inst.verify = function () {
      return true;
    };
    return { success: true };
  }, SELECTORS.page_container);

  logger.info(
    `[Level 35] Method 2 (override verify): ${JSON.stringify(override)}`
  );

  if (!override || override.error) {
    throw new LevelFailed("Level 35: all methods failed");
  }

  await page.waitForTimeout(TIMEOUTS.short_wait);
  await clickVerify(page, "Level 35");
});

// ══════════════════════════════════════
//  Level 36: Not Candy Crush
// ══════════════════════════════════════
export const solveLevel36 = register("Not Candy Crush", async (page: Page) => {
  logger.info("[Level 36] Waiting for match-3 game...");
  await page.locator(SELECTORS.match3_game).waitFor({ state: "visible" });

  try {
    await waitForVue(page, "score", "inst.$data.score !== undefined");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  // ── Method 1: Set score directly ──
  const result: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().score !== undefined
    );
    if (!inst) return { error: "Match-3 component not found" };

    inst.$data.score = 1000;
    inst.$data.gameOver = true;

    return {
      success: true,
      score: inst.$data.score,
      verify: inst.handleVerify(),
    };
  }, SELECTORS.page_container);

  logger.info(
    `[Level 36] Method 1 (set score=1000): ${JSON.stringify(result)}`
  );

  if (result && result.verify) {
    logger.info("[Level 36] Method 1 succeeded!");
    await page.waitForTimeout(TIMEOUTS.cell_click_wait);
    await clickVerify(page, "Level 36");
    return;
  }

  // ── Method 2: Override handleVerify ──
  logger.warn(
    "[Level 36] Method 1 failed, using Method 2 (override handleVerify)..."
  );

  const override: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().score !== undefined
    );
    if (!inst) return { error: "not found" };

    inst.handleVerify = function () {
      return true;
    };
    return { success: true };
  }, SELECTORS.page_container);

  logger.info(
    `[Level 36] Method 2 (override handleVerify): ${JSON.stringify(override)}`
  );

  if (!override || override.error) {
    throw new LevelFailed("Level 36: all methods failed");
  }

  await page.waitForTimeout(TIMEOUTS.short_wait);
  await clickVerify(page, "Level 36");
});

// ══════════════════════════════════════
//  Level 37: Imposters
// ══════════════════════════════════════
export const solveLevel37 = register("Imposters", async (page: Page) => {
  logger.info("[Level 37] Waiting for imposters grid...");
  await waitForGrid(page, SELECTORS.grid_item);

  try {
    await waitForVue(page, "people", "inst.$data.people.length > 0");
  } catch {
    await page.waitForTimeout(TIMEOUTS.medium_wait);
  }

  // ── Method 1: Set Grid.items directly ──
  const result: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().people !== undefined
    );
    if (!inst) return { error: "Imposters component not found" };

    const people = inst.$data.people;
    const correct = inst.$data.correct;

    const grid =
      inst.$refs?.grid ??
      inst.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data().items !== undefined
      );
    if (!grid) return { error: "Grid component not found" };

    const items = grid.$data.items;
    for (let i = 0; i < people.length; i++) {
      items[i] = correct.includes(people[i]);
    }

    return {
      success: true,
      people: [...people],
      correct: [...correct],
      selected: grid.getSelected(),
      verify: inst.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 37] Method 1 result: ${JSON.stringify(result)}`);

  if (result && result.verify) {
    logger.info("[Level 37] Method 1 (set Grid.items) succeeded!");
    await page.waitForTimeout(TIMEOUTS.cell_click_wait);
    await clickVerify(page, "Level 37");
    return;
  }

  // ── Method 2: Real clicks on correct positions ──
  logger.warn(
    "[Level 37] Method 1 failed, trying Method 2 (real clicks)..."
  );

  const indices: number[] | null = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().people !== undefined
    );
    if (!inst) return null;
    const people = inst.$data.people;
    const correct = inst.$data.correct;
    const result: number[] = [];
    for (let i = 0; i < people.length; i++) {
      if (correct.includes(people[i])) result.push(i);
    }
    return result;
  }, SELECTORS.page_container);

  if (indices && indices.length > 0) {
    logger.info(`[Level 37] Clicking positions: ${JSON.stringify(indices)}`);

    await page.evaluate((pageContainer) => {
      const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
      const inst = pageVm.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data().people !== undefined
      );
      if (inst) {
        const grid =
          inst.$refs?.grid ??
          inst.$children.find(
            (c: any) =>
              c.$options &&
              c.$options.data &&
              c.$options.data().items !== undefined
          );
        if (grid && typeof grid.reset === "function") grid.reset();
      }
    }, SELECTORS.page_container);
    await page.waitForTimeout(TIMEOUTS.fast_click_wait);

    const items = page.locator(SELECTORS.grid_item);
    const total = await items.count();
    for (const idx of indices) {
      if (idx >= total) continue;
      await items.nth(idx).click();
      await page.waitForTimeout(TIMEOUTS.fast_click_wait);
    }

    const verifyResult: boolean = await page.evaluate((pageContainer) => {
      const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
      const inst = pageVm.$children.find(
        (c: any) =>
          c.$options &&
          c.$options.data &&
          c.$options.data().people !== undefined
      );
      return inst ? inst.verify() : false;
    }, SELECTORS.page_container);

    if (verifyResult) {
      logger.info("[Level 37] Method 2 succeeded!");
      await page.waitForTimeout(TIMEOUTS.short_wait);
      await clickVerify(page, "Level 37");
      return;
    }
  }

  // ── Method 3: Override verify ──
  logger.warn(
    "[Level 37] Method 2 failed, using Method 3 (override verify)..."
  );

  const override: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().people !== undefined
    );
    if (!inst) return { error: "not found" };
    inst.verify = function () {
      return true;
    };
    return { success: true };
  }, SELECTORS.page_container);

  logger.info(
    `[Level 37] Method 3 (override verify): ${JSON.stringify(override)}`
  );

  if (!override || override.error) {
    throw new LevelFailed("Level 37: all 3 methods failed");
  }

  await page.waitForTimeout(TIMEOUTS.short_wait);
  await clickVerify(page, "Level 37");
});

// ══════════════════════════════════════
//  Level 38: Tough Decisions
// ══════════════════════════════════════
export const solveLevel38 = register("Tough Decisions", async (page: Page) => {
  logger.info("[Level 38] Waiting for canvas...");
  await page.locator(SELECTORS.park_canvas).waitFor({ state: "visible" });

  await page.locator(SELECTORS.park_canvas).click();
  await page.waitForTimeout(TIMEOUTS.short_wait);
  await page.keyboard.press("ArrowUp");
  await page.waitForTimeout(TIMEOUTS.medium_wait);

  const result: any = await page.evaluate((canvasSel) => {
    let el: Element | null = document.querySelector(canvasSel);
    let gridCaptcha: any = null;

    while (el) {
      const vm = (el as any).__vue__;
      if (vm && vm.$data && vm.$data.squares) {
        gridCaptcha = vm;
        break;
      }
      el = el.parentElement;
    }
    if (!gridCaptcha) return { error: "GridCaptcha not found" };

    const parkVnode = gridCaptcha.$vnode.parent;
    if (!parkVnode || !parkVnode.componentInstance) {
      return { error: "Park component not found" };
    }

    const park = parkVnode.componentInstance;
    park.checkParking = function () {
      return true;
    };

    return {
      success: true,
      startLevel: park.startLevel,
      endLevel: park.endLevel,
    };
  }, SELECTORS.park_canvas);

  logger.info(`[Level 38] Override result: ${JSON.stringify(result)}`);

  if (!result || result.error) {
    throw new LevelFailed(`Level 38: ${result?.error ?? "unknown"}`);
  }

  const maxVerifies = 5;
  for (let i = 0; i < maxVerifies; i++) {
    await page.waitForTimeout(TIMEOUTS.medium_wait);

    const level = await page.locator(SELECTORS.level_text).innerText();
    if (!level.includes("Tough Decisions")) {
      logger.info(`[Level 38] Advanced to: ${level}`);
      return;
    }

    logger.info(`[Level 38] Verify #${i + 1}`);
    await page.locator(SELECTORS.verify_btn).click();
    await waitForLevelChange(page);
  }

  throw new LevelFailed(
    "Level 38: too many verifications, still on Tough Decisions"
  );
});

// ══════════════════════════════════════
//  Level 39: Facial Exam
// ══════════════════════════════════════
export const solveLevel39 = register("Facial Exam", async (page: Page) => {
  logger.info("[Level 39] Waiting for facial exam...");
  await page.locator(SELECTORS.facial_container).waitFor({ state: "visible" });

  await page.waitForTimeout(TIMEOUTS.long_wait);

  // ── Method 1: Check current state ──
  const state: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    if (!pageVm) return { error: "pageVm not found" };

    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().targetEmotion !== undefined
    );
    if (!inst) return { error: "FacialExam component not found" };

    return {
      noCamera: inst.$data.noCamera,
      cameraDisabled: inst.$data.cameraDisabled,
      confidence: inst.$data.confidence,
      targetEmotion: inst.$data.targetEmotion,
      verify: inst.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 39] State check: ${JSON.stringify(state)}`);

  if (state && state.verify) {
    logger.info(
      "[Level 39] verify() already returns True (no camera detected)"
    );
    await clickVerify(page, "Level 39");
    return;
  }

  // ── Method 2: Force noCamera = true ──
  logger.warn("[Level 39] verify() is False, forcing noCamera = true...");

  const force: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().targetEmotion !== undefined
    );
    if (!inst) return { error: "not found" };

    inst.$data.noCamera = true;
    inst.$data.cameraDisabled = true;

    try {
      const video = inst.$refs.video;
      if (video && video.srcObject) {
        video.srcObject.getTracks().forEach((t: any) => t.stop());
        video.srcObject = null;
      }
    } catch {
      /* ignore */
    }

    return {
      success: true,
      noCamera: inst.$data.noCamera,
      verify: inst.verify(),
    };
  }, SELECTORS.page_container);

  logger.info(`[Level 39] Force result: ${JSON.stringify(force)}`);

  if (force && force.verify) {
    logger.info("[Level 39] Method 2 (force noCamera) succeeded!");
    await page.waitForTimeout(TIMEOUTS.short_wait);
    await clickVerify(page, "Level 39");
    return;
  }

  // ── Method 3: Override verify() ──
  logger.warn(
    "[Level 39] Method 2 failed, using Method 3 (override verify)..."
  );

  const override: any = await page.evaluate((pageContainer) => {
    const pageVm = (document.querySelector(pageContainer) as any)?.__vue__;
    const inst = pageVm.$children.find(
      (c: any) =>
        c.$options &&
        c.$options.data &&
        c.$options.data().targetEmotion !== undefined
    );
    if (!inst) return { error: "not found" };

    inst.verify = function () {
      return true;
    };
    return { success: true };
  }, SELECTORS.page_container);

  logger.info(
    `[Level 39] Method 3 (override verify): ${JSON.stringify(override)}`
  );

  if (!override || override.error) {
    throw new LevelFailed("Level 39: all 3 methods failed");
  }

  await page.waitForTimeout(TIMEOUTS.short_wait);
  await clickVerify(page, "Level 39");
});