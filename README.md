# CAPTCHA Solvers

> A collection of automated CAPTCHA solvers built with Python and Playwright,
> designed for educational purposes to explore web automation and security concepts.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-1.40+-green.svg)](https://playwright.dev/python/)
[![uv](https://img.shields.io/badge/managed%20by-uv-purple.svg)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Projects](#-projects)
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

This repository contains two independent CAPTCHA-solving projects that
demonstrate different techniques for interacting with modern web challenges:

| Project | Target | Technique |
|---------|--------|-----------|
| **Google Recaptcha** | Google reCAPTCHA v2 | Audio challenge + speech-to-text |
| **Not a Robot** | [neal.fun/not-a-robot](https://neal.fun/not-a-robot/) | Vue.js internals + AI algorithms |

Both projects use **Playwright** for browser automation and are managed
with **uv** for fast, reproducible dependency management.

---

## 🚀 Projects

### 1. Not a Robot (`iam_not_a_robot/`)

Automatically solves all 24 levels of the
[neal.fun "Not a Robot"](https://neal.fun/not-a-robot/) game.

**Key techniques:**
- Read Vue.js component internals via `__vue__`
- Minimax algorithm for tic-tac-toe (Level 6)
- 8-directional word search (Level 7)
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