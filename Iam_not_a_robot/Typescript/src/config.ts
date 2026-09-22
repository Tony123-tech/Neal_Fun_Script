/** Global configuration: URL, selectors, timeouts, browser options. */

export const GAME_URL = "https://neal.fun/not-a-robot/";

// ══════════════════════════════════════
//  Selectors — all CSS selectors in one place
// ══════════════════════════════════════
export const SELECTORS = {
  // ── General ──
  level_text: ".site-level span",
  reset: ".site-footer .reset",
  page_container: ".page-container",
  captcha_container: ".captcha-container",
  captcha_title_type: ".captcha-title-type",

  // ── Level 1: Checkbox ──
  captcha_box: ".captcha-box",

  // ── Level 2, 4, 6, 11, 13, 29, 31, 37: Grid ──
  grid_item: ".grid-item",
  verify_btn: "#captcha-verify-button",
  refresh_btn: ".captcha-refresh",

  // ── Level 3, 8, 16, 19, 20, 33, 40: Text input ──
  captcha_input: ".captcha-input-text",
  captcha_submit: ".captcha-button",

  // ── Level 5: Rotation ──
  rotating_item: ".rotating-item",

  // ── Level 6: XOXO ──
  ttt_cell: ".tic-tac-toe-cell",

  // ── Level 7: Word Search ──
  ws_cell: ".grid-item.letter",

  // ── Level 8: License Plate ──
  license_image: ".license-image",

  // ── Level 9: Nested ──
  nested_grid: ".nested-grid",

  // ── Level 10: Whack-a-Mole ──
  mole_wrapper: ".mole-wrapper",
  mole_active: ".mole.active",

  // ── Level 12: Muffins? ──
  muffin_img: ".muffin-img",

  // ── Level 14: Affirmations ──
  recaptcha_container: ".recaptcha-container",
  captcha_box_checkbox: ".captcha-box-checkbox-input",

  // ── Level 15, 26, 38: Parking ──
  park_canvas: "#park-canvas",

  // ── Level 17: Perfect Circle ──
  circle_svg: "svg[viewBox='0 0 1000 1000']",

  // ── Level 18: Sisyphus ──
  sisyphus_grid_item: ".sisyphus-grid-item",
  sisyphus_item: ".sisyphus-item",
  hydrant_img: "img[src*='/hydrants/']",

  // ── Level 19: In the Dark ──
  flashlight_container: ".flashlight-container",
  letter: ".letters .letter",

  // ── Level 20: Rorschach ──
  rorschach_image: ".rorschach-image",

  // ── Level 21: CRAFTCHA ──
  crafting_slot: ".crafting-slot",

  // ── Level 22: My Ducks Ahhh ──
  duck_container: ".duck-container",

  // ── Level 23: Panorama ──
  panorama: "#panorama",
  panorama_canvas: "#panorama canvas",

  // ── Level 24: Eye Exam ──
  eye_exam_container: ".eye-exam-container",
  eye_exam_input: ".eye-exam-input input",
  eye_exam_square: ".color-square",

  // ── Level 25: Creativity ──
  express_canvas: "#express-canvas",

  // ── Level 27: Networking ──
  flow_grid: ".flow-grid",
  flow_cell: ".flow-cell",
  flow_endpoint: ".endpoint",

  // ── Level 28: Day Trader ──
  stock_buy_btn: ".stock-buy",
  stock_sell_btn: ".stock-sell",
  stock_graph: ".graph",

  // ── Level 30: Sliding Tiles ──
  sliding_container: ".puzzle-container",
  sliding_tile: ".puzzle-tile",
  sliding_empty: ".empty-tile",
  sliding_image: ".tile-image",

  // ── Level 32: Drum Verify ──
  drum_container: ".launchpad-container",
  drum_pad: ".dance-square",
  drum_grid_item: ".grid-item",

  // ── Level 33: Brands ──
  brand_container: ".brand-container",

  // ── Level 34: Mathematics ──
  math_grid: ".grid-container",
  math_grid_item: ".grid-item",
  math_actual: ".math-grid-term-actual",

  // ── Level 35: Shuffle ──
  cups_container: ".cups-container",
  cup: ".cup",
  cup_ball: ".ball",
  cup_level_indicator: ".level-indicator-text",

  // ── Level 36: Not Candy Crush ──
  match3_game: ".match3-game",
  match3_board: ".game-grid",
  match3_cell: ".candy-cell",
  match3_score: ".stat-item.score .stat-value",

  // ── Level 39: Facial Exam ──
  facial_container: ".emotions-container",
  facial_video: ".webcam",
  facial_progress: ".progress-bar",

  // ── Level 40: Slot Machine ──
  slot_container: ".slot-machine-container",
  slot_column: ".slot-column",
  slot_input: ".captcha-input-text",
  slot_submit: ".captcha-button",

  // ── Level 41: Grave ──
  grave_container: ".mourn-container",
  grave_canvas: ".grave-zoomed",

  // ── Level 42: Reverse Turing ──
  chat_container: ".chat-container",
  chat_input: "input[placeholder='Type your message...']",
  chat_send: ".send-button",

  // ── Level 43: Ikea ──
  ikea_canvas: ".ikea-canvas",

  // ── Levels 29, 31, 37: Grids that reuse the generic .grid-item ──
  soul_image:     "img.soul-image",
  traffic_tree_bg: "div.grid-item-with-image",
  ai_generated:   "img.ai-generated",

  // ── Level 33: Brands ──
  brand_image:  "img.brand-letter",
  brand_input:  "input.captcha-input-text",
  brand_submit: "button.captcha-button",
} as const;

export type SelectorKey = keyof typeof SELECTORS;

// ══════════════════════════════════════
//  Timeouts — all wait times in one place (ms)
// ══════════════════════════════════════
export const TIMEOUTS = {
  level_text: 3000,
  click_wait: 1000,
  loop_wait: 800,
  page_load: 2500,
  cell_click_wait: 200,
  quick_click_wait: 150,
  fast_click_wait: 100,
  short_wait: 300,
  medium_wait: 500,
  long_wait: 1200,
  vue_condition: 5000,
} as const;

export type TimeoutKey = keyof typeof TIMEOUTS;

// ══════════════════════════════════════
//  Retry limits — all loop counts in one place
// ══════════════════════════════════════
export const RETRY_LIMITS = {
  xoxo_games: 20,
  mole_timeout: 60,
  mole_click_wait: 50,
  parking_verifies: 6,
  sisyphus_attempts: 40,
  panorama_attempts: 10,
} as const;

// ══════════════════════════════════════
//  Panorama — Pannellum specific settings
// ══════════════════════════════════════
export const PANORAMA = {
  wheel_delta: 120,
  wheel_wait: 80,
  drag_steps: 30,
  max_zoom_iter: 50,
} as const;

// ══════════════════════════════════════
//  Fallback answers — for levels with random answers
// ══════════════════════════════════════
export const FALLBACK_ANSWERS = {
  wiggles: ["WVUGYQ", "YHRPCD", "FNZZSD"],
  rorschach: "a butterfly",
} as const;

// ══════════════════════════════════════
//  Browser options
// ══════════════════════════════════════
export const BROWSER = {
  headless: false,
  viewport: { width: 1280, height: 800 },
  locale: "en-US",
  args: ["--disable-blink-features=AutomationControlled"],
} as const;
