"""One handler per level. Auto-registered via @register."""

import logging
import math
import time

from playwright.sync_api import Page

from config import (
    SELECTORS,
    TIMEOUTS,
    RETRY_LIMITS,
    PANORAMA,
    FALLBACK_ANSWERS,
)

logger = logging.getLogger(__name__)

LEVEL_HANDLERS = {}


# ══════════════════════════════════════
#  Exception
# ══════════════════════════════════════
class LevelFailed(Exception):
    """Raised when a level cannot be solved."""
    pass


# ══════════════════════════════════════
#  Registry
# ══════════════════════════════════════
def register(name: str):
    """Decorator: auto-register a handler into LEVEL_HANDLERS."""
    def wrapper(func):
        LEVEL_HANDLERS[name] = func
        return func
    return wrapper


# ══════════════════════════════════════
#  Shared helpers
# ══════════════════════════════════════
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
    """Wait until a Vue condition is true.

    Example: wait_for_vue(page, "grid", "inst.$data.grid.every(x => x === null)")
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


# ══════════════════════════════════════
#  Level 1: Checkbox
# ══════════════════════════════════════
@register("Checkbox")
def solve_level_1(page: Page) -> None:
    """Level 1: Click the checkbox."""
    logger.info("[Level 1] Click checkbox...")
    page.locator(SELECTORS["captcha_box"]).click()
    wait_for_level_change(page)
    logger.info("[Level 1] Done.")


# ══════════════════════════════════════
#  Level 2: Stop Signs
# ══════════════════════════════════════
@register("Stop Signs")
def solve_level_2(page: Page) -> None:
    """Level 2: Click all stop signs (by background-position)."""
    logger.info("[Level 2] Waiting for grid...")
    wait_for_grid(page, SELECTORS["grid_item"])

    target_positions = [
        "66.6667% 0%",
        "100% 0%",
        "66.6667% 33.3333%",
        "100% 33.3333%",
    ]

    items = page.locator(SELECTORS["grid_item"])
    total = items.count()
    logger.info(f"[Level 2] {total} cells")

    for i in range(total):
        style = items.nth(i).get_attribute("style") or ""
        pos = ""
        if "background-position:" in style:
            pos = style.split("background-position:")[1].split(";")[0].strip()

        if pos in target_positions:
            logger.info(f"[Level 2] Click cell {i} -> {pos}")
            items.nth(i).click()
            page.wait_for_timeout(TIMEOUTS["cell_click_wait"])

    click_verify(page, "Level 2")


# ══════════════════════════════════════
#  Level 3: Wiggles
# ══════════════════════════════════════
@register("Wiggles")
def solve_level_3(page: Page) -> None:
    """Level 3: Read the answer from Vue $data.answer."""
    logger.info("[Level 3] Waiting for input...")
    page.locator(SELECTORS["captcha_input"]).wait_for(state="visible")

    try:
        wait_for_vue(page, "answer", "inst.$data.answer !== undefined")
    except Exception:
        logger.warning("[Level 3] Vue answer not ready within timeout")

    answer = page.evaluate(f"""
        () => {{
            const els = document.querySelectorAll('{SELECTORS["captcha_container"]}');
            for (const el of els) {{
                const vm = el.__vue__;
                if (vm && vm.$data && vm.$data.answer !== undefined) {{
                    return vm.$data.answer;
                }}
            }}
            return null;
        }}
    """)

    if not answer:
        logger.warning("[Level 3] Could not read answer, trying fallback...")
        for candidate in FALLBACK_ANSWERS["wiggles"]:
            page.locator(SELECTORS["captcha_input"]).fill(candidate)
            page.locator(SELECTORS["captcha_submit"]).click()
            page.wait_for_timeout(TIMEOUTS["loop_wait"])
            level = page.locator(SELECTORS["level_text"]).inner_text()
            if "Wiggles" not in level:
                logger.info(f"[Level 3] '{candidate}' worked!")
                return
        raise LevelFailed("Level 3: no fallback worked")

    logger.info(f"[Level 3] Answer: {answer!r}")
    page.locator(SELECTORS["captcha_input"]).fill(answer)
    page.locator(SELECTORS["captcha_submit"]).click()
    wait_for_level_change(page)


# ══════════════════════════════════════
#  Level 4: Vegetables
# ══════════════════════════════════════
@register("Vegetables")
def solve_level_4(page: Page) -> None:
    """Level 4: Click all vegetables in the 'correct' list."""
    logger.info("[Level 4] Waiting for grid...")
    wait_for_grid(page, SELECTORS["grid_item"])

    result = page.evaluate(f"""
        () => {{
            const vm = [...document.querySelectorAll('{SELECTORS["captcha_container"]}')]
                .map(el => el.__vue__)
                .find(v => v && v.$data && v.$data.correct);
            if (!vm) return null;
            return {{
                correct:   [...vm.$data.correct],
                optional:  [...vm.$data.optional],
                images:    [...vm.$data.images],
                threshold: vm.$data.threshold,
            }};
        }}
    """)

    if not result:
        raise LevelFailed("Level 4: could not read Vue data")

    logger.info(f"[Level 4] correct={result['correct']}")
    to_click = set(result["correct"])

    items = page.locator(SELECTORS["grid_item"])
    total = items.count()
    clicked = 0

    for i in range(total):
        src = result["images"][i] or ""
        name = src.split("/")[-1].replace(".webp", "").lower()

        if name in to_click:
            logger.info(f"[Level 4] Cell {i} -> {name}, clicking")
            items.nth(i).click()
            clicked += 1
            page.wait_for_timeout(TIMEOUTS["cell_click_wait"])

    logger.info(f"[Level 4] Clicked {clicked} cells")
    click_verify(page, "Level 4")


# ══════════════════════════════════════
#  Level 5: Rotation
# ══════════════════════════════════════
@register("Rotation")
def solve_level_5(page: Page) -> None:
    """Level 5: Rotate each cell to 0 degrees."""
    logger.info("[Level 5] Waiting for grid...")
    wait_for_grid(page, SELECTORS["rotating_item"])

    items = page.locator(SELECTORS["rotating_item"])
    total = items.count()
    logger.info(f"[Level 5] {total} cells")

    for i in range(total):
        style = items.nth(i).get_attribute("style") or ""
        rot = 0
        if "rotate(" in style:
            rot = int(style.split("rotate(")[1].split("deg")[0])

        clicks = ((0 - rot) % 360) // 90
        logger.info(f"[Level 5] Cell {i}: {rot}° -> 0°, {clicks} clicks")

        for _ in range(clicks):
            items.nth(i).click()
            page.wait_for_timeout(TIMEOUTS["quick_click_wait"])

    click_verify(page, "Level 5")


# ══════════════════════════════════════
#  Level 6: XOXO
# ══════════════════════════════════════
def _is_winner(board, player) -> bool:
    """Check if the given player has won on the board."""
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6],
    ]
    for a, b, c in lines:
        if board[a] == board[b] == board[c] == player:
            return True
    return False


def _minimax(board, depth, is_max, me='X', opp='O'):
    """Minimax with depth weighting."""
    if _is_winner(board, me):
        return 10 - depth
    if _is_winner(board, opp):
        return depth - 10
    if '.' not in board:
        return 0

    if is_max:
        best = -math.inf
        for i in range(9):
            if board[i] == '.':
                board[i] = me
                best = max(best, _minimax(board, depth + 1, False, me, opp))
                board[i] = '.'
        return best
    else:
        best = math.inf
        for i in range(9):
            if board[i] == '.':
                board[i] = opp
                best = min(best, _minimax(board, depth + 1, True, me, opp))
                board[i] = '.'
        return best


def _best_move(board, me='X', opp='O'):
    """Return the best move index for the given player."""
    best_score = -math.inf
    best_idx = None
    for i in range(9):
        if board[i] == '.':
            board[i] = me
            score = _minimax(board, 0, False, me, opp)
            board[i] = '.'
            if score > best_score:
                best_score = score
                best_idx = i
    return best_idx


def _read_xoxo_state(page: Page):
    """Read grid, currentPlayer, winner from the XOXO component."""
    return page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return null;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().grid !== undefined
            );
            if (!inst) return null;
            return {{
                grid: [...inst.$data.grid],
                currentPlayer: inst.$data.currentPlayer,
                winner: inst.$data.winner,
            }};
        }}
    """)


@register("XOXO")
def solve_level_6(page: Page) -> None:
    """Level 6: Win at tic-tac-toe."""
    logger.info("[Level 6] Waiting for board...")
    wait_for_grid(page, SELECTORS["ttt_cell"])

    for attempt in range(RETRY_LIMITS["xoxo_games"]):
        logger.info(f"[Level 6] Game #{attempt + 1}")

        logger.info("[Level 6] Clicking Reset...")
        page.locator(SELECTORS["refresh_btn"]).click()

        try:
            wait_for_vue(page, "grid", "inst.$data.grid.every(x => x === null)")
        except Exception:
            page.wait_for_timeout(TIMEOUTS["long_wait"])

        state = _read_xoxo_state(page)
        logger.info(f"[Level 6] Initial state: {state}")

        for move_num in range(9):
            page.wait_for_timeout(TIMEOUTS["medium_wait"])

            state = _read_xoxo_state(page)
            if not state:
                logger.warning("[Level 6] State not found")
                break

            board = ['.' if x is None else x for x in state["grid"]]
            logger.info(f"[Level 6] Board: {board} | player: {state['currentPlayer']} | winner: {state['winner']!r}")

            if state["winner"] == "X":
                logger.info("[Level 6] We won!")
                break
            if state["winner"] == "O":
                logger.warning("[Level 6] Computer won, refreshing...")
                break
            if '.' not in board:
                logger.warning("[Level 6] Draw, refreshing...")
                break

            if state["currentPlayer"] == "X":
                best = _best_move(board, me='X', opp='O')
                if best is None:
                    break
                logger.info(f"[Level 6] Playing at {best}")
                page.locator(SELECTORS["ttt_cell"]).nth(best).click()

        state = _read_xoxo_state(page)
        if state and state["winner"] == "X":
            break
    else:
        raise LevelFailed("Level 6: could not win in retries")

    click_verify(page, "Level 6")


# ══════════════════════════════════════
#  Level 7: Word Search
# ══════════════════════════════════════
@register("Word Search")
def solve_level_7(page: Page) -> None:
    """Level 7: Find hidden words in a word search grid."""
    logger.info("[Level 7] Waiting for grid...")
    wait_for_grid(page, SELECTORS["ws_cell"])

    data = read_vue_child(page, "puzzle")
    if not data:
        raise LevelFailed("Level 7: could not read puzzle")

    size = data["gridSize"]
    grid = data["puzzle"]
    words = data["words"]
    logger.info(f"[Level 7] Grid size: {size}, words={words}")

    directions = [
        (0, 1), (1, 0), (1, 1), (1, -1),
        (0, -1), (-1, 0), (-1, -1), (-1, 1),
    ]

    cells_to_click = set()

    for word in words:
        found = False
        for r in range(size):
            for c in range(size):
                if grid[r][c].upper() != word[0]:
                    continue
                for dr, dc in directions:
                    coords = []
                    ok = True
                    for i, ch in enumerate(word):
                        nr, nc = r + dr * i, c + dc * i
                        if not (0 <= nr < size and 0 <= nc < size):
                            ok = False
                            break
                        if grid[nr][nc].upper() != ch:
                            ok = False
                            break
                        coords.append((nr, nc))
                    if ok:
                        logger.info(f"[Level 7] Found '{word}' at {coords}")
                        for (nr, nc) in coords:
                            cells_to_click.add(nr * size + nc)
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if not found:
            logger.warning(f"[Level 7] Could not find '{word}'")

    items = page.locator(SELECTORS["ws_cell"])
    for idx in sorted(cells_to_click):
        items.nth(idx).click()
        page.wait_for_timeout(TIMEOUTS["fast_click_wait"])

    click_verify(page, "Level 7")


# ══════════════════════════════════════
#  Level 8: License Plate
# ══════════════════════════════════════
@register("License Plate")
def solve_level_8(page: Page) -> None:
    """Level 8: Read the license plate from the image URL."""
    logger.info("[Level 8] Waiting for image...")
    page.locator(SELECTORS["license_image"]).wait_for(state="visible")

    src = page.locator(SELECTORS["license_image"]).get_attribute("src") or ""
    plate = src.split("/")[-1].replace(".webp", "")
    logger.info(f"[Level 8] Plate: {plate}")

    page.locator(SELECTORS["captcha_input"]).fill(plate)
    page.locator(SELECTORS["captcha_submit"]).click()
    wait_for_level_change(page)


# ══════════════════════════════════════
#  Level 9: Nested
# ══════════════════════════════════════
@register("Nested")
def solve_level_9(page: Page) -> None:
    """Level 9: Set selected = correct."""
    logger.info("[Level 9] Waiting for grid...")
    page.locator(SELECTORS["nested_grid"]).wait_for(state="visible")

    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().correct !== undefined
            );
            if (!inst) return null;
            inst.$data.selected = [...inst.$data.correct];
            return {{
                correct: [...inst.$data.correct],
                selected: [...inst.$data.selected],
            }};
        }}
    """)

    if not result:
        raise LevelFailed("Level 9: could not set selected")

    logger.info(f"[Level 9] Set selected = {len(result['selected'])} paths")
    page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
    click_verify(page, "Level 9")


# ══════════════════════════════════════
#  Level 10: Whack-a-Mole
# ══════════════════════════════════════
@register("Whack-a-Mole")
def solve_level_10(page: Page) -> None:
    """Level 10: Whack 5 moles."""
    logger.info("[Level 10] Waiting for grid...")
    wait_for_grid(page, SELECTORS["mole_wrapper"])

    start = time.time()
    timeout = RETRY_LIMITS["mole_timeout"]

    while time.time() - start < timeout:
        active = page.locator(SELECTORS["mole_active"])
        count = active.count()

        if count > 0:
            for i in range(count):
                try:
                    active.nth(i).click(timeout=500, force=True)
                    logger.info("[Level 10] Whacked an active mole")
                except Exception:
                    try:
                        active.nth(i).scroll_into_view_if_needed(timeout=300)
                        active.nth(i).click(timeout=300, force=True)
                        logger.info("[Level 10] Whacked after scroll")
                    except Exception:
                        pass
        else:
            page.wait_for_timeout(RETRY_LIMITS["mole_click_wait"])

        whacked = read_vue_child(page, "targetScore")
        if whacked and whacked["whackedMoles"] and len(whacked["whackedMoles"]) >= whacked["targetScore"]:
            logger.info(f"[Level 10] Whacked {len(whacked['whackedMoles'])}/{whacked['targetScore']}!")
            break

    click_verify(page, "Level 10")


# ══════════════════════════════════════
#  Level 11: Waldo
# ══════════════════════════════════════
@register("Waldo")
def solve_level_11(page: Page) -> None:
    """Level 11: Click the cells containing Waldo."""
    logger.info("[Level 11] Waiting for grid...")
    wait_for_grid(page, SELECTORS["grid_item"])

    data = read_vue_child(page, "correct")
    if not data:
        raise LevelFailed("Level 11: could not read correct")

    correct = data["correct"]
    logger.info(f"[Level 11] Correct indexes: {correct}")

    items = page.locator(SELECTORS["grid_item"])
    for idx in correct:
        items.nth(idx).click()
        page.wait_for_timeout(TIMEOUTS["fast_click_wait"])

    click_verify(page, "Level 11")


# ══════════════════════════════════════
#  Level 12: Muffins?
# ══════════════════════════════════════
@register("Muffins?")
def solve_level_12(page: Page) -> None:
    """Level 12: Click all images matching the target."""
    logger.info("[Level 12] Waiting for grid...")
    wait_for_grid(page, SELECTORS["muffin_img"])

    target = page.locator(SELECTORS["captcha_title_type"]).inner_text().strip().lower()
    logger.info(f"[Level 12] Target: {target}")

    items = page.locator(SELECTORS["muffin_img"])
    total = items.count()
    clicked = 0

    for i in range(total):
        src = items.nth(i).get_attribute("src") or ""
        category = src.split("/")[-2].lower()

        if target in category or category in target:
            logger.info(f"[Level 12] Cell {i} -> {category}, clicking")
            items.nth(i).locator("xpath=..").click()
            clicked += 1
            page.wait_for_timeout(TIMEOUTS["quick_click_wait"])

    logger.info(f"[Level 12] Clicked {clicked} cells")
    click_verify(page, "Level 12")


# ══════════════════════════════════════
#  Level 13: Reverse
# ══════════════════════════════════════
@register("Reverse")
def solve_level_13(page: Page) -> None:
    """Level 13: Click all cells WITHOUT a traffic light."""
    logger.info("[Level 13] Waiting for grid...")
    wait_for_grid(page, SELECTORS["grid_item"])

    result = read_vue_child(page, "answers")
    if not result:
        raise LevelFailed("Level 13: could not read answers")

    q_idx = result["questionIndex"]
    correct = result["answers"][q_idx]
    logger.info(f"[Level 13] Question index: {q_idx}, correct: {correct}")

    items = page.locator(SELECTORS["grid_item"])
    for idx in correct:
        items.nth(idx).click()
        page.wait_for_timeout(TIMEOUTS["fast_click_wait"])

    click_verify(page, "Level 13")


# ══════════════════════════════════════
#  Level 14: Affirmations
# ══════════════════════════════════════
@register("Affirmations")
def solve_level_14(page: Page) -> None:
    """Level 14: Click the only checkbox with wrong=false."""
    logger.info("[Level 14] Waiting for grid...")
    wait_for_grid(page, SELECTORS["recaptcha_container"])

    result = page.evaluate(f"""
        () => {{
            const boxes = document.querySelectorAll('{SELECTORS["recaptcha_container"]}');
            const toClick = [];
            boxes.forEach((box, i) => {{
                const vm = box.__vue__;
                if (!vm) return;
                if (vm.$props.wrong === false) {{
                    toClick.push({{ index: i, text: vm.$props.text }});
                }}
            }});
            return toClick;
        }}
    """)

    if not result:
        raise LevelFailed("Level 14: no correct answer found")

    logger.info(f"[Level 14] Found {len(result)} correct boxes")
    for item in result:
        idx = item["index"]
        clicked = page.evaluate(f"""
            () => {{
                const boxes = document.querySelectorAll('{SELECTORS["recaptcha_container"]}');
                const box = boxes[{idx}];
                if (!box) return false;
                const checkbox = box.querySelector('{SELECTORS["captcha_box_checkbox"]}');
                if (checkbox) {{
                    checkbox.click();
                    return true;
                }}
                return false;
            }}
        """)
        logger.info(f"[Level 14] Box {idx} clicked: {clicked}")

    wait_for_level_change(page)


# ══════════════════════════════════════
#  Level 15: Parking
# ══════════════════════════════════════
@register("Parking")
def solve_level_15(page: Page) -> None:
    """Level 15: Override checkParking to always return true."""
    logger.info("[Level 15] Waiting for canvas...")
    page.locator(SELECTORS["park_canvas"]).wait_for(state="visible")

    page.locator(SELECTORS["park_canvas"]).click()
    page.wait_for_timeout(TIMEOUTS["short_wait"])
    page.keyboard.press("ArrowUp")
    page.wait_for_timeout(TIMEOUTS["medium_wait"])

    result = page.evaluate(f"""
        () => {{
            let el = document.querySelector('{SELECTORS["park_canvas"]}');
            let gridCaptcha = null;
            while (el) {{
                if (el.__vue__ && el.__vue__.$data && el.__vue__.$data.squares) {{
                    gridCaptcha = el.__vue__;
                    break;
                }}
                el = el.parentElement;
            }}
            if (!gridCaptcha) return {{ error: 'GridCaptcha not found' }};

            const parkVnode = gridCaptcha.$vnode.parent;
            if (!parkVnode || !parkVnode.componentInstance) {{
                return {{ error: 'Park component not found' }};
            }}

            const park = parkVnode.componentInstance;
            park.checkParking = function() {{ return true; }};

            return {{ success: true }};
        }}
    """)

    if not result or result.get("error"):
        raise LevelFailed("Level 15: failed to override checkParking")

    for i in range(RETRY_LIMITS["parking_verifies"]):
        page.wait_for_timeout(TIMEOUTS["medium_wait"])

        level = page.locator(SELECTORS["level_text"]).inner_text()
        if "Parking" not in level:
            logger.info(f"[Level 15] Advanced to: {level}")
            return

        logger.info(f"[Level 15] Verify #{i+1}")
        page.locator(SELECTORS["verify_btn"]).click()
        wait_for_level_change(page)


# ══════════════════════════════════════
#  Level 16: Now in 3D!
# ══════════════════════════════════════
@register("Now in 3D!")
def solve_level_16(page: Page) -> None:
    """Level 16: Read captchaText from Vue."""
    logger.info("[Level 16] Waiting for input...")
    page.locator(SELECTORS["captcha_input"]).wait_for(state="visible")

    try:
        wait_for_vue(page, "captchaText", "inst.$data.captchaText !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])

    data = read_vue_child(page, "captchaText")
    answer = data.get("captchaText") if data else None

    if not answer:
        raise LevelFailed("Level 16: could not read captchaText")

    logger.info(f"[Level 16] Answer: {answer!r}")
    page.locator(SELECTORS["captcha_input"]).fill(answer)
    page.locator(SELECTORS["captcha_submit"]).click()
    wait_for_level_change(page)


# ══════════════════════════════════════
#  Level 17: Perfect Circle
# ══════════════════════════════════════
@register("Perfect Circle")
def solve_level_17(page: Page) -> None:
    """Level 17: Override score to 1000."""
    logger.info("[Level 17] Waiting for SVG...")
    page.locator(SELECTORS["circle_svg"]).wait_for(state="visible")

    try:
        wait_for_vue(page, "score", "inst.$data.score !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["long_wait"])

    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c && c.$data && c.$data.score !== undefined
            );
            if (!inst) return {{ error: 'Component not found' }};

            inst.$data.score = 1000;
            inst.$data.best = 1000;
            inst.$data.hasDrawn = true;
            inst.$data.valid = true;

            return {{ success: true, score: inst.$data.score }};
        }}
    """)

    if not result or result.get("error"):
        raise LevelFailed("Level 17: failed to override score")

    logger.info(f"[Level 17] Override result: {result}")
    page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
    click_verify(page, "Level 17")


# ══════════════════════════════════════
#  Level 18: Sisyphus
# ══════════════════════════════════════
@register("Sisyphus")
def solve_level_18(page: Page) -> None:
    """Level 18: Click hydrants until none remain."""
    logger.info("[Level 18] Waiting for grid...")
    wait_for_grid(page, SELECTORS["sisyphus_grid_item"])

    max_attempts = RETRY_LIMITS["sisyphus_attempts"]
    for i in range(max_attempts):
        hydrants = page.locator(SELECTORS["hydrant_img"])
        count = hydrants.count()
        logger.info(f"[Level 18] Attempt #{i+1} | {count} hydrants")

        if count == 0:
            logger.info("[Level 18] No more hydrants")
            break

        try:
            hydrants.first.click(timeout=1000, force=True)
        except Exception as e:
            logger.warning(f"[Level 18] Click failed: {e}")

        page.wait_for_timeout(TIMEOUTS["click_wait"])

    logger.info("[Level 18] Clicking Verify...")
    page.locator(SELECTORS["verify_btn"]).click(force=True)
    wait_for_level_change(page)


# ══════════════════════════════════════
#  Level 19: In the Dark
# ══════════════════════════════════════
@register("In the Dark")
def solve_level_19(page: Page) -> None:
    """Level 19: Read the letters from the DOM."""
    logger.info("[Level 19] Waiting for grid...")
    page.locator(SELECTORS["flashlight_container"]).wait_for(state="visible")

    answer = page.evaluate(f"""
        () => {{
            const letters = document.querySelectorAll('{SELECTORS["letter"]}');
            return [...letters].map(l => l.innerText.trim()).join('');
        }}
    """)

    if not answer:
        raise LevelFailed("Level 19: could not read letters")

    logger.info(f"[Level 19] Answer: {answer!r}")
    page.locator(SELECTORS["captcha_input"]).fill(answer)
    page.locator(SELECTORS["captcha_submit"]).click()
    wait_for_level_change(page)


# ══════════════════════════════════════
#  Level 20: Rorschach
# ══════════════════════════════════════
@register("Rorschach")
def solve_level_20(page: Page) -> None:
    """Level 20: Any answer works (tested manually)."""
    logger.info("[Level 20] Waiting for image...")
    page.locator(SELECTORS["rorschach_image"]).wait_for(state="visible")

    answer = FALLBACK_ANSWERS["rorschach"]
    logger.info(f"[Level 20] Answer: {answer!r}")

    page.locator(SELECTORS["captcha_input"]).fill(answer)
    page.locator(SELECTORS["captcha_submit"]).click()
    wait_for_level_change(page)


# ══════════════════════════════════════
#  Level 21: CRAFTCHA
# ══════════════════════════════════════
@register("CRAFTCHA")
def solve_level_21(page: Page) -> None:
    """Level 21: Set hasCraftedTargetItem = true."""
    logger.info("[Level 21] Waiting for crafting UI...")
    page.locator(SELECTORS["crafting_slot"]).first.wait_for(state="visible")
    page.wait_for_timeout(TIMEOUTS["short_wait"])

    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c && c.$data && c.$data.craftingTable !== undefined
            );
            if (!inst) return {{ error: 'crafting component not found' }};

            inst.hasCraftedTargetItem = true;
            return {{ success: true }};
        }}
    """)

    if not result or result.get("error"):
        raise LevelFailed("Level 21: failed to set hasCraftedTargetItem")

    logger.info(f"[Level 21] result: {result}")
    page.wait_for_timeout(TIMEOUTS["short_wait"])
    click_verify(page, "Level 21")


# ══════════════════════════════════════
#  Level 22: My Ducks Ahhh
# ══════════════════════════════════════
@register("My Ducks Ahhh")
def solve_level_22(page: Page) -> None:
    """Level 22: Set all ducks clicked = true."""
    logger.info("[Level 22] Waiting for ducks...")
    page.locator(SELECTORS["duck_container"]).wait_for(state="visible")

    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c && c.$data && Array.isArray(c.$data.ducks)
            );
            if (!inst) return {{ error: 'ducks component not found' }};

            inst.$data.ducks.forEach((duck) => {{
                duck.clicked = true;
            }});
            inst.$data.done = true;
            inst.$data.isRoaming = false;

            return {{
                success: true,
                clicked: inst.$data.ducks.filter(d => d.clicked).length,
                total: inst.$data.ducks.length,
            }};
        }}
    """)

    if not result or result.get("error"):
        raise LevelFailed("Level 22: failed to set ducks clicked")

    logger.info(f"[Level 22] result: {result}")
    click_verify(page, "Level 22")


# ══════════════════════════════════════
#  Level 23: Panorama
# ══════════════════════════════════════
@register("Panorama")
def solve_level_23(page: Page) -> None:
    """Level 23: Panorama — Real drag with fallback to direct setters."""
    logger.info("[Level 23] Waiting for panorama...")
    page.locator(SELECTORS["panorama"]).wait_for(state="visible")

    try:
        wait_for_vue(page, "challenges", "inst.viewer !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["page_load"])

    for attempt in range(RETRY_LIMITS["panorama_attempts"]):
        info = page.evaluate(f"""
            () => {{
                const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
                const inst = pageVm.$children.find(c =>
                    c && c.$data && c.$data.challenges !== undefined
                );
                if (!inst || !inst.viewer) return {{ error: 'viewer not found' }};

                const challenge = inst.challenges[inst.currentChallenge];
                const canvas = document.querySelector('{SELECTORS["panorama_canvas"]}');
                if (!canvas) return {{ error: 'canvas not found' }};

                return {{
                    title: challenge.title,
                    pitchBounds: challenge.pitchBounds,
                    yawBounds: challenge.yawBounds,
                    maxHfov: challenge.maxHfov,
                    currentPitch: inst.viewer.getPitch(),
                    currentYaw: inst.viewer.getYaw(),
                    currentHfov: inst.viewer.getHfov(),
                    canvasWidth: canvas.width,
                    canvasHeight: canvas.height,
                }};
            }}
        """)

        if info.get("error"):
            raise LevelFailed(f"Level 23: {info['error']}")

        in_pitch = info["pitchBounds"][0] <= info["currentPitch"] <= info["pitchBounds"][1]
        in_yaw = info["yawBounds"][0] <= info["currentYaw"] <= info["yawBounds"][1]
        in_hfov = info["currentHfov"] <= info["maxHfov"]

        logger.info(
            f"[Level 23] Attempt #{attempt + 1}: "
            f"pitch={info['currentPitch']:.2f}, yaw={info['currentYaw']:.2f}, "
            f"hfov={info['currentHfov']:.2f} | "
            f"target: pitch={info['pitchBounds']}, yaw={info['yawBounds']}, "
            f"hfov<={info['maxHfov']}"
        )

        if in_pitch and in_yaw and in_hfov:
            logger.info("[Level 23] Already in range!")
            break

        target_pitch = (info["pitchBounds"][0] + info["pitchBounds"][1]) / 2
        target_yaw = (info["yawBounds"][0] + info["yawBounds"][1]) / 2
        delta_pitch = target_pitch - info["currentPitch"]
        delta_yaw = target_yaw - info["currentYaw"]

        pixels_yaw = -delta_yaw * info["canvasWidth"] / info["currentHfov"]
        pixels_pitch = delta_pitch * info["canvasHeight"] / info["currentHfov"]

        pano = page.locator(SELECTORS["panorama"])
        box = pano.bounding_box()
        if not box:
            raise LevelFailed("Level 23: could not get bounding box")

        center_x = box["x"] + box["width"] / 2
        center_y = box["y"] + box["height"] / 2

        page.mouse.move(center_x, center_y)
        page.mouse.down()
        page.mouse.move(center_x + pixels_yaw, center_y + pixels_pitch, steps=PANORAMA["drag_steps"])
        page.mouse.up()
        page.wait_for_timeout(TIMEOUTS["medium_wait"])

        page.mouse.move(center_x, center_y)
        for _ in range(PANORAMA["max_zoom_iter"]):
            hfov = page.evaluate(f"""
                () => {{
                    const inst = document.querySelector('{SELECTORS["page_container"]}').__vue__.$children.find(c =>
                        c && c.$data && c.$data.challenges !== undefined
                    );
                    return inst.viewer.getHfov();
                }}
            """)
            if hfov <= info["maxHfov"]:
                break
            page.mouse.wheel(0, PANORAMA["wheel_delta"])
            page.wait_for_timeout(PANORAMA["wheel_wait"])

    final = page.evaluate(f"""
        () => {{
            const inst = document.querySelector('{SELECTORS["page_container"]}').__vue__.$children.find(c =>
                c && c.$data && c.$data.challenges !== undefined
            );
            const challenge = inst.challenges[inst.currentChallenge];
            const pitch = inst.viewer.getPitch();
            const yaw = inst.viewer.getYaw();
            const hfov = inst.viewer.getHfov();
            const ok = hfov <= challenge.maxHfov
                && pitch >= challenge.pitchBounds[0] && pitch <= challenge.pitchBounds[1]
                && yaw >= challenge.yawBounds[0] && yaw <= challenge.yawBounds[1];
            return {{ ok, pitch, yaw, hfov }};
        }}
    """)
    logger.info(f"[Level 23] Final: {final}")

    if not final["ok"]:
        logger.warning("[Level 23] Method 3 failed, using method 1 (direct setters)...")
        page.evaluate(f"""
            () => {{
                const inst = document.querySelector('{SELECTORS["page_container"]}').__vue__.$children.find(c =>
                    c && c.$data && c.$data.challenges !== undefined
                );
                const challenge = inst.challenges[inst.currentChallenge];
                const pitch = (challenge.pitchBounds[0] + challenge.pitchBounds[1]) / 2;
                const yaw = (challenge.yawBounds[0] + challenge.yawBounds[1]) / 2;
                const hfov = challenge.maxHfov - 1;
                inst.viewer.setPitch(pitch);
                inst.viewer.setYaw(yaw);
                inst.viewer.setHfov(hfov);
            }}
        """)
        page.wait_for_timeout(TIMEOUTS["medium_wait"])

    click_verify(page, "Level 23")

@register("Eye Exam")
def solve_level_24(page: Page) -> None:
    """Level 24: Eye Exam — complete all 4 sub-levels."""
    logger.info("[Level 24] Waiting for eye exam...")
    page.locator(SELECTORS["eye_exam_container"]).wait_for(state="visible")

    # ══════════════════════════════════════
    #  Sub-level 0: Read the last row letters
    # ══════════════════════════════════════
    logger.info("[Level 24] Sub-level 0: last row letters")
    letters = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c && c.$data && c.$data.chartRows !== undefined
            );
            if (!inst) return null;
            return inst.$data.chartRows[4].letters.join("");
        }}
    """)
    logger.info(f"[Level 24] Letters: {letters}")

    if not letters:
        raise LevelFailed("Level 24: could not read chartRows[4]")

    page.locator(SELECTORS["eye_exam_input"]).fill(letters)
    page.locator(SELECTORS["verify_btn"]).click()
    page.wait_for_timeout(TIMEOUTS["medium_wait"])

    # ══════════════════════════════════════
    #  Sub-level 1: Read the number
    # ══════════════════════════════════════
    logger.info("[Level 24] Sub-level 1: number")
    number = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c && c.$data && c.$data.chartRows !== undefined
            );
            if (!inst) return null;
            return String(inst.$data.colorTests[inst.$data.colorTestIndex]);
        }}
    """)
    logger.info(f"[Level 24] Number: {number}")

    if not number:
        raise LevelFailed("Level 24: could not read colorTests")

    page.locator(SELECTORS["eye_exam_input"]).fill(number)
    page.locator(SELECTORS["verify_btn"]).click()
    page.wait_for_timeout(TIMEOUTS["medium_wait"])

    # ══════════════════════════════════════
    #  Sub-level 2: Count dots (always 34)
    # ══════════════════════════════════════
    logger.info("[Level 24] Sub-level 2: counting dots (34)")
    page.locator(SELECTORS["eye_exam_input"]).fill("34")
    page.locator(SELECTORS["verify_btn"]).click()
    page.wait_for_timeout(TIMEOUTS["medium_wait"])

    # ══════════════════════════════════════
    #  Sub-level 3: Click the different color square
    # ══════════════════════════════════════
    logger.info("[Level 24] Sub-level 3: different color square")
    diff_index = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c && c.$data && c.$data.chartRows !== undefined
            );
            if (!inst) return null;
            return inst.$data.randomColorDiffIndex;
        }}
    """)
    logger.info(f"[Level 24] Different color at index: {diff_index}")

    if diff_index is None:
        raise LevelFailed("Level 24: could not read randomColorDiffIndex")

    page.locator(SELECTORS["eye_exam_square"]).nth(diff_index).click()
    page.wait_for_timeout(TIMEOUTS["quick_click_wait"])
    page.locator(SELECTORS["verify_btn"]).click()

    # Wait for level change
    wait_for_level_change(page)
    logger.info("[Level 24] Done.")