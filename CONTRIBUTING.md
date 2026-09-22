# 🤝 Contributing to Neal.fun Scripts

Thank you for your interest in improving this educational project! We welcome contributions, especially adding support for planned games or refining existing level handlers.

Please note that this project is strictly for **educational purposes** to demonstrate browser automation, frontend frameworks, and classic computer science algorithms.

---

## 🏗️ How to Add a New Level Handler

The `iam_not_a_robot/` workspace uses a modular registry system. When a new level is encountered, the state machine reads the DOM title and executes the matched handler inside `src/not-a-robot/handlers.ts`.

### 🛡️ Adhering to the Hybrid Strategy
When writing or updating a level solver, always attempt to build out the solution in this specific order of operations:

1. **Method 1 (Vue State Mutation):** Try querying the `.__vue__` instance property on the component container and updating its structural `$data` fields directly.
2. **Method 2 (Authentic DOM Playback):** If the data engine is locked down or validated externally, fall back to triggering mechanical actions like `.click()`, keyboard actions, or `.dispatchEvent(new DragEvent(...))`.
3. **Method 3 (Lifecycle Hook Override):** If the puzzle is mathematically impossible or computationally excessive to simulate within standard timeouts, intercept and rewrite the internal component `verify()` or validation method natively inside the browser context.

### 📝 Handler Boilerplate Code

To register a new level, open `src/not-a-robot/handlers.ts` and add your code to the handler system:

```typescript
import { Page } from '@playwright/test';
import { logger } from './logger';

/**
 * Example level handler implementation
 * @param page The active Playwright page instance
 */
export async function solveLevelX(page: Page): Promise<void> {
  logger.info('Executing solver for Level X...');

  // Step 1: Execute scripts safely within the browser frame context
  await page.evaluate(() => {
    const container = document.querySelector('.page-container');
    if (container && (container as any).__vue__) {
      const vm = (container as any).__vue__;
      
      // Implement Method 1 or Method 3 here
      if (vm.$data) {
        vm.$data.isSolved = true;
      }
    }
  });

  // Step 2: Fall back to direct DOM clicking if mutation is insufficient
  const verifyButton = page.locator('button:has-text("Verify")');
  await verifyButton.click();
}

// Remember to append your solver reference to the LEVEL_HANDLERS map object at the bottom of the file!
```

---

## 🛠️ Local Workflow Setup

1. **Fork the repo** and clone it locally.
2. Ensure you have Node.js 20+ and your choice of package manager installed (`pnpm` preferred).
3. Run `pnpm install` to load typing definitions and dependencies.
4. Run `pnpm exec playwright install chromium` to fetch the browser binaries.
5. Create a cleanly named feature branch (e.g., `feat/level-40-handler`).

### 🧪 Code Standards & Testing
* Always add accompanying unit tests to `tests/xoxo.test.ts` or respective test suites if writing complex mathematical heuristics.
* Ensure all structural application runtime processes use the Winston `logger` rather than basic `console.log()` outputs.
* Make sure your complete automated pipeline runs successfully locally by asserting `npm test` or `pnpm test` clears without errors before submitting a Pull Request.
