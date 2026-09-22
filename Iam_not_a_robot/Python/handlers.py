"""One handler per level. Auto-registered via @register."""
import logging
import math
import time
from playwright.sync_api import Page
from Iam_not_a_robot.Python.config import (
    SELECTORS,
    TIMEOUTS,
    RETRY_LIMITS,
    FALLBACK_ANSWERS,
)
from Iam_not_a_robot.Python.helpers import (
    read_vue_child,
    wait_for_level_change,
    click_verify,
    wait_for_grid,
    wait_for_vue,
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
    """Level 23: Panorama — set viewer to correct values directly."""
    logger.info("[Level 23] Waiting for panorama...")
    page.locator(SELECTORS["panorama"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "challenges", "inst.viewer !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["page_load"])
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c && c.$data && c.$data.challenges !== undefined
            );
            if (!inst || !inst.viewer) return {{ error: 'viewer not found' }};
            const challenge = inst.challenges[inst.currentChallenge];
            const pitch = (challenge.pitchBounds[0] + challenge.pitchBounds[1]) / 2;
            const yaw = (challenge.yawBounds[0] + challenge.yawBounds[1]) / 2;
            const hfov = challenge.maxHfov - 1;
            inst.viewer.setPitch(pitch);
            inst.viewer.setYaw(yaw);
            inst.viewer.setHfov(hfov);
            return {{
                success: true,
                title: challenge.title,
                pitch: pitch,
                yaw: yaw,
                hfov: hfov,
            }};
        }}
    """)
    logger.info(f"[Level 23] Set viewer: {result}")
    if not result or result.get("error"):
        raise LevelFailed(f"Level 23: {result.get('error', 'unknown')}")
    page.wait_for_timeout(TIMEOUTS["short_wait"])
    click_verify(page, "Level 23")
# ══════════════════════════════════════
#  Level 24: Eye Exam
# ══════════════════════════════════════
@register("Eye Exam")
def solve_level_24(page: Page) -> None:
    """Level 24: Eye Exam — complete all 4 sub-levels."""
    logger.info("[Level 24] Waiting for eye exam...")
    page.locator(SELECTORS["eye_exam_container"]).wait_for(state="visible")
    # ── Sub-level 0: Read the last row letters ──
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
    # ── Sub-level 1: Read the number ──
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
    # ── Sub-level 2: Count dots (always 34) ──
    logger.info("[Level 24] Sub-level 2: counting dots (34)")
    page.locator(SELECTORS["eye_exam_input"]).fill("34")
    page.locator(SELECTORS["verify_btn"]).click()
    page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # ── Sub-level 3: Click the different color square ──
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
    wait_for_level_change(page)
    logger.info("[Level 24] Done.")
# ══════════════════════════════════════
#  Level 25: Creativity
# ══════════════════════════════════════
@register("Creativity")
def solve_level_25(page: Page) -> None:
    """Level 25: Express Yourself — set pass conditions directly."""
    logger.info("[Level 25] Waiting for canvas...")
    page.locator(SELECTORS["express_canvas"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "numDrawn", "inst.$data.numDrawn !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().numDrawn !== undefined
            );
            if (!inst) return {{ error: 'creativity component not found' }};
            inst.$data.numDrawn = 11;
            inst.$data.toolsUsed = {{
                brush:  true,
                spray:  true,
                pencil: true,
                eraser: true,
            }};
            inst.$data.differentColorUsed = true;
            return {{
                success: true,
                numDrawn: inst.$data.numDrawn,
                toolsUsed: inst.$data.toolsUsed,
                differentColorUsed: inst.$data.differentColorUsed,
                verify: inst.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 25] Override result: {result}")
    if not result or result.get("error"):
        raise LevelFailed(f"Level 25: {result.get('error', 'unknown')}")
    if not result.get("verify"):
        raise LevelFailed("Level 25: verify() still returns False")
    page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
    click_verify(page, "Level 25")
# ══════════════════════════════════════
#  Level 26: Parallel Parking
# ══════════════════════════════════════
@register("Parallel Parking")
def solve_level_26(page: Page) -> None:
    """Level 26: Parallel Parking — override checkParking.
    Uses the same <Park> component as Level 15.
    """
    logger.info("[Level 26] Waiting for canvas...")
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
            return {{
                success: true,
                startLevel: park.startLevel,
                endLevel: park.endLevel,
            }};
        }}
    """)
    logger.info(f"[Level 26] Override result: {result}")
    if not result or result.get("error"):
        raise LevelFailed(f"Level 26: {result.get('error', 'unknown')}")
    max_verifies = 10
    for i in range(max_verifies):
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
        level = page.locator(SELECTORS["level_text"]).inner_text()
        if "Parking" not in level:
            logger.info(f"[Level 26] Advanced to: {level}")
            return
        logger.info(f"[Level 26] Verify #{i + 1}")
        page.locator(SELECTORS["verify_btn"]).click()
        wait_for_level_change(page)
    raise LevelFailed("Level 26: too many verifications, still on Parking")
# ══════════════════════════════════════
#  Level 27: Networking
# ══════════════════════════════════════
#  Fixed endpoint pairs (from Flow component source):
#    #ff6b6b (red)    : 0  ↔ 27
#    #4ecdc4 (cyan)   : 5  ↔ 15
#    #ff8c42 (orange) : 26 ↔ 28
#    #f9ca24 (yellow) : 13 ↔ 3
#    #6c5ce7 (purple) : 11 ↔ 35
#    #fd79a8 (pink)   : 8  ↔ 14
FLOW_ENDPOINTS = {
    "#ff6b6b": (0, 27),
    "#4ecdc4": (5, 15),
    "#ff8c42": (26, 28),
    "#f9ca24": (13, 3),
    "#6c5ce7": (11, 35),
    "#fd79a8": (8, 14),
}
FLOW_GRID_SIZE = 6
def _flow_neighbors(idx: int, grid_size: int) -> list[int]:
    """Return the 4 adjacent cell indexes (up/down/left/right)."""
    row, col = divmod(idx, grid_size)
    result = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = row + dr, col + dc
        if 0 <= nr < grid_size and 0 <= nc < grid_size:
            result.append(nr * grid_size + nc)
    return result
def _flow_solve_paths(grid_size: int, pairs: list[tuple[int, int]]) -> list[list[int]] | None:
    """Find 6 non-overlapping paths that fill ALL cells.
    Uses backtracking: try to route one pair at a time, blocking cells
    already used by previous paths (except endpoints).
    Returns:
        List of 6 paths, or None if no solution found.
    """
    total = grid_size * grid_size
    # Track which cells are used by which path
    used_by: dict[int, int] = {}  # cell -> path index
    # All endpoints (any pair)
    all_endpoints = set()
    for a, b in pairs:
        all_endpoints.add(a)
        all_endpoints.add(b)
    paths: list[list[int]] = []
    def can_use(idx: int, path_idx: int) -> bool:
        """A cell can be used if it's unused, or it's an endpoint of THIS pair."""
        if idx not in used_by:
            return True
        # Can re-use an endpoint of the current pair
        a, b = pairs[path_idx]
        return idx in (a, b) and used_by[idx] == path_idx
    def dfs_path(path_idx: int, current: int, target: int, path: list[int], visited_in_path: set[int]) -> bool:
        """DFS from `current` to `target`. Returns True if path found."""
        if current == target and len(path) > 1:
            return True
        for nxt in _flow_neighbors(current, grid_size):
            if nxt in visited_in_path:
                continue
            if not can_use(nxt, path_idx):
                continue
            # If nxt is an endpoint of a DIFFERENT pair, skip
            if nxt in all_endpoints and nxt != target and nxt != pairs[path_idx][0]:
                continue
            visited_in_path.add(nxt)
            path.append(nxt)
            if dfs_path(path_idx, nxt, target, path, visited_in_path):
                return True
            path.pop()
            visited_in_path.remove(nxt)
        return False
    def place_path(path_idx: int) -> bool:
        """Try to place the path for pairs[path_idx], then recurse."""
        if path_idx == len(pairs):
            # Success: all paths placed
            return True
        a, b = pairs[path_idx]
        path = [a]
        visited = {a}
        if not dfs_path(path_idx, a, b, path, visited):
            return False
        # Check: does this path cover at least one new cell?
        for cell in path:
            if cell not in used_by:
                used_by[cell] = path_idx
        paths.append(path)
        if place_path(path_idx + 1):
            return True
        # Backtrack
        paths.pop()
        for cell in path:
            if used_by.get(cell) == path_idx:
                del used_by[cell]
        return False
    if place_path(0):
        # Check that all cells are covered
        covered = set()
        for p in paths:
            covered.update(p)
        if len(covered) == total:
            return paths
        else:
            # Not all cells covered — need to try different paths
            return None
    return None
def _flow_drag_path(page: Page, grid_locator, path: list[int]) -> None:
    """Simulate a mouse drag along the given cell path."""
    # Move to start and press
    first = grid_locator.nth(path[0])
    box = first.bounding_box()
    if not box:
        return
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.wait_for_timeout(30)
    # Move through each cell
    for idx in path[1:]:
        cell = grid_locator.nth(idx)
        cbox = cell.bounding_box()
        if not cbox:
            continue
        ccx = cbox["x"] + cbox["width"] / 2
        ccy = cbox["y"] + cbox["height"] / 2
        page.mouse.move(ccx, ccy, steps=3)
        page.wait_for_timeout(20)
    page.mouse.up()
    page.wait_for_timeout(80)
# ══════════════════════════════════════
#  Level 27: Networking
# ══════════════════════════════════════
#  Fixed endpoint pairs (from Flow component source):
#    #ff6b6b (red)    : 0  ↔ 27
#    #4ecdc4 (cyan)   : 5  ↔ 15
#    #ff8c42 (orange) : 26 ↔ 28
#    #f9ca24 (yellow) : 13 ↔ 3
#    #6c5ce7 (purple) : 11 ↔ 35
#    #fd79a8 (pink)   : 8  ↔ 14
FLOW_ENDPOINTS = [
    ("#ff6b6b", 0, 27),
    ("#4ecdc4", 5, 15),
    ("#ff8c42", 26, 28),
    ("#f9ca24", 13, 3),
    ("#6c5ce7", 11, 35),
    ("#fd79a8", 8, 14),
]
FLOW_GRID_SIZE = 6
def _flow_neighbors(idx: int, size: int) -> list[int]:
    """Return the 4 adjacent cell indexes (up/down/left/right)."""
    row, col = divmod(idx, size)
    result = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = row + dr, col + dc
        if 0 <= nr < size and 0 <= nc < size:
            result.append(nr * size + nc)
    return result
def _flow_solve_all_paths(size: int) -> list[list[int]] | None:
    """Find 6 non-overlapping paths that fill ALL 36 cells.
    Uses backtracking with a Warnsdorff-like heuristic: prefer cells
    with fewer onward options (dead-end first).
    Returns:
        List of 6 paths (each a list of cell indexes), or None if
        no solution was found.
    """
    total = size * size
    # Blocked map: cell index -> path index that uses it
    used_by: dict[int, int] = {}
    # All endpoint cells, mapped to their path index
    endpoint_owner: dict[int, int] = {}
    for path_idx, (_, a, b) in enumerate(FLOW_ENDPOINTS):
        endpoint_owner[a] = path_idx
        endpoint_owner[b] = path_idx
    paths: list[list[int]] = []
    def can_pass(idx: int, path_idx: int) -> bool:
        """Can this path pass through `idx`?"""
        # Already used by another path?
        if idx in used_by and used_by[idx] != path_idx:
            return False
        # Is it a foreign endpoint?
        if idx in endpoint_owner and endpoint_owner[idx] != path_idx:
            return False
        return True
    def dfs_path(path_idx: int, current: int, target: int,
                 path: list[int], visited: set[int]) -> bool:
        if current == target and len(path) > 1:
            return True
        # Warnsdorff: sort neighbors by fewest onward options
        candidates = []
        for nxt in _flow_neighbors(current, size):
            if nxt in visited:
                continue
            if not can_pass(nxt, path_idx):
                continue
            # Count onward options from nxt
            onward = 0
            for nn in _flow_neighbors(nxt, size):
                if nn in visited or nn == current:
                    continue
                if not can_pass(nn, path_idx):
                    continue
                onward += 1
            candidates.append((onward, nxt))
        candidates.sort()  # Fewest options first
        for _, nxt in candidates:
            visited.add(nxt)
            path.append(nxt)
            if dfs_path(path_idx, nxt, target, path, visited):
                return True
            path.pop()
            visited.remove(nxt)
        return False
    def place(path_idx: int) -> bool:
        """Try to place path #path_idx, then recurse to the next."""
        if path_idx == len(FLOW_ENDPOINTS):
            # All paths placed — check full coverage
            covered = set()
            for p in paths:
                covered.update(p)
            return len(covered) == total
        _, a, b = FLOW_ENDPOINTS[path_idx]
        path = [a]
        visited = {a}
        if not dfs_path(path_idx, a, b, path, visited):
            return False
        # Mark cells
        for cell in path:
            if cell not in used_by:
                used_by[cell] = path_idx
        paths.append(path)
        if place(path_idx + 1):
            return True
        # Backtrack
        paths.pop()
        for cell in path:
            if used_by.get(cell) == path_idx:
                del used_by[cell]
        return False
    if place(0):
        return paths
    return None
def _flow_drag_path(page: Page, grid_locator, path: list[int]) -> None:
    """Simulate a mouse drag along the given cell path."""
    first = grid_locator.nth(path[0])
    box = first.bounding_box()
    if not box:
        return
    cx = box["x"] + box["width"] / 2
    cy = box["y"] + box["height"] / 2
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.wait_for_timeout(40)
    for idx in path[1:]:
        cell = grid_locator.nth(idx)
        cbox = cell.bounding_box()
        if not cbox:
            continue
        ccx = cbox["x"] + cbox["width"] / 2
        ccy = cbox["y"] + cbox["height"] / 2
        page.mouse.move(ccx, ccy, steps=3)
        page.wait_for_timeout(25)
    page.mouse.up()
    page.wait_for_timeout(100)
@register("Networking")
def solve_level_27(page: Page) -> None:
    """Level 27: Networking — connect endpoint pairs to fill all squares.
    Strategy (Hybrid / Method C):
      1. Try to set $data directly (fast path).
      2. If that fails, compute paths via backtracking and simulate drags.
    """
    logger.info("[Level 27] Waiting for grid...")
    page.locator(SELECTORS["flow_grid"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "grid", "inst.$data.grid.length > 0")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # ── Method 1: Direct $data override ──
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().gridSize !== undefined
            );
            if (!inst) return {{ error: 'Flow component not found' }};
            // Mark every cell as having a path
            inst.$data.grid.forEach(cell => {{ cell.hasPath = true; }});
            // Mark every endpoint as connected
            inst.$data.endpoints.forEach(ep => {{ ep.isConnected = true; }});
            return {{
                success: true,
                filledCells: inst.filledCells,
                totalCells: inst.totalCells,
                allConnected: inst.endpoints.every(e => e.isConnected),
                isComplete: inst.isComplete,
            }};
        }}
    """)
    logger.info(f"[Level 27] Method 1 result: {result}")
    if result and result.get("isComplete"):
        logger.info("[Level 27] Method 1 (direct $data) succeeded!")
        page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
        click_verify(page, "Level 27")
        return
    # ── Method 2: Compute paths and simulate real drags ──
    logger.warning("[Level 27] Method 1 failed, switching to Method 2 "
                   "(backtracking + real drags)...")
    # Reset the puzzle so we start from a clean state
    page.locator(SELECTORS["refresh_btn"]).click()
    page.wait_for_timeout(TIMEOUTS["medium_wait"])
    paths = _flow_solve_all_paths(FLOW_GRID_SIZE)
    if not paths:
        raise LevelFailed("Level 27: could not compute a valid path solution")
    logger.info(f"[Level 27] Computed {len(paths)} paths "
                f"(total cells: {sum(len(p) for p in paths)})")
    grid_locator = page.locator(SELECTORS["flow_cell"])
    for i, path in enumerate(paths):
        color = FLOW_ENDPOINTS[i][0]
        logger.info(f"[Level 27] Drawing path {i + 1}/{len(paths)} "
                    f"({color}, length={len(path)})")
        _flow_drag_path(page, grid_locator, path)
        page.wait_for_timeout(TIMEOUTS["short_wait"])
    # Verify the puzzle is now complete
    final = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().gridSize !== undefined
            );
            if (!inst) return {{ error: 'Flow not found' }};
            return {{
                isComplete: inst.isComplete,
                filledCells: inst.filledCells,
                totalCells: inst.totalCells,
                allConnected: inst.endpoints.every(e => e.isConnected),
            }};
        }}
    """)
    logger.info(f"[Level 27] Final state: {final}")
    if not final or not final.get("isComplete"):
        raise LevelFailed(
            f"Level 27: puzzle not complete after real drags: {final}"
        )
    page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
    click_verify(page, "Level 27")
# ══════════════════════════════════════
#  Level 28: Day Trader
# ══════════════════════════════════════
@register("Day Trader")
def solve_level_28(page: Page) -> None:
    """Level 28: Day Trader — make $2,500 in the stock market.
    Strategy (Hybrid: Method 2 + Method 3 merged):
      1. Try direct $data override (fast path).
      2. Fallback: timing-based trading using Vue methods directly.
    The combined fallback reads real-time prices and calls
    inst.buy() / inst.sell() directly (no mouse clicks), which is
    both accurate AND fast.
    """
    logger.info("[Level 28] Waiting for stock market UI...")
    page.locator(SELECTORS["stock_buy_btn"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "balance", "inst.$data.balance !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # ── Method 1: Direct $data override ──
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().balance !== undefined
            );
            if (!inst) return {{ error: 'Day Trader component not found' }};
            inst.$data.balance = 3000;
            if (inst.$data.stocks && inst.$data.stocks[0]) {{
                inst.$data.stocks[0].realizedGains = 3000;
            }}
            return {{
                success: true,
                balance: inst.$data.balance,
                diff: inst.diff,
                verify: inst.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 28] Method 1 result: {result}")
    if result and result.get("verify"):
        logger.info("[Level 28] Method 1 (direct $data) succeeded!")
        page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
        click_verify(page, "Level 28")
        return
    # ── Method 2+3 merged: Timing-based trading via Vue methods ──
    logger.warning("[Level 28] Method 1 failed, using Method 2+3 "
                   "(timing-based trading via Vue methods)...")
    start = time.time()
    timeout = 90  # 90-second hard cap
    trades = 0
    while time.time() - start < timeout:
        # Read current state and decide the action
        action = page.evaluate(f"""
            () => {{
                const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
                if (!pageVm) return {{ error: 'pageVm not found' }};
                const inst = pageVm.$children.find(c =>
                    c.$options && c.$options.data &&
                    c.$options.data().balance !== undefined
                );
                if (!inst) return {{ error: 'not found' }};
                // Already won?
                if (inst.verify()) {{
                    return {{
                        action: 'done',
                        balance: inst.balance,
                        diff: inst.diff,
                    }};
                }}
                const price = inst.lastPrice;
                const shares = inst.shares;
                const balance = inst.balance;
                const avgCost = shares > 0
                    ? inst.selectedStockObj.totalCost / shares
                    : 0;
                // Look at recent price history to gauge trend
                const history = inst.selectedStockObj.data;
                const recent = history.slice(-10).map(d => d.val);
                const minRecent = Math.min(...recent);
                const maxRecent = Math.max(...recent);
                const range = maxRecent - minRecent;
                // Decision logic:
                // 1. If flat (no shares), buy at a low point
                // 2. If holding, sell at a high point or with profit
                let act = 'wait';
                if (shares === 0) {{
                    // Buy when price is in the lower 30% of recent range
                    if (balance >= price && price <= minRecent + range * 0.3) {{
                        act = 'buy';
                    }}
                }} else {{
                    // Sell when price is in the upper 30% of recent range
                    // OR we have a profit
                    const hasProfit = price > avgCost * 1.01;
                    const isHigh = price >= maxRecent - range * 0.3;
                    if (hasProfit && isHigh) {{
                        act = 'sell';
                    }} else if (hasProfit && price >= maxRecent - range * 0.1) {{
                        // Fallback: near the peak, just sell
                        act = 'sell';
                    }}
                }}
                return {{
                    action: act,
                    price: price,
                    shares: shares,
                    balance: balance,
                    avgCost: avgCost,
                    minRecent: minRecent,
                    maxRecent: maxRecent,
                    diff: inst.diff,
                }};
            }}
        """)
        if not action or action.get("error"):
            logger.warning(f"[Level 28] State read error: {action}")
            break
        act = action["action"]
        if act == "done":
            logger.info(f"[Level 28] Completed! balance={action['balance']}, "
                        f"diff={action['diff']}")
            break
        if act == "buy":
            # Call inst.buy() directly (Method 3)
            page.evaluate(f"""
                () => {{
                    const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
                    const inst = pageVm.$children.find(c =>
                        c.$options && c.$options.data &&
                        c.$options.data().balance !== undefined
                    );
                    if (inst) inst.buy();
                }}
            """)
            trades += 1
            logger.info(f"[Level 28] BUY  @ ${action['price']} "
                        f"(trades={trades}, balance=${action['balance']})")
        elif act == "sell":
            page.evaluate(f"""
                () => {{
                    const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
                    const inst = pageVm.$children.find(c =>
                        c.$options && c.$options.data &&
                        c.$options.data().balance !== undefined
                    );
                    if (inst) inst.sell();
                }}
            """)
            trades += 1
            logger.info(f"[Level 28] SELL @ ${action['price']} "
                        f"(trades={trades}, diff=${action['diff']:.0f})")
        # Wait for the next price tick (500ms interval) — Method 2
        page.wait_for_timeout(500)
    # ── Final verification ──
    final = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().balance !== undefined
            );
            if (!inst) return null;
            return {{
                balance: inst.balance,
                diff: inst.diff,
                verify: inst.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 28] Final state: {final}")
    if not final or not final.get("verify"):
        raise LevelFailed(f"Level 28: could not reach $2,500: {final}")
    page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
    click_verify(page, "Level 28")
# ══════════════════════════════════════
#  Level 29: Soul
# ══════════════════════════════════════
#  From the Soul component source (module 1117):
#    answers = [0, 5, 7]      ← fixed, never changes
#    Selecting index 3         ← instant fail
#    Need >= 8/9 correct matches
#
#  The verify() method reads this.$refs.grid.getSelected(),
#  which reads the Grid component's `items` array.
SOUL_ANSWERS = [0, 5, 7]
@register("Soul")
def solve_level_29(page: Page) -> None:
    """Level 29: Soul — click cells 0, 5, 7 (the ones with a soul).
    Strategy (Hybrid / Method C):
      1. Try to set the Grid component's `items` array directly.
      2. Fallback: click the correct grid items in the DOM.
    """
    logger.info("[Level 29] Waiting for grid...")
    page.locator(SELECTORS["soul_grid"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "answers", "inst.$data.answers !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # ── Method 1: Direct $data override on the Grid component ──
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            // Find the Soul component (has `answers` in its $data)
            const soul = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().answers !== undefined
            );
            if (!soul) return {{ error: 'Soul component not found' }};
            // Read the answers array
            const answers = [...soul.$data.answers];
            // Find the child Grid component (has `items` in its $data)
            const grid = soul.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().items !== undefined
            );
            if (!grid) return {{ error: 'Grid component not found' }};
            // Mark only the correct cells as selected
            const items = grid.$data.items;
            for (let i = 0; i < items.length; i++) {{
                items[i] = answers.includes(i);
            }}
            // Verify
            const selected = grid.getSelected();
            const verifyResult = soul.verify();
            return {{
                success: true,
                answers: answers,
                selected: selected,
                verify: verifyResult,
            }};
        }}
    """)
    logger.info(f"[Level 29] Method 1 result: {result}")
    if result and result.get("verify"):
        logger.info("[Level 29] Method 1 (direct $data) succeeded!")
        page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
        click_verify(page, "Level 29")
        return
    # ── Method 2: Real clicks on the correct grid items ──
    logger.warning("[Level 29] Method 1 failed, using Method 2 "
                   "(real clicks)...")
    items = page.locator(SELECTORS["soul_item"])
    total = items.count()
    logger.info(f"[Level 29] Total cells: {total}")
    for idx in SOUL_ANSWERS:
        logger.info(f"[Level 29] Clicking cell {idx}")
        items.nth(idx).click()
        page.wait_for_timeout(TIMEOUTS["fast_click_wait"])
    # Verify state after clicks
    final = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const soul = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().answers !== undefined
            );
            if (!soul) return {{ error: 'Soul not found' }};
            const grid = soul.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().items !== undefined
            );
            return {{
                selected: grid ? grid.getSelected() : [],
                verify: soul.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 29] Final state: {final}")
    if not final or not final.get("verify"):
        raise LevelFailed(f"Level 29: verify() still False: {final}")
    page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
    click_verify(page, "Level 29")
# ══════════════════════════════════════
#  Level 30: Sliding Tiles
# ══════════════════════════════════════
#  From the SlidingPuzzle component source (module 1114):
#    gridSize = 3
#    tiles    = [1, 2, 3, 4, 5, 6, 7, 8, 0]   ← solved state
#    verify() compares tiles array with the solved state
SLIDING_SOLVED = [1, 2, 3, 4, 5, 6, 7, 8, 0]
@register("Sliding Tiles")
def solve_level_30(page: Page) -> None:
    """Level 30: Sliding Tiles — set tiles array to solved state.
    Strategy (Hybrid / Method C):
      1. Try to set the tiles array directly (fast path).
      2. Fallback: solve the puzzle via BFS + moveTile() calls.
    """
    logger.info("[Level 30] Waiting for puzzle...")
    page.locator(SELECTORS["sliding_container"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "tiles", "inst.$data.tiles.length > 0")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # ── Method 1: Direct $data override ──
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().tiles !== undefined
            );
            if (!inst) return {{ error: 'SlidingPuzzle component not found' }};
            // Solved state
            const solved = [1, 2, 3, 4, 5, 6, 7, 8, 0];
            // Set the tiles array
            inst.$data.tiles = [...solved];
            // Rebuild tilePositions (number -> position map)
            const positions = {{}};
            solved.forEach((tile, idx) => {{
                positions[tile] = idx;
            }});
            inst.$data.tilePositions = positions;
            // Mark as solved
            inst.$data.solved = true;
            // Verify
            return {{
                success: true,
                tiles: [...inst.$data.tiles],
                verify: inst.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 30] Method 1 result: {result}")
    if result and result.get("verify"):
        logger.info("[Level 30] Method 1 (direct $data) succeeded!")
        page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
        click_verify(page, "Level 30")
        return
    # ── Method 2: BFS solve + real moveTile() calls ──
    logger.warning("[Level 30] Method 1 failed, using Method 2 "
                   "(BFS + real moves)...")
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().tiles !== undefined
            );
            if (!inst) return {{ error: 'SlidingPuzzle not found' }};
            const N = inst.$data.gridSize;
            const start = [...inst.$data.tiles];
            const goal = [1, 2, 3, 4, 5, 6, 7, 8, 0];
            const key = arr => arr.join(',');
            const visited = new Set([key(start)]);
            const queue = [{{ state: start, path: [] }}];
            const goalKey = key(goal);
            const neighbors = (state) => {{
                const emptyIdx = state.indexOf(0);
                const r = Math.floor(emptyIdx / N);
                const c = emptyIdx % N;
                const moves = [];
                const dirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
                for (const [dr, dc] of dirs) {{
                    const nr = r + dr;
                    const nc = c + dc;
                    if (nr < 0 || nr >= N || nc < 0 || nc >= N) continue;
                    const swapIdx = nr * N + nc;
                    const newState = [...state];
                    [newState[emptyIdx], newState[swapIdx]] = [newState[swapIdx], newState[emptyIdx]];
                    moves.push({{ state: newState, tileIdx: swapIdx }});
                }}
                return moves;
            }};
            // BFS
            let solution = null;
            let iterations = 0;
            const maxIterations = 200000;
            while (queue.length > 0 && iterations < maxIterations) {{
                const {{ state, path }} = queue.shift();
                iterations++;
                if (key(state) === goalKey) {{
                    solution = path;
                    break;
                }}
                for (const {{ state: next, tileIdx }} of neighbors(state)) {{
                    const k = key(next);
                    if (!visited.has(k)) {{
                        visited.add(k);
                        queue.push({{ state: next, path: [...path, tileIdx] }});
                    }}
                }}
            }}
            if (!solution) {{
                return {{ error: 'No solution found', iterations: iterations }};
            }}
            // Apply the moves via moveTile
            for (const tileIdx of solution) {{
                inst.moveTile(tileIdx);
            }}
            return {{
                success: true,
                moves: solution.length,
                iterations: iterations,
                tiles: [...inst.$data.tiles],
                verify: inst.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 30] Method 2 result: {result}")
    if not result or result.get("error"):
        raise LevelFailed(f"Level 30: {result.get('error', 'unknown')}")
    if not result.get("verify"):
        raise LevelFailed(f"Level 30: verify() still False: {result}")
    page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
    click_verify(page, "Level 30")
# ══════════════════════════════════════
#  Level 31: Traffic Tree
# ══════════════════════════════════════
#  From the Traffic Tree component source (module 1123):
#    correct = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
#    gridSize = 4  (16 cells, index 0-15)
#    Wrong cells: 0 and 3 (top-left and top-right corners)
TRAFFIC_TREE_CORRECT = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
@register("Traffic Tree")
def solve_level_31(page: Page) -> None:
    """Level 31: Traffic Tree — click all cells with a traffic light.
    Strategy (Hybrid / Method C):
      1. Try to set the Grid's items array directly (via $refs).
      2. Fallback: click each correct grid item.
    From source:
      - correct = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
      - gridSize = 4 (16 cells)
      - Wrong cells: 0 and 3
    """
    logger.info("[Level 31] Waiting for grid...")
    page.locator(SELECTORS["traffic_tree_grid"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "correct", "inst.$data.correct !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # ── Method 1: Direct $data override on the Grid component ──
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            // Find the Traffic Tree component (has `correct` in its $data)
            const tree = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().correct !== undefined
            );
            if (!tree) return {{ error: 'Traffic Tree component not found' }};
            // Read the correct answers
            const correct = [...tree.$data.correct];
            // Find the Grid component via $refs
            const grid = tree.$refs.grid;
            if (!grid) return {{ error: 'Grid ref not found' }};
            // Mark only the correct cells as selected
            const items = grid.$data.items;
            for (let i = 0; i < items.length; i++) {{
                items[i] = correct.includes(i);
            }}
            // Verify
            const selected = grid.getSelected();
            const verifyResult = tree.verify();
            return {{
                success: true,
                correct: correct,
                selected: selected,
                verify: verifyResult,
            }};
        }}
    """)
    logger.info(f"[Level 31] Method 1 result: {result}")
    if result and result.get("verify"):
        logger.info("[Level 31] Method 1 (direct $data) succeeded!")
        page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
        click_verify(page, "Level 31")
        return
    # ── Method 2: Real clicks on correct grid items ──
    logger.warning("[Level 31] Method 1 failed, using Method 2 "
                   "(real clicks)...")
    items = page.locator(SELECTORS["traffic_tree_item"])
    total = items.count()
    logger.info(f"[Level 31] Total cells: {total}")
    for idx in TRAFFIC_TREE_CORRECT:
        logger.info(f"[Level 31] Clicking cell {idx}")
        items.nth(idx).click()
        page.wait_for_timeout(TIMEOUTS["fast_click_wait"])
    # Verify state after clicks
    final = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const tree = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().correct !== undefined
            );
            if (!tree) return {{ error: 'Tree not found' }};
            const grid = tree.$refs.grid;
            return {{
                selected: grid ? grid.getSelected() : [],
                verify: tree.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 31] Final state: {final}")
    if not final or not final.get("verify"):
        raise LevelFailed(f"Level 31: verify() still False: {final}")
    page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
    click_verify(page, "Level 31")
# ══════════════════════════════════════
#  Level 32: Drum Verify
# ══════════════════════════════════════
#  From the DrumVerify component source (module 1081):
#    gameState: "idle" | "waiting" | "watching" | "playing" | "failed" | "success"
#    handleVerify() returns gameState === "success"
#
#  To pass: complete 3 sub-levels (level 0, 1, 2) correctly.
#  Each sub-level shows a sequence the user must repeat.
#
#  Easiest: set gameState = "success" directly.
#  Fallback: read targetSequence and click the correct pads.
@register("Drum Verify")
def solve_level_32(page: Page) -> None:
    """Level 32: Drum Verify — set gameState to 'success'.
    Strategy (Hybrid / Method C):
      1. Try to set gameState = 'success' directly (fast path).
      2. Fallback: read targetSequence and click the correct pads.
    """
    logger.info("[Level 32] Waiting for launchpad...")
    page.locator(SELECTORS["drum_container"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "gameState", "inst.$data.gameState !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # Wait a moment for the component to finish initializing
    page.wait_for_timeout(TIMEOUTS["short_wait"])
    # ── Method 1: Direct gameState override ──
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().gameState !== undefined
            );
            if (!inst) return {{ error: 'DrumVerify component not found' }};
            // Set gameState to "success"
            inst.$data.gameState = "success";
            inst.$data.isPlayingSequence = false;
            // Verify
            return {{
                success: true,
                gameState: inst.$data.gameState,
                verify: inst.handleVerify(),
            }};
        }}
    """)
    logger.info(f"[Level 32] Method 1 result: {result}")
    if result and result.get("verify"):
        logger.info("[Level 32] Method 1 (direct gameState) succeeded!")
        page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
        click_verify(page, "Level 32")
        return
    # ── Method 2: Play 3 rounds by clicking the correct pads ──
    logger.warning("[Level 32] Method 1 failed, using Method 2 "
                   "(play 3 rounds)...")
    drum_pads = page.locator(SELECTORS["drum_pad"])
    total = drum_pads.count()
    logger.info(f"[Level 32] Total pads: {total}")
    rounds_completed = 0
    max_rounds = 10  # safety limit
    for round_idx in range(max_rounds):
        # Wait until game is in "playing" state (user can click)
        try:
            page.wait_for_function(
                f"""() => {{
                    const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
                    const inst = pageVm.$children.find(c =>
                        c.$options && c.$options.data &&
                        c.$options.data().gameState !== undefined
                    );
                    return inst && inst.$data.gameState === 'playing';
                }}""",
                timeout=10000,
            )
        except Exception:
            logger.warning(f"[Level 32] Round {round_idx + 1}: "
                           f"timeout waiting for 'playing' state")
            break
        # Read the target sequence
        seq = page.evaluate(f"""
            () => {{
                const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
                const inst = pageVm.$children.find(c =>
                    c.$options && c.$options.data &&
                    c.$options.data().gameState !== undefined
                );
                return inst ? {{
                    targetSequence: [...inst.$data.targetSequence],
                    level: inst.$data.level,
                    gameState: inst.$data.gameState,
                }} : null;
            }}
        """)
        if not seq:
            logger.warning("[Level 32] Could not read sequence")
            break
        logger.info(f"[Level 32] Round {round_idx + 1}: "
                    f"level={seq['level']}, "
                    f"sequence={seq['targetSequence']}")
        # Click each pad in order
        for pad_idx in seq["targetSequence"]:
            try:
                drum_pads.nth(pad_idx).click(timeout=2000)
                page.wait_for_timeout(80)
            except Exception as e:
                logger.warning(f"[Level 32] Click pad {pad_idx} failed: {e}")
        # Wait for state transition
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
        # Check if we reached success
        state = page.evaluate(f"""
            () => {{
                const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
                const inst = pageVm.$children.find(c =>
                    c.$options && c.$options.data &&
                    c.$options.data().gameState !== undefined
                );
                return inst ? {{
                    gameState: inst.$data.gameState,
                    level: inst.$data.level,
                }} : null;
            }}
        """)
        logger.info(f"[Level 32] After round {round_idx + 1}: {state}")
        if state and state.get("gameState") == "success":
            rounds_completed = round_idx + 1
            logger.info(f"[Level 32] Success after {rounds_completed} rounds!")
            break
    # Final verify
    final = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().gameState !== undefined
            );
            return inst ? {{
                gameState: inst.$data.gameState,
                verify: inst.handleVerify(),
            }} : null;
        }}
    """)
    logger.info(f"[Level 32] Final state: {final}")
    if not final or not final.get("verify"):
        raise LevelFailed(f"Level 32: could not reach success: {final}")
    page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
    click_verify(page, "Level 32")
# ══════════════════════════════════════
#  Level 33: Brands
# ══════════════════════════════════════
#  From the Brands component source (module 1076):
#    brands = ["adobe", "bing", ..., "honda"]  (17 brands)
#    list   = 5 random brands, shown as images
#    verify(text) = text[0..4] must match the first letter of each brand
#
#  Strategy: hybrid — try both methods in ONE evaluate call and
#  use whichever produces a non-empty answer.
@register("Brands")
def solve_level_33(page: Page) -> None:
    """Level 33: Brands — read the 5 brands and type their first letters.
    Hybrid strategy (both methods in one JS call):
      A. Read `list` from Vue $data.
      B. Read `<img class="brand-letter">` src filenames.
      Use whichever returns a non-empty string.
    """
    logger.info("[Level 33] Waiting for brands...")
    page.locator(SELECTORS["brand_container"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "brands", "inst.$data.brands !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # ── Hybrid: try both methods in ONE evaluate call ──
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            // ── Method A: read from Vue $data.list ──
            let answerA = null;
            if (pageVm) {{
                const inst = pageVm.$children.find(c =>
                    c.$options && c.$options.data &&
                    c.$options.data().brands !== undefined
                );
                if (inst && inst.$data.list && inst.$data.list.length) {{
                    answerA = inst.$data.list.map(brand => brand[0]).join('');
                }}
            }}
            // ── Method B: read from image src filenames ──
            let answerB = null;
            const images = document.querySelectorAll('{SELECTORS["brand_image"]}');
            if (images.length) {{
                answerB = [...images].map(img => {{
                    const m = img.src.match(/\\/brands\\/([^\\/]+)\\.svg/);
                    return m ? m[1][0] : '';
                }}).join('');
            }}
            // ── Decide: use whichever is non-empty ──
            const answer = answerA || answerB || null;
            return {{
                answer: answer,
                methodA: answerA,
                methodB: answerB,
                source: answerA ? 'vue' : (answerB ? 'dom' : 'none'),
            }};
        }}
    """)
    logger.info(f"[Level 33] Hybrid result: {result}")
    if not result or not result.get("answer"):
        raise LevelFailed(f"Level 33: could not determine answer: {result}")
    answer = result["answer"]
    source = result.get("source", "?")
    logger.info(f"[Level 33] Answer: {answer!r} (from {source})")
    # ── Fill in the answer and submit ──
    page.locator(SELECTORS["brand_input"]).fill(answer)
    page.wait_for_timeout(TIMEOUTS["fast_click_wait"])
    page.locator(SELECTORS["brand_submit"]).click()
    wait_for_level_change(page)
    logger.info("[Level 33] Submitted.")
# ══════════════════════════════════════
#  Level 34: Mathematics
# ══════════════════════════════════════
#  From the MathCaptcha component source (module 1097):
#    gridSize = 3
#    terms = 9 math expressions with `.actual` values
#    selectedOrder = the user's click order
#    verify() = selectedOrder must match sorted-by-actual index order
#
#  Strategy (3-way fallback chain):
#    1. Set `selectedOrder` directly (fastest)
#    2. Simulate real clicks (most authentic)
#    3. Override `verify()` (most reliable)
@register("Mathematics")
def solve_level_34(page: Page) -> None:
    """Level 34: Mathematics — sort terms and set selectedOrder.
    Strategy (3-way fallback chain):
      1. Try direct `selectedOrder` override (fastest).
      2. If that fails, fall back to real clicks (most authentic).
      3. If that fails, override `verify()` (most reliable).
    """
    logger.info("[Level 34] Waiting for math grid...")
    page.locator(SELECTORS["math_grid_item"]).first.wait_for(state="visible")
    try:
        wait_for_vue(page, "terms", "inst.$data.terms.length > 0")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # ── Method 1: Set selectedOrder directly ──
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            const inst = pageVm.$children.find(c =>
                c && c.$data && c.$data.terms !== undefined
            );
            if (!inst) return {{ error: 'math component not found' }};
            // Sort term indexes by actual value (least to greatest)
            const sorted = [...inst.terms.keys()].sort((a, b) =>
                inst.terms[a].actual - inst.terms[b].actual
            );
            // Set selectedOrder directly
            inst.selectedOrder = sorted;
            return {{
                success: true,
                sorted: sorted,
                values: sorted.map(i => inst.terms[i].actual),
                verify: inst.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 34] Method 1 (set selectedOrder): {result}")
    if result and result.get("verify"):
        logger.info(f"[Level 34] Method 1 succeeded! "
                    f"order={result.get('sorted')}")
        page.wait_for_timeout(TIMEOUTS["short_wait"])
        click_verify(page, "Level 34")
        return
    # ── Method 2: Real clicks in sorted order ──
    logger.warning("[Level 34] Method 1 failed, "
                   "trying Method 2 (real clicks)...")
    sorted_indexes = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c && c.$data && c.$data.terms !== undefined
            );
            if (!inst) return null;
            return [...inst.terms.keys()].sort((a, b) =>
                inst.terms[a].actual - inst.terms[b].actual
            );
        }}
    """)
    if sorted_indexes:
        logger.info(f"[Level 34] Clicking in order: {sorted_indexes}")
        # Reset any prior selection state
        page.evaluate(f"""
            () => {{
                const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
                const inst = pageVm.$children.find(c =>
                    c && c.$data && c.$data.terms !== undefined
                );
                if (inst) inst.selectedOrder = [];
            }}
        """)
        page.wait_for_timeout(TIMEOUTS["fast_click_wait"])
        items = page.locator(SELECTORS["math_grid_item"])
        for idx in sorted_indexes:
            items.nth(idx).click()
            page.wait_for_timeout(TIMEOUTS["quick_click_wait"])
        # Check verify after clicks
        verify_result = page.evaluate(f"""
            () => {{
                const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
                const inst = pageVm.$children.find(c =>
                    c && c.$data && c.$data.terms !== undefined
                );
                return inst ? inst.verify() : false;
            }}
        """)
        if verify_result:
            logger.info("[Level 34] Method 2 succeeded!")
            page.wait_for_timeout(TIMEOUTS["short_wait"])
            click_verify(page, "Level 34")
            return
    # ── Method 3: Override verify() ──
    logger.warning("[Level 34] Method 2 failed, "
                   "using Method 3 (override verify)...")
    override = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c && c.$data && c.$data.terms !== undefined
            );
            if (!inst) return {{ error: 'not found' }};
            inst.verify = function() {{ return true; }};
            return {{ success: true }};
        }}
    """)
    logger.info(f"[Level 34] Method 3 (override verify): {override}")
    if not override or override.get("error"):
        raise LevelFailed("Level 34: all 3 methods failed")
    page.wait_for_timeout(TIMEOUTS["short_wait"])
    click_verify(page, "Level 34")
# ══════════════════════════════════════
#  Level 35: Shuffle
# ══════════════════════════════════════
#  From the CupsCaptcha component source (module 1080):
#    cups = [0, 1, 2]        (visual position -> cup index)
#    ballIndex = which cup has the ball
#    level = 0, 1, 2         (must reach 3 to pass)
#    verify() = level === 3
#
#  Strategy (3-way fallback chain):
#    1. Set `level = 3` directly (fastest)
#    2. Simulate real guesses (most authentic)
#    3. Override `verify()` (most reliable)
@register("Shuffle")
def solve_level_35(page: Page) -> None:
    """Level 35: Shuffle — find the ball 3 times in a row.
    Strategy (3-way fallback chain):
      1. Set `level = 3` directly (fastest).
      2. If that fails, override `verify()` (most reliable).
      3. Real play is skipped — too slow (~20+ seconds).
    """
    logger.info("[Level 35] Waiting for cups...")
    page.locator(SELECTORS["cups_container"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "cups", "inst.$data.cups !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # ── Method 1: Set level = 3 directly ──
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            const inst = pageVm.$children.find(c =>
                c && c.$data && c.$data.cups !== undefined
            );
            if (!inst) return {{ error: 'CupsCaptcha component not found' }};
            inst.$data.level = 3;
            return {{
                success: true,
                level: inst.$data.level,
                verify: inst.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 35] Method 1 (set level=3): {result}")
    if result and result.get("verify"):
        logger.info("[Level 35] Method 1 succeeded!")
        page.wait_for_timeout(TIMEOUTS["short_wait"])
        click_verify(page, "Level 35")
        return
    # ── Method 2: Override verify() ──
    logger.warning("[Level 35] Method 1 failed, "
                   "using Method 2 (override verify)...")
    override = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c && c.$data && c.$data.cups !== undefined
            );
            if (!inst) return {{ error: 'not found' }};
            inst.verify = function() {{ return true; }};
            return {{ success: true }};
        }}
    """)
    logger.info(f"[Level 35] Method 2 (override verify): {override}")
    if not override or override.get("error"):
        raise LevelFailed("Level 35: all methods failed")
    page.wait_for_timeout(TIMEOUTS["short_wait"])
    click_verify(page, "Level 35")
# ══════════════════════════════════════
#  Level 36: Not Candy Crush
# ══════════════════════════════════════
#  From the Match-3 component source (module 1078):
#    score = 0
#    targetScore = 1000
#    handleVerify() = score >= targetScore
#
#  Strategy (3-way fallback chain):
#    1. Set `score = 1000` directly (fastest).
#    2. Override `handleVerify()` (most reliable).
@register("Not Candy Crush")
def solve_level_36(page: Page) -> None:
    """Level 36: Not Candy Crush — set score to 1000 or override verify.
    Strategy (3-way fallback chain):
      1. Set `score = 1000` directly (fastest).
      2. Override `handleVerify()` (most reliable).
    """
    logger.info("[Level 36] Waiting for match-3 game...")
    page.locator(SELECTORS["match3_game"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "score", "inst.$data.score !== undefined")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # ── Method 1: Set score directly ──
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().score !== undefined
            );
            if (!inst) return {{ error: 'Match-3 component not found' }};
            inst.$data.score = 1000;
            inst.$data.gameOver = true;
            return {{
                success: true,
                score: inst.$data.score,
                verify: inst.handleVerify(),
            }};
        }}
    """)
    logger.info(f"[Level 36] Method 1 (set score=1000): {result}")
    if result and result.get("verify"):
        logger.info("[Level 36] Method 1 succeeded!")
        page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
        click_verify(page, "Level 36")
        return
    # ── Method 2: Override handleVerify ──
    logger.warning("[Level 36] Method 1 failed, "
                   "using Method 2 (override handleVerify)...")
    override = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().score !== undefined
            );
            if (!inst) return {{ error: 'not found' }};
            inst.handleVerify = function() {{ return true; }};
            return {{ success: true }};
        }}
    """)
    logger.info(f"[Level 36] Method 2 (override handleVerify): {override}")
    if not override or override.get("error"):
        raise LevelFailed("Level 36: all methods failed")
    page.wait_for_timeout(TIMEOUTS["short_wait"])
    click_verify(page, "Level 36")
# ══════════════════════════════════════
#  Level 37: Imposters
# ══════════════════════════════════════
#  From the Imposters component source (module 1093):
#    people = [1..9] shuffled  (position -> person ID)
#    correct = [1, 6, 7, 9]    (fixed! which people are AI)
#    threshold = 1             (allow 1 mistake)
#    verify() = selected matches correct within threshold
#
#  Strategy (3-way fallback chain):
#    1. Set Grid.items directly based on `people` + `correct`.
#    2. Real clicks on correct positions.
#    3. Override verify().
@register("Imposters")
def solve_level_37(page: Page) -> None:
    """Level 37: Imposters — select the AI-generated men.
    Strategy (3-way fallback chain):
      1. Set `Grid.items` directly based on `people` + `correct`.
      2. Real clicks on correct positions.
      3. Override `verify()`.
    """
    logger.info("[Level 37] Waiting for imposters grid...")
    page.locator(SELECTORS["imposters_grid"]).wait_for(state="visible")
    try:
        wait_for_vue(page, "people", "inst.$data.people.length > 0")
    except Exception:
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # ── Method 1: Set Grid.items directly ──
    result = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().people !== undefined
            );
            if (!inst) return {{ error: 'Imposters component not found' }};
            const people = inst.$data.people;
            const correct = inst.$data.correct;
            const grid = inst.$refs.grid;
            if (!grid) return {{ error: 'Grid ref not found' }};
            // Mark items that correspond to correct person IDs
            const items = grid.$data.items;
            for (let i = 0; i < people.length; i++) {{
                items[i] = correct.includes(people[i]);
            }}
            return {{
                success: true,
                people: [...people],
                correct: [...correct],
                selected: grid.getSelected(),
                verify: inst.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 37] Method 1 result: {result}")
    if result and result.get("verify"):
        logger.info("[Level 37] Method 1 (set Grid.items) succeeded!")
        page.wait_for_timeout(TIMEOUTS["cell_click_wait"])
        click_verify(page, "Level 37")
        return
    # ── Method 2: Real clicks on correct positions ──
    logger.warning("[Level 37] Method 1 failed, "
                   "trying Method 2 (real clicks)...")
    indices = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().people !== undefined
            );
            if (!inst) return null;
            const people = inst.$data.people;
            const correct = inst.$data.correct;
            const result = [];
            for (let i = 0; i < people.length; i++) {{
                if (correct.includes(people[i])) result.push(i);
            }}
            return result;
        }}
    """)
    if indices:
        logger.info(f"[Level 37] Clicking positions: {indices}")
        # Reset prior selection first
        page.evaluate(f"""
            () => {{
                const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
                const inst = pageVm.$children.find(c =>
                    c.$options && c.$options.data &&
                    c.$options.data().people !== undefined
                );
                if (inst && inst.$refs.grid) inst.$refs.grid.reset();
            }}
        """)
        page.wait_for_timeout(TIMEOUTS["fast_click_wait"])
        items = page.locator(SELECTORS["imposters_item"])
        for idx in indices:
            items.nth(idx).click()
            page.wait_for_timeout(TIMEOUTS["fast_click_wait"])
        # Check verify
        verify_result = page.evaluate(f"""
            () => {{
                const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
                const inst = pageVm.$children.find(c =>
                    c.$options && c.$options.data &&
                    c.$options.data().people !== undefined
                );
                return inst ? inst.verify() : false;
            }}
        """)
        if verify_result:
            logger.info("[Level 37] Method 2 succeeded!")
            page.wait_for_timeout(TIMEOUTS["short_wait"])
            click_verify(page, "Level 37")
            return
    # ── Method 3: Override verify ──
    logger.warning("[Level 37] Method 2 failed, "
                   "using Method 3 (override verify)...")
    override = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().people !== undefined
            );
            if (!inst) return {{ error: 'not found' }};
            inst.verify = function() {{ return true; }};
            return {{ success: true }};
        }}
    """)
    logger.info(f"[Level 37] Method 3 (override verify): {override}")
    if not override or override.get("error"):
        raise LevelFailed("Level 37: all 3 methods failed")
    page.wait_for_timeout(TIMEOUTS["short_wait"])
    click_verify(page, "Level 37")
# ══════════════════════════════════════
#  Level 38: Tough Decisions
# ══════════════════════════════════════
#  From the Tough Decisions component source (module 1103):
#    Uses the SAME <Park> component as Level 15 and Level 26.
#    startLevel = 4, endLevel = 4  (only 1 sub-level)
#    Background image: level-5.webp
#
#  Strategy: reuse the same checkParking override as Level 15/26.
@register("Tough Decisions")
def solve_level_38(page: Page) -> None:
    """Level 38: Tough Decisions — same <Park> component as Level 15/26.
    Only 1 sub-level (startLevel=4, endLevel=4), so we just need
    to override checkParking and verify once.
    """
    logger.info("[Level 38] Waiting for canvas...")
    page.locator(SELECTORS["park_canvas"]).wait_for(state="visible")
    # 初始化元件
    page.locator(SELECTORS["park_canvas"]).click()
    page.wait_for_timeout(TIMEOUTS["short_wait"])
    page.keyboard.press("ArrowUp")
    page.wait_for_timeout(TIMEOUTS["medium_wait"])
    # 覆寫 checkParking
    result = page.evaluate(f"""
        () => {{
            let el = document.querySelector('{SELECTORS["park_canvas"]}');
            let gridCaptcha = null;
            // 往上找有 $data.squares 的 GridCaptcha 元件
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
            return {{
                success: true,
                startLevel: park.startLevel,
                endLevel: park.endLevel,
            }};
        }}
    """)
    logger.info(f"[Level 38] Override result: {result}")
    if not result or result.get("error"):
        raise LevelFailed(f"Level 38: {result.get('error', 'unknown')}")
    # 自動偵測：最多 5 次驗證（安全上限）
    # startLevel=4, endLevel=4 → 只需 1 次
    max_verifies = 5
    for i in range(max_verifies):
        page.wait_for_timeout(TIMEOUTS["medium_wait"])
        level = page.locator(SELECTORS["level_text"]).inner_text()
        if "Tough Decisions" not in level:
            logger.info(f"[Level 38] Advanced to: {level}")
            return
        logger.info(f"[Level 38] Verify #{i + 1}")
        page.locator(SELECTORS["verify_btn"]).click()
        wait_for_level_change(page)
    raise LevelFailed("Level 38: too many verifications, still on Tough Decisions")
# ══════════════════════════════════════
#  Level 39: Facial Exam
# ══════════════════════════════════════
#  From the FacialExam component source (module 1083):
#    - Uses webcam + face-api.js to detect 4 emotions
#    - verify() returns `!!this.noCamera` if confidence is low
#    - "noCamera" is set true when getUserMedia fails
#
#  In Playwright Chromium (no real webcam), getUserMedia fails
#  and noCamera becomes true automatically → verify() returns true.
#  If it doesn't (fake device / structured clone), we force it.
@register("Facial Exam")
def solve_level_39(page: Page) -> None:
    """Level 39: Facial Exam — bypass webcam requirement.
    Strategy (3-way fallback chain):
      1. Check if `noCamera` is already true (Playwright has no webcam).
      2. Force `noCamera = true` via Vue $data.
      3. Override `verify()` — always returns true.
    """
    logger.info("[Level 39] Waiting for facial exam...")
    page.locator(SELECTORS["facial_container"]).wait_for(state="visible")
    # Wait for the component to initialize and getUserMedia to resolve
    page.wait_for_timeout(TIMEOUTS["long_wait"])
    # ── Method 1: Check current state ──
    state = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            if (!pageVm) return {{ error: 'pageVm not found' }};
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().targetEmotion !== undefined
            );
            if (!inst) return {{ error: 'FacialExam component not found' }};
            return {{
                noCamera: inst.$data.noCamera,
                cameraDisabled: inst.$data.cameraDisabled,
                confidence: inst.$data.confidence,
                targetEmotion: inst.$data.targetEmotion,
                verify: inst.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 39] State check: {state}")
    # If verify() already returns true (noCamera auto-set), we're done
    if state and state.get("verify"):
        logger.info("[Level 39] verify() already returns True (no camera detected)")
        click_verify(page, "Level 39")
        return
    # ── Method 2: Force noCamera = true ──
    logger.warning("[Level 39] verify() is False, forcing noCamera = true...")
    force = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().targetEmotion !== undefined
            );
            if (!inst) return {{ error: 'not found' }};
            // Force noCamera = true
            inst.$data.noCamera = true;
            inst.$data.cameraDisabled = true;
            // Also stop the video stream if any
            try {{
                const video = inst.$refs.video;
                if (video && video.srcObject) {{
                    video.srcObject.getTracks().forEach(t => t.stop());
                    video.srcObject = null;
                }}
            }} catch (e) {{}}
            return {{
                success: true,
                noCamera: inst.$data.noCamera,
                verify: inst.verify(),
            }};
        }}
    """)
    logger.info(f"[Level 39] Force result: {force}")
    if force and force.get("verify"):
        logger.info("[Level 39] Method 2 (force noCamera) succeeded!")
        page.wait_for_timeout(TIMEOUTS["short_wait"])
        click_verify(page, "Level 39")
        return
    # ── Method 3: Override verify() ──
    logger.warning("[Level 39] Method 2 failed, using Method 3 (override verify)...")
    override = page.evaluate(f"""
        () => {{
            const pageVm = document.querySelector('{SELECTORS["page_container"]}').__vue__;
            const inst = pageVm.$children.find(c =>
                c.$options && c.$options.data &&
                c.$options.data().targetEmotion !== undefined
            );
            if (!inst) return {{ error: 'not found' }};
            inst.verify = function() {{ return true; }};
            return {{ success: true }};
        }}
    """)
    logger.info(f"[Level 39] Method 3 (override verify): {override}")
    if not override or override.get("error"):
        raise LevelFailed("Level 39: all 3 methods failed")
    page.wait_for_timeout(TIMEOUTS["short_wait"])
    click_verify(page, "Level 39")