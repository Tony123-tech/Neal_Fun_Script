# Neal.fun Scripts

> A collection of educational Playwright scripts for [neal.fun](https://neal.fun) games,
> written in TypeScript. Demonstrates browser automation, Vue.js internals,
> and classic AI algorithms.

[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![Playwright](https://img.shields.io/badge/playwright-1.40+-green.svg)](https://playwright.dev/)
[![Node](https://img.shields.io/badge/node-20+-brightgreen.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

> **Note:** While the code is MIT-licensed, it is intended for
> **educational, non-commercial use only**. Please see the [Disclaimer](#-disclaimer).

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Games](#-games)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [Disclaimer](#-disclaimer)
- [License](#-license)

---

## 🎯 Overview

This repository contains a collection of educational Playwright scripts
for various [neal.fun](https://neal.fun) games, written in TypeScript.

| Game | Status | Technique |
|------|--------|-----------|
| **Not a Robot** | ✅ Complete (39 levels) | Vue.js internals + AI algorithms |
| *More games* | 🚧 Planned | TBD |

Each script uses **Playwright** for browser automation and **Winston**
for structured logging.

---

## 🎮 Games

### ✅ Not a Robot 

Automatically solves all **39 levels** of the
[neal.fun "Not a Robot"](https://neal.fun/not-a-robot/) game.

**Key techniques:**

- Read Vue.js component internals via `__vue__`
- Minimax algorithm for tic-tac-toe (Level 6)
- 8-directional word search (Level 7)
- Backtracking + Warnsdorff heuristic (Level 27)
- BFS for sliding tiles (Level 30)
- Pannellum panorama manipulation (Level 23)
- Multi-step state machine (Level 24)
- Event-driven waiting (`waitForFunction`)
- Structured logging with Winston

**Levels covered:**

| # | Level | Technique |
|---|-------|-----------|
| 1 | Checkbox | Direct click |
| 2 | Stop Signs | CSS `background-position` parsing |
| 3 | Wiggles | Vue `$data.answer` read + fallback |
| 4 | Vegetables | Vue `$data.correct` matching |
| 5 | Rotation | CSS `rotate()` parsing |
| 6 | XOXO | Minimax AI |
| 7 | Word Search | 8-directional search |
| 8 | License Plate | URL filename parsing |
| 9 | Nested | Direct `$data.selected` set |
| 10 | Whack-a-Mole | Active element clicking |
| 11 | Waldo | Vue `$data.correct` indexes |
| 12 | Muffins? | URL path classification |
| 13 | Reverse | Vue `$data.answers` read |
| 14 | Affirmations | Vue `$props.wrong` filter |
| 15 | Parking | JS function override |
| 16 | Now in 3D! | Vue `$data.captchaText` read |
| 17 | Perfect Circle | Vue `$data.score` override |
| 18 | Sisyphus | Repeated element clicking |
| 19 | In the Dark | DOM letter extraction |
| 20 | Rorschach | Fixed answer |
| 21 | CRAFTCHA | Vue flag override |
| 22 | My Ducks Ahhh | Vue `$data.ducks` loop |
| 23 | Panorama | Pannellum viewer manipulation |
| 24 | Eye Exam | Multi-step: letters + number + dots + color |
| 25 | Creativity | Vue state override (`numDrawn`, tools) |
| 26 | Parallel Parking | JS function override |
| 27 | Networking | Backtracking + Warnsdorff + real drags |
| 28 | Day Trader | Timing-based trading via Vue methods |
| 29 | Soul | Vue `$data.items` override / real clicks |
| 30 | Sliding Tiles | BFS + `moveTile()` calls |
| 31 | Traffic Tree | Vue `$data.items` override / real clicks |
| 32 | Drum Verify | `gameState = "success"` override |
| 33 | Brands | Vue `$data.list` + DOM fallback |
| 34 | Mathematics | Set `selectedOrder` / real clicks / verify override |
| 35 | Shuffle | Set `level = 3` / verify override |
| 36 | Not Candy Crush | Set `score = 1000` / handleVerify override |
| 37 | Imposters | Set `Grid.items` / real clicks / verify override |
| 38 | Tough Decisions | Same `<Park>` component as Level 15/26 |
| 39 | Facial Exam | Force `noCamera = true` / verify override |

### 🚧 Planned Games

- [Infinite Craft](https://neal.fun/infinite-craft/)
- [Password Game](https://neal.fun/password-game/)
- [Absurd Trolley Problem](https://neal.fun/absurd-trolley-problems/)

> **Note:** Only purely single-player, offline-style puzzles are considered.
> Games with real security implications are **out of scope**.

---

## 📋 Requirements

- **Node.js** 20 or higher
- **npm** or **pnpm** or **yarn**
- **Playwright** with Chromium browser
- **TypeScript** 5.0+

---

## 🔧 Installation

### Step 1: Clone the repository

```bash
git clone https://github.com/Tony123-tech/Neal_Fun_Script.git
cd Neal_Fun_Script
```

### Step 2: Install dependencies

```bash
npm install
# or
pnpm install
# or
yarn install
```

### Step 3: Install Playwright browsers

```bash
npx playwright install chromium
```

### Step 4: Build (optional)

```bash
npm run build
```

---

## 🎮 Usage

### Development mode (ts-node / tsx)

```bash
npm run dev
```

### Production mode (compiled)

```bash
npm run build
npm start
```

The bot will:
- Open Chromium (visible window)
- Navigate to https://neal.fun/not-a-robot
- Solve levels 1–39 automatically

### ⏱️ Expected Runtime
- ~5–10 minutes for all 39 levels
- Requires a visible browser window (`headless: false`)

### 🛑 Stopping
- Press `Ctrl+C` in the terminal, or close the browser window.

### ⚠️ Rate Limiting
- Please run this at most once per day.
- Do NOT run it in loops or with multiple parallel instances.
- See Disclaimer for details.

---

## 🧪 Testing

```bash
npm test
```

Tests cover the XOXO (tic-tac-toe) helper functions:
- `isWinner()` — win detection
- `bestMove()` — optimal move selection
- `minimax()` — game tree evaluation

---

## 📁 Project Structure

```text
Neal_Fun_Script/
├── src/
│   ├── not-a-robot/
│   │   ├── main.ts          # Entry point
│   │   ├── config.ts        # Selectors, timeouts, retry limits
│   │   ├── handlers.ts      # 39 level solvers + registry
│   │   ├── helpers.ts       # Shared Playwright/Vue helpers
│   │   └── logger.ts        # Winston logger
│   └── ...
├── tests/
│   └── xoxo.test.ts         # Unit tests for XOXO
├── package.json
├── tsconfig.json
├── playwright.config.ts
└── README.md
```

---

## 🔍 How It Works

Each level handler follows the same general pattern:
- **Level detection** — Read the current level title from the DOM.
- **Handler lookup** — Match against `LEVEL_HANDLERS` registry.
- **Strategy (Hybrid)** — Try direct Vue `$data` manipulation first, fall back to real DOM interaction, then override `verify()`.
- **Verification** — Click Verify and wait for level change.

### The Hybrid Strategy
Most advanced levels use a 3-tier fallback chain:

```text
Method 1: Direct $data mutation      →  Fast, but fragile
    ↓ fails
Method 2: Real DOM interaction       →  Slow, but authentic
    ↓ fails
Method 3: Override verify()          →  Bulletproof, but brute force
```
This pattern appears in levels 27–39.

### Vue Internals Access
```typescript
const pageVm = document.querySelector('.page-container').__vue__;
const inst = pageVm.$children.find(c =>
  c.$options.data().someKey !== undefined
);
```
Duck-typing to find the target component by its `$data` keys — no component names required.

### Special Handling
**Level 39 (Facial Exam):** `getUserMedia` is overridden in `main.ts` via `context.addInitScript()` to auto-reject, so `noCamera` becomes `true` and no camera permission dialog appears.

---

## ⚠️ Disclaimer

This project is for **EDUCATIONAL PURPOSES ONLY**.

- Not affiliated with NEALFUN INC.
- Not endorsed by neal.fun
- Do NOT use for commercial purposes
- Do NOT use for mass automation or to disrupt services
- Do NOT use to bypass real security mechanisms

The techniques demonstrated here are meant to teach:
- Browser automation with Playwright
- Vue.js component internals
- Classic AI algorithms (Minimax, BFS, backtracking)
- TypeScript project structure

### 🛑 Please Respect the Developer
neal.fun is a small independent project that relies on ad revenue. Running these scripts does not generate ad revenue for them.

If you enjoy the games:
- Play them legitimately
- Share them with friends
- Support the developer

Play the original games here: https://neal.fun/

If you are a rights holder and want this removed, please contact me.
