"""Global configuration: URL, selectors, timeouts, browser options."""

GAME_URL = "https://neal.fun/not-a-robot/"

# ══════════════════════════════════════
#  Selectors — all CSS selectors in one place
# ══════════════════════════════════════
SELECTORS = {
    # ── General ──
    "level_text":         ".site-level span",
    "reset":              ".site-footer .reset",
    "page_container":     ".page-container",
    "captcha_container":  ".captcha-container",
    "captcha_title_type": ".captcha-title-type",

    # ── Level 1: Checkbox ──
    "captcha_box": ".captcha-box",

    # ── Level 2, 4, 6, 11, 13: Grid ──
    "grid_item":   ".grid-item",
    "verify_btn":  "#captcha-verify-button",
    "refresh_btn": ".captcha-refresh",

    # ── Level 3, 8, 16, 19, 20, 24: Text input ──
    "captcha_input":  ".captcha-input-text",
    "captcha_submit": ".captcha-button",

    # ── Level 5: Rotation ──
    "rotating_item": ".rotating-item",

    # ── Level 6: XOXO ──
    "ttt_cell": ".tic-tac-toe-cell",

    # ── Level 7: Word Search ──
    "ws_cell": ".grid-item.letter",

    # ── Level 8: License Plate ──
    "license_image": ".license-image",

    # ── Level 9: Nested ──
    "nested_grid": ".nested-grid",

    # ── Level 10: Whack-a-Mole ──
    "mole_wrapper": ".mole-wrapper",
    "mole_active":  ".mole.active",

    # ── Level 12: Muffins? ──
    "muffin_img": ".muffin-img",

    # ── Level 14: Affirmations ──
    "recaptcha_container":  ".recaptcha-container",
    "captcha_box_checkbox": ".captcha-box-checkbox-input",

    # ── Level 15: Parking ──
    "park_canvas": "#park-canvas",

    # ── Level 17: Perfect Circle ──
    "circle_svg": "svg[viewBox='0 0 1000 1000']",

    # ── Level 18: Sisyphus ──
    "sisyphus_grid_item": ".sisyphus-grid-item",
    "sisyphus_item":      ".sisyphus-item",
    "hydrant_img":        "img[src*='/hydrants/']",

    # ── Level 19: In the Dark ──
    "flashlight_container": ".flashlight-container",
    "letter":               ".letters .letter",

    # ── Level 20: Rorschach ──
    "rorschach_image": ".rorschach-image",

    # ── Level 21: CRAFTCHA ──
    "crafting_slot": ".crafting-slot",

    # ── Level 22: My Ducks Ahhh ──
    "duck_container": ".duck-container",

    # ── Level 23: Panorama ──
    "panorama":        "#panorama",
    "panorama_canvas": "#panorama canvas",

    # ── Level 24: Eye Exam ──
    "eye_exam_container": ".eye-exam-container",
    "eye_exam_input":     ".eye-exam-input input",
    "eye_exam_square":    ".color-square",
}

# ══════════════════════════════════════
#  Timeouts — all wait times in one place
# ══════════════════════════════════════
TIMEOUTS = {
    "level_text":       3000,
    "click_wait":       1000,
    "loop_wait":         800,
    "page_load":        2500,
    "cell_click_wait":   200,
    "quick_click_wait":  150,
    "fast_click_wait":   100,
    "short_wait":        300,
    "medium_wait":       500,
    "long_wait":        1200,
    "vue_condition":    5000,   # for wait_for_function
}

# ══════════════════════════════════════
#  Retry limits — all loop counts in one place
# ══════════════════════════════════════
RETRY_LIMITS = {
    "xoxo_games":        20,
    "mole_timeout":      60,
    "mole_click_wait":   50,
    "parking_verifies":   6,
    "sisyphus_attempts": 40,
    "panorama_attempts": 10,
    "eye_exam_subs":      4,   # Level 24 sub-levels
}

# ══════════════════════════════════════
#  Panorama — Pannellum specific settings
# ══════════════════════════════════════
PANORAMA = {
    "wheel_delta":   120,
    "wheel_wait":     80,
    "drag_steps":     30,
    "max_zoom_iter":  50,
}

# ══════════════════════════════════════
#  Fallback answers — for levels with random answers
# ══════════════════════════════════════
FALLBACK_ANSWERS = {
    "wiggles":   ["WVUGYQ", "YHRPCD", "FNZZSD"],
    "rorschach": "a butterfly",
    "eye_exam":  "34",   # Level 24 sub-level 2 (dots)
}

# ══════════════════════════════════════
#  Browser options
# ══════════════════════════════════════
BROWSER = {
    "headless": False,
    "viewport": {"width": 1280, "height": 800},
    "locale":   "en-US",
    "args":     ["--disable-blink-features=AutomationControlled"],
}