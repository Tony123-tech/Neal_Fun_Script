/**
 * Not-A-Robot Solver — JavaScript Console Helper
 * ================================================
 * A toolbox for exploring, debugging, and reverse-engineering
 * neal.fun/not-a-robot levels directly in DevTools Console.
 *
 * Usage:
 *   1. Open https://neal.fun/not-a-robot/
 *   2. Open DevTools (F12) → Console
 *   3. Paste this entire file
 *   4. Call NAB.autoSolve() or NAB.debug()
 *
 * @version 2.0.0
 * @license CC BY-NC 4.0
 */

(() => {
    'use strict';

    // ══════════════════════════════════════
    //  1. Core Helpers
    // ══════════════════════════════════════

    /**
     * Get the root Vue instance (.page-container).
     * @returns {object|null}
     */
    function getPageVm() {
        return document.querySelector('.page-container')?.__vue__ || null;
    }

    /**
     * Get the current level number (0-indexed).
     * @returns {number|null}
     */
    function getLevel() {
        const pageVm = getPageVm();
        return pageVm ? pageVm.$data.level : null;
    }

    /**
     * Get the current level display name (e.g. "Checkbox").
     * NOTE: currentLevelName is a Vue computed property,
     *       NOT $data.currentLevelName.
     * @returns {string|null}
     */
    function getLevelName() {
        const pageVm = getPageVm();
        return pageVm ? pageVm.currentLevelName : null;
    }

    /**
     * Find a Vue child component by a $data key.
     * Uses $data directly (safe — does not invoke data()).
     * @param {string} key
     * @returns {object|null}
     */
    function findVueChild(key) {
        const pageVm = getPageVm();
        if (!pageVm) return null;
        return pageVm.$children.find(c =>
            c && c.$data && c.$data[key] !== undefined
        ) || null;
    }

    /**
     * Read $data of a Vue child component that has the given key.
     * @param {string} key
     * @returns {object|null}
     */
    function readVueChild(key) {
        const inst = findVueChild(key);
        return inst ? inst.$data : null;
    }

    /**
     * List all children of page-container with their data keys.
     */
    function listVueChildren() {
        const pageVm = getPageVm();
        if (!pageVm) {
            console.warn('pageVm not found');
            return;
        }
        pageVm.$children.forEach((c, i) => {
            console.log(i, {
                name: c.$options.name || c.$options._componentTag,
                tag: c.$options._componentTag,
                dataKeys: c.$data ? Object.keys(c.$data) : [],
            });
        });
    }

    /**
     * Dump the full Vue state of the level component.
     * Scans all children and picks the one with the most data keys.
     */
    function dumpVueState() {
        const pageVm = getPageVm();
        if (!pageVm) return;
        // Pick the child with the most $data keys (likely the game component)
        const inst = pageVm.$children.reduce((best, c) => {
            if (!c.$data) return best;
            const n = Object.keys(c.$data).length;
            if (!best || n > best.n) return { c, n };
            return best;
        }, null);
        if (!inst) {
            console.warn('No level component found');
            return;
        }
        console.log('Component:', inst.c.$options.name || inst.c.$options._componentTag);
        console.log(JSON.parse(JSON.stringify(inst.c.$data)));
    }


    // ══════════════════════════════════════
    //  2. Level Exploration
    // ══════════════════════════════════════

    /**
     * List loaded components (populated lazily as you play).
     */
    function listLoadedComponents() {
        const pageVm = getPageVm();
        if (!pageVm) return;
        console.log('Loaded:', Object.keys(pageVm.$data.loadedComponents));
        console.log('Current level:', pageVm.$data.level);
    }

    /**
     * Get the current level's component definition.
     */
    function getCurrentComponent() {
        const pageVm = getPageVm();
        return pageVm ? pageVm.$data.loadedComponents[String(pageVm.$data.level)] : null;
    }

    /**
     * Print all method sources of the current component.
     */
    function printMethods() {
        const comp = getCurrentComponent();
        if (!comp?.methods) {
            console.warn('No methods found');
            return;
        }
        Object.keys(comp.methods).forEach(name => {
            console.log(`=== ${name} ===`);
            console.log(comp.methods[name].toString());
        });
    }

    /**
     * Print the verify() method source.
     */
    function printVerify() {
        const comp = getCurrentComponent();
        if (!comp?.methods?.verify) {
            console.warn('verify not found');
            return;
        }
        console.log(comp.methods.verify.toString());
    }


    // ══════════════════════════════════════
    //  3. Chunk Finder (Reverse Engineering)
    // ══════════════════════════════════════

    /**
     * Fetch a chunk and check if it contains a module.
     * @param {string} hash - chunk hash (e.g. "a724031")
     * @param {string} moduleId - module id (e.g. "1085")
     * @returns {Promise<boolean>}
     */
    async function checkChunk(hash, moduleId) {
        const url = `/_nuxt/${hash}.js`;
        try {
            const res = await fetch(url);
            const code = await res.text();
            const hasModule = code.includes(`${moduleId}:`);
            console.log(`=== ${hash}.js (${code.length} bytes) ===`);
            console.log(`has ${moduleId}:`, hasModule);
            if (hasModule) {
                const idx = code.indexOf(`${moduleId}:`);
                console.log(code.substring(idx, idx + 25000));
            }
            return hasModule;
        } catch (e) {
            console.error(`Error fetching ${url}:`, e);
            return false;
        }
    }

    /**
     * Search for a module across multiple chunks.
     * @param {string} moduleId
     * @param {string[]} chunks
     * @returns {Promise<string|null>}
     */
    async function findLevelChunk(moduleId, chunks) {
        for (const c of chunks) {
            const has = await checkChunk(c, moduleId);
            if (has) {
                console.log(`✅ Found module ${moduleId} in ${c}.js`);
                return c;
            }
        }
        console.log(`❌ Module ${moduleId} not found in any chunk`);
        return null;
    }

    /**
     * List all modules in a chunk.
     * @param {string} hash
     */
    async function listChunkModules(hash) {
        const url = `/_nuxt/${hash}.js`;
        try {
            const code = await (await fetch(url)).text();
            const modules = code.match(/(\d{4}):function/g);
            console.log(`=== ${hash}.js (${code.length} bytes) ===`);
            console.log('modules:', modules ? modules.join(', ') : 'none');
            return modules;
        } catch (e) {
            console.error(`Error fetching ${url}:`, e);
            return null;
        }
    }


    // ══════════════════════════════════════
    //  4. Utility
    // ══════════════════════════════════════

    /**
     * Take a snapshot of the current page state.
     */
    function snapshot() {
        return {
            level: getLevel(),
            name: getLevelName(),
            url: window.location.href,
            timestamp: new Date().toISOString(),
        };
    }

    /**
     * Print level, name, URL, and Vue children.
     */
    function debug() {
        console.log('Level:', getLevel());
        console.log('Name:', getLevelName());
        console.log('URL:', window.location.href);
        listVueChildren();
    }

    /**
     * Wait until a Vue condition is true.
     * @param {string} key - $data key to find the component
     * @param {(inst: object) => boolean} conditionFn - predicate
     * @param {number} [timeout=5000]
     * @returns {Promise<object>}
     */
    function waitForVue(key, conditionFn, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const start = Date.now();
            const check = () => {
                const inst = findVueChild(key);
                if (inst && conditionFn(inst)) {
                    resolve(inst);
                } else if (Date.now() - start > timeout) {
                    reject(new Error(`Timeout waiting for Vue key: ${key}`));
                } else {
                    setTimeout(check, 100);
                }
            };
            check();
        });
    }

    /**
     * Click the Verify button.
     */
    function clickVerify() {
        const btn = document.querySelector('#captcha-verify-button');
        if (btn) btn.click();
        else console.warn('Verify button not found');
    }


    // ══════════════════════════════════════
    //  5. Level-Specific: Inspect (read-only)
    // ══════════════════════════════════════

    /**
     * Level 3 (Wiggles): read the answer.
     * @returns {string|null}
     */
    function inspectWiggles() {
        const els = document.querySelectorAll('.captcha-container');
        for (const el of els) {
            const vm = el.__vue__;
            if (vm?.$data?.answer !== undefined) return vm.$data.answer;
        }
        return null;
    }

    /**
     * Level 6 (XOXO): read board, currentPlayer, winner.
     */
    function inspectXoxo() {
        const inst = findVueChild('grid');
        if (!inst) return null;
        return {
            grid: [...inst.$data.grid],
            currentPlayer: inst.$data.currentPlayer,
            winner: inst.$data.winner,
        };
    }

    /**
     * Level 7 (Word Search): read puzzle, words, gridSize.
     */
    function inspectWordSearch() {
        const inst = findVueChild('puzzle');
        if (!inst) return null;
        return {
            gridSize: inst.$data.gridSize,
            puzzle: JSON.parse(JSON.stringify(inst.$data.puzzle)),
            words: [...inst.$data.words],
        };
    }

    /**
     * Level 24 (Eye Exam): read sub-level state.
     */
    function inspectEyeExam() {
        const inst = findVueChild('chartRows');
        if (!inst) return null;
        return {
            level: inst.$data.level,
            letters: inst.$data.chartRows[4].letters.join(''),
            colorTests: inst.$data.colorTests,
            colorTestIndex: inst.$data.colorTestIndex,
            randomColorDiffIndex: inst.$data.randomColorDiffIndex,
        };
    }


    // ══════════════════════════════════════
    //  6. Level-Specific: Solve (mutate + verify)
    // ══════════════════════════════════════

    /** Level 9 (Nested): set selected = correct. */
    function solveNested() {
        const inst = findVueChild('correct');
        if (!inst) return null;
        inst.$data.selected = [...inst.$data.correct];
        return inst.$data.selected;
    }

    /** Level 17 (Perfect Circle): override score. */
    function solvePerfectCircle() {
        const inst = findVueChild('score');
        if (!inst) return null;
        inst.$data.score = 1000;
        inst.$data.best = 1000;
        inst.$data.hasDrawn = true;
        inst.$data.valid = true;
        return inst.$data.score;
    }

    /** Level 21 (CRAFTCHA): set hasCraftedTargetItem. */
    function solveCraftcha() {
        const inst = findVueChild('craftingTable');
        if (!inst) return null;
        inst.$data.hasCraftedTargetItem = true;
        return inst.$data.hasCraftedTargetItem;
    }

    /** Level 22 (My Ducks Ahhh): set all ducks clicked. */
    function solveDucks() {
        const inst = findVueChild('ducks');
        if (!inst) return null;
        inst.$data.ducks.forEach(d => { d.clicked = true; });
        inst.$data.done = true;
        inst.$data.isRoaming = false;
        return inst.$data.ducks.filter(d => d.clicked).length;
    }

    /** Level 23 (Panorama): set viewer to centre of bounds. */
    function solvePanorama() {
        const inst = findVueChild('challenges');
        if (!inst?.viewer) return null;
        const ch = inst.challenges[inst.currentChallenge];
        const pitch = (ch.pitchBounds[0] + ch.pitchBounds[1]) / 2;
        const yaw   = (ch.yawBounds[0]   + ch.yawBounds[1])   / 2;
        const hfov  = ch.maxHfov - 1;
        inst.viewer.setPitch(pitch);
        inst.viewer.setYaw(yaw);
        inst.viewer.setHfov(hfov);
        return { pitch, yaw, hfov };
    }

    /** Level 25 (Creativity): set drawing flags. */
    function solveCreativity() {
        const inst = findVueChild('numDrawn');
        if (!inst) return null;
        inst.$data.numDrawn = 11;
        inst.$data.toolsUsed = { brush: true, spray: true, pencil: true, eraser: true };
        inst.$data.differentColorUsed = true;
        return inst.verify();
    }

    /** Level 26 / 38 (Parking / Tough Decisions): override checkParking. */
    function solveParking() {
        let el = document.querySelector('#park-canvas');
        while (el && !(el.__vue__?.$data?.squares)) el = el.parentElement;
        if (!el) return { error: 'GridCaptcha not found' };
        const park = el.__vue__.$vnode?.parent?.componentInstance;
        if (!park) return { error: 'Park component not found' };
        park.checkParking = () => true;
        return { success: true };
    }

    /** Level 27 (Networking): set all cells connected. */
    function solveNetworking() {
        const inst = findVueChild('gridSize');
        if (!inst) return null;
        inst.$data.grid.forEach(cell => { cell.hasPath = true; });
        inst.$data.endpoints.forEach(ep => { ep.isConnected = true; });
        return {
            filledCells: inst.filledCells,
            totalCells: inst.totalCells,
            isComplete: inst.isComplete,
        };
    }

    /** Level 28 (Day Trader): set balance = 2500. */
    function solveDayTrader() {
        const inst = findVueChild('balance');
        if (!inst) return null;
        inst.$data.balance = 2500;
        const stock = inst.$data.stocks.find(s => s.name === inst.$data.selectedStock);
        if (stock) stock.realizedGains = 2500;
        return { balance: inst.$data.balance, diff: inst.diff, verify: inst.verify() };
    }

    /** Level 30 (Sliding Tiles): set tiles to solved state. */
    function solveSlidingTiles() {
        const inst = findVueChild('tiles');
        if (!inst) return null;
        inst.$data.tiles = [1, 2, 3, 4, 5, 6, 7, 8, 0];
        return inst.$data.tiles;
    }

    /** Level 32 (Drum Verify): set gameState = "success". */
    function solveDrumVerify() {
        const inst = findVueChild('gameState');
        if (!inst) return null;
        inst.$data.gameState = 'success';
        return inst.$data.gameState;
    }

    /** Level 34 (Mathematics): sort terms, set selectedOrder. */
    function solveMathematics() {
        const inst = findVueChild('terms');
        if (!inst) return null;
        const sorted = [...inst.$data.terms.keys()].sort((a, b) =>
            inst.$data.terms[a].actual - inst.$data.terms[b].actual
        );
        inst.$data.selectedOrder = sorted;
        return { sorted, verify: inst.verify() };
    }

    /** Level 37 (Imposters): select all "correct" people. */
    function solveImposters() {
        const inst = findVueChild('people');
        if (!inst) return null;
        const toClick = [];
        inst.$data.people.forEach((id, idx) => {
            if (inst.$data.correct.includes(id)) toClick.push(idx);
        });
        toClick.forEach(idx => inst.$refs.grid.select(idx));
        return { toClick, verify: inst.verify() };
    }

    /** Level 39 (Facial Exam): set noCamera = true. */
    function solveFacial() {
        const inst = findVueChild('targetEmotion') ||
                     findVueChild('emotion') ||
                     findVueChild('noCamera');
        if (!inst) return null;
        inst.$data.noCamera = true;
        return { noCamera: inst.$data.noCamera, verify: inst.verify() };
    }


    // ══════════════════════════════════════
    //  7. Auto-Solve Registry
    // ══════════════════════════════════════

    const SOLVERS = {
        'Wiggles':        inspectWiggles,        // read-only, needs fill
        'XOXO':           inspectXoxo,           // read-only, needs minimax
        'Word Search':    inspectWordSearch,     // read-only, needs click
        'Nested':         solveNested,
        'Perfect Circle': solvePerfectCircle,
        'CRAFTCHA':       solveCraftcha,
        'My Ducks Ahhh':  solveDucks,
        'Panorama':       solvePanorama,
        'Eye Exam':       inspectEyeExam,        // read-only, needs multi-step
        'Creativity':     solveCreativity,
        'Parking':        solveParking,
        'Parallel Parking': solveParking,
        'Tough Decisions':  solveParking,
        'Networking':     solveNetworking,
        'Day Trader':     solveDayTrader,
        'Sliding Tiles':  solveSlidingTiles,
        'Drum Verify':    solveDrumVerify,
        'Mathematics':    solveMathematics,
        'Imposters':      solveImposters,
        'Facial Exam':    solveFacial,
    };

    /**
     * Auto-solve the current level (best effort).
     * @returns {boolean} true if a solver ran, false otherwise
     */
    function autoSolve() {
        const name = getLevelName();
        console.log('Auto-solving:', name);

        const solver = SOLVERS[name];
        if (!solver) {
            console.warn(
                `No solver for "${name}". Available:`,
                Object.keys(SOLVERS)
            );
            return false;
        }

        const result = solver();
        console.log('Result:', result);

        clickVerify();
        return true;
    }


    // ══════════════════════════════════════
    //  8. Public API
    // ══════════════════════════════════════

    window.NAB = {
        // Core
        getPageVm,
        getLevel,
        getLevelName,
        findVueChild,
        readVueChild,
        listVueChildren,
        dumpVueState,

        // Exploration
        listLoadedComponents,
        getCurrentComponent,
        printMethods,
        printVerify,

        // Chunk Finder
        checkChunk,
        findLevelChunk,
        listChunkModules,

        // Utility
        snapshot,
        debug,
        waitForVue,
        clickVerify,

        // Inspect
        inspectWiggles,
        inspectXoxo,
        inspectWordSearch,
        inspectEyeExam,

        // Solve
        solveNested,
        solvePerfectCircle,
        solveCraftcha,
        solveDucks,
        solvePanorama,
        solveCreativity,
        solveParking,
        solveNetworking,
        solveDayTrader,
        solveSlidingTiles,
        solveDrumVerify,
        solveMathematics,
        solveImposters,
        solveFacial,

        // Auto
        autoSolve,
        SOLVERS,
    };

    console.log(
        '%c[NAB] Not-A-Robot Helper loaded ✅',
        'color:#00d4aa;font-weight:bold'
    );
    console.log('Try: NAB.debug() | NAB.dumpVueState() | NAB.autoSolve()');
    console.log('API:', Object.keys(window.NAB).join(', '));

})();