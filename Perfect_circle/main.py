"""Perfect Circle — Interruptible version.

⚠️ Educational use only.
"""

import math
import random
import signal
import sys
import time

import keyboard
import pyautogui
from playwright.sync_api import sync_playwright


# ══════════════════════════════════════
#  Global flags
# ══════════════════════════════════════
_running = True


def _handle_sigint(signum, frame):
    """Handle Ctrl+C gracefully."""
    global _running
    print("\n[SIGINT] Aborting...")
    _running = False
    try:
        pyautogui.mouseUp()
    except Exception:
        pass
    sys.exit(0)


signal.signal(signal.SIGINT, _handle_sigint)


# ══════════════════════════════════════
#  Config
# ══════════════════════════════════════
GAME_URL = "https://neal.fun/perfect-circle/"
PAGE_LOAD_WAIT = 3.0
SVG_CENTER = (500, 500)
RADIUS_RATIO = 0.40
STEPS = 120
MOVE_DURATION = 0.001


# ══════════════════════════════════════
#  Draw circle — INTERRUPTIBLE
# ══════════════════════════════════════
def draw_circle(center_x, center_y, radius, steps=STEPS,
                wobble=0.0, ellipse_ratio=1.0):
    """Draw a circle. Return True if completed, False if cancelled."""
    start_x = center_x + radius * ellipse_ratio
    start_y = center_y

    pyautogui.moveTo(start_x, start_y, duration=0.1)
    time.sleep(0.1)
    pyautogui.mouseDown()
    time.sleep(0.05)

    try:
        for i in range(1, steps + 1):
            # ── Interrupt check #1: ESC key ──
            if keyboard.is_pressed("esc"):
                print("  [ESC pressed]")
                return False

            # ── Interrupt check #2: global flag ──
            if not _running:
                return False

            angle = 2 * math.pi * i / steps
            r = radius + (random.uniform(-wobble, wobble) if wobble > 0 else 0)
            x = center_x + r * ellipse_ratio * math.cos(angle)
            y = center_y + r * math.sin(angle)
            pyautogui.moveTo(x, y, duration=MOVE_DURATION)
    finally:
        # ── ALWAYS release mouse, even on error ──
        try:
            pyautogui.mouseUp()
        except Exception:
            pass
        time.sleep(0.3)

    return True


# ══════════════════════════════════════
#  Read Vue state — safe
# ══════════════════════════════════════
def read_vue_state(page):
    try:
        return page.evaluate("""
            () => {
                const el = document.querySelector('.container');
                if (!el || !el.__vue__) return { error: 'no vue' };
                const vm = el.__vue__;
                return { score: vm.score, best: vm.best, valid: vm.valid };
            }
        """)
    except Exception as e:
        return {"error": str(e)[:80]}


# ══════════════════════════════════════
#  Geometry
# ══════════════════════════════════════
def compute_geometry(page):
    info = page.evaluate("""
        () => {
            const svg = document.querySelector('svg[viewBox="0 0 1000 1000"]');
            if (!svg) return null;
            const r = svg.getBoundingClientRect();
            return { left: r.left, top: r.top, width: r.width, height: r.height };
        }
    """)
    if not info:
        return {}
    scale = info["width"] / 1000
    return {
        "center": (info["left"] + 500 * scale, info["top"] + 500 * scale),
        "radius": min(info["width"], info["height"]) * RADIUS_RATIO,
    }


# ══════════════════════════════════════
#  Test runner — INTERRUPTIBLE
# ══════════════════════════════════════
def run_tests(page, geometry):
    """Run each test. Returns dict of results."""
    cx, cy = geometry["center"]
    radius = geometry["radius"]

    scenarios = [
        ("Perfect circle", dict(steps=STEPS, wobble=0, ellipse_ratio=1.0)),
        ("Noisy circle",   dict(steps=STEPS, wobble=10, ellipse_ratio=1.0)),
        ("Ellipse",        dict(steps=STEPS, wobble=0, ellipse_ratio=1.5)),
    ]

    results = {}

    for name, kwargs in scenarios:
        if not _running:
            break

        # Reload + Go
        print(f"\n[{name}] Reloading...")
        try:
            page.reload()
            time.sleep(1.0)
            page.locator("button").first.click(timeout=2000)
            time.sleep(0.5)
        except Exception as e:
            print(f"  [skip] {e}")
            continue

        print(f"[{name}] Draw in 2s (ESC to skip)...")
        time.sleep(2)

        ok = draw_circle(cx, cy, radius, **kwargs)

        if not ok:
            results[name] = "cancelled"
            print(f"[{name}] Cancelled.")
            continue

        state = read_vue_state(page)
        score = state.get("score", "?") if "error" not in state else state["error"]
        results[name] = score
        print(f"[{name}] Score = {score}")

    return results


# ══════════════════════════════════════
#  Main — FULLY INTERRUPTIBLE
# ══════════════════════════════════════
def main():
    global _running

    print("=" * 60)
    print("Perfect Circle — Interruptible")
    print("=" * 60)
    print("  ESC  → skip current test")
    print("  Ctrl+C → abort everything")
    print("=" * 60)

    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            page.goto(GAME_URL, wait_until="domcontentloaded")
            time.sleep(PAGE_LOAD_WAIT)

            try:
                page.locator("button").first.click(timeout=3000)
                time.sleep(0.5)
            except Exception:
                pass

            page.bring_to_front()
            time.sleep(0.5)

            geometry = compute_geometry(page)
            print(f"\nGeometry: center={geometry.get('center')}, "
                  f"radius={geometry.get('radius')}")

            results = run_tests(page, geometry)

            print("\n" + "=" * 60)
            print("RESULTS")
            print("=" * 60)
            for name, score in results.items():
                print(f"  {name:22s} → {score}")

            print("\nPress Enter to close (or Ctrl+C)...")
            try:
                input()
            except (KeyboardInterrupt, EOFError):
                pass

    except KeyboardInterrupt:
        print("\n[Aborted by Ctrl+C]")
    except Exception as e:
        print(f"\n[Error] {e}")
    finally:
        # ── ALWAYS release resources ──
        try:
            pyautogui.mouseUp()
        except Exception:
            pass
        if browser:
            try:
                browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()