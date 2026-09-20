# Neal.fun Scripts

> A collection of educational Playwright scripts for [neal.fun](https://neal.fun) games,
> demonstrating browser automation, Vue.js internals, and classic AI algorithms.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-1.40+-green.svg)](https://playwright.dev/python/)
[![uv](https://img.shields.io/badge/managed%20by-uv-purple.svg)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

> ⚠️ **Educational Use Only**
>
> This project is a **learning exercise** for browser automation,
> Vue.js internals, and classic AI algorithms. It is **not intended**
> to harm, disrupt, or compete with any service.
>
> If you are a rights holder and want this removed, please
> [open an issue](https://github.com/Tony123-tech/Neal_Fun_Script/issues)
> and I will respond promptly.

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
for various [neal.fun](https://neal.fun) games.

| Game | Status | Technique |
|------|--------|-----------|
| **Not a Robot** | ✅ Complete (33 levels) | Vue.js internals + AI algorithms |
| *More games* | 🚧 Planned | TBD |

Each script uses **Playwright** for browser automation and is managed
with **uv** for fast, reproducible dependency management.

---

## 🎮 Games

### ✅ Not a Robot (`iam_not_a_robot/`)

Automatically solves all **33 levels** of the
[neal.fun "Not a Robot"](https://neal.fun/not-a-robot/) game.

**Key techniques:**

- Read Vue.js component internals via `__vue__`
- Minimax algorithm for tic-tac-toe (Level 6)
- 8-directional word search (Level 7)
- Backtracking + Warnsdorff heuristic (Level 27)
- BFS for sliding tiles (Level 30)
- Pannellum panorama drag math (Level 23)
- Multi-step state machine (Level 24)
- Event-driven waiting (`wait_for_function`)
- Structured logging and error handling

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
| 20 | Rorschach | Fixed answer (any works) |
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

### 🚧 Planned Games

The following neal.fun games are candidates for future scripts.
Contributions welcome!

- [Infinite Craft](https://neal.fun/infinite-craft/)
- [Password Game](https://neal.fun/password-game/)
- [Absurd Trolley Problem](https://neal.fun/absurd-trolley-problem/)
- [Spend Bill Gates' Money](https://neal.fun/spend/)
- [Draw a Perfect Circle](https://neal.fun/perfect-circle/)

> **Note:** Not all neal.fun games are suitable for automation.
> Only games that are purely single-player, offline-style puzzles
> are considered. Games with real security implications (e.g. actual
> CAPTCHAs protecting third-party services) are **out of scope**.

---

## 📋 Requirements

- **Python** 3.10 or higher
- **uv** (recommended) or pip
- **Playwright** with Chromium browser

---

## 🔧 Installation

### Step 1: Install `uv` (if not already installed)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2: Clone the repository

```bash
git clone https://github.com/Tony123-tech/Neal_Fun_Script.git
cd Neal_Fun_Script
```

### Step 3: Install the dependencies

```bash
uv sync
```

### Step 4: Install Playwright browsers

```bash
uv run playwright install chromium
```

---

## 🎮 Usage

### Not a Robot

```bash
cd iam_not_a_robot
python main.py
```

The bot will:
- Open Chromium (visible window)
- Navigate to https://neal.fun/not-a-robot
- Solve levels 1–33 automatically

### ⏱️ Expected Runtime
- ~5–10 minutes for all 33 levels
- Requires a visible browser window (headless=False)

### 🛑 Stopping
- Press Ctrl+C in the terminal, or close the browser window

### ⚠️ Rate Limiting
- Please run this at most once per day.
- Do NOT run it in loops or with multiple parallel instances.
- See Disclaimer for details.

---

## 🧪 Testing

```bash
uv run pytest
```

Currently covers the XOXO (tic-tac-toe) helper functions:
- `_is_winner()` — win detection
- `_best_move()` — optimal move selection
- `_minimax()` — game tree evaluation

---

## 📁 Project Structure

```text
Neal_Fun_Script/
└── iam_not_a_robot/
    ├── main.py          # Entry point
    ├── config.py        # Selectors, timeouts, retry limits
    ├── handlers.py      # 33 level solvers + registry
    ├── helpers.py       # Shared Playwright/Vue helpers
    └── test_xoxo.py     # Unit tests for XOXO
```

Future games will follow the same structure, e.g.:

```text
Neal_Fun_Script/
├── iam_not_a_robot/
└── infinite_craft/     # 🚧 Planned
    ├── main.py
    ├── config.py
    └── ...
```

---

## 🔍 How It Works

Each game script follows the same general pattern:
- **Level / state detection** — Read the current game state from the DOM
- **Handler lookup** — Match against a registry of solvers
- **Strategy** — Try direct Vue $data manipulation first, fall back to real DOM interaction
- **Verification** — Click Verify and wait for state change

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

### 🛑 Please Respect the Developer
neal.fun is a small independent project that relies on ad revenue. Running these scripts does not generate ad revenue for them.

If you enjoy the games:
- Play them legitimately
- Share it with friends
- Support the developer


### ⚖️ No Warranty

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED. The author is **not liable** for any damages
or legal consequences arising from the use of this software.

**You use this software at your own risk.**

### 👤 User Responsibility

By using this software, you agree that:

- You are **solely responsible** for your own actions
- You will **comply with all applicable laws** in your jurisdiction
- You will **respect the Terms of Service** of any website you interact with
- You will **not hold the author liable** for any consequences

The author provides this code for **learning purposes only**
and does **not condone** any misuse.


Play the original games here: https://neal.fun/

If you are a rights holder and want this removed, please contact me.

