/** Unit tests for XOXO (tic-tac-toe) helper functions. */

import {
  isWinner as _is_winner,
  bestMove as _best_move,
  minimax as _minimax,
  type Board,
} from "../handlers";

// ══════════════════════════════════════
//  _is_winner
// ══════════════════════════════════════
describe("TestIsWinner", () => {
  // Parametrised cases mirroring the pytest @pytest.mark.parametrize
  const cases: Array<[string, Board, string, boolean]> = [
    // ── Winning cases ──
    // Horizontal (top row)
    ["horizontal top X", ["X", "X", "X", ".", ".", ".", ".", ".", "."], "X", true],
    // Horizontal (middle row)
    ["horizontal middle O", [".", ".", ".", "O", "O", "O", ".", ".", "."], "O", true],
    // Vertical (left column)
    ["vertical left X", ["X", ".", ".", "X", ".", ".", "X", ".", "."], "X", true],
    // Diagonal (top-left to bottom-right)
    ["diagonal X", ["X", ".", ".", ".", "X", ".", ".", ".", "X"], "X", true],
    // Anti-diagonal (top-right to bottom-left)
    ["anti-diagonal X", [".", ".", "X", ".", "X", ".", "X", ".", "."], "X", true],

    // ── Non-winning cases ──
    // Empty board
    ["empty board", [".", ".", ".", ".", ".", ".", ".", ".", "."], "X", false],
    // Draw
    [
      "draw",
      ["X", "O", "X", "X", "O", "O", "O", "X", "X"],
      "X",
      false,
    ],
    // X wins but we check O
    ["X wins but check O", ["X", "X", "X", ".", ".", ".", ".", ".", "."], "O", false],
  ];

  test.each(cases)("%s", (_name, board, player, expected) => {
    expect(_is_winner(board, player)).toBe(expected);
  });
});

// ══════════════════════════════════════
//  _best_move
// ══════════════════════════════════════
describe("TestBestMove", () => {
  test("wins when possible", () => {
    // X has two in a row at 0, 1 → should play 2 to win
    const board: Board = ["X", "X", ".", "O", "O", ".", ".", ".", "."];
    expect(_best_move(board)).toBe(2);
  });

  test("blocks opponent", () => {
    // O is about to win at 2, X must block
    const board: Board = ["O", "O", ".", "X", "X", ".", ".", ".", "."];
    expect(_best_move(board)).toBe(2);
  });

  test("center on empty", () => {
    const board: Board = [".", ".", ".", ".", ".", ".", ".", ".", "."];
    expect(_best_move(board)).toBe(4);
  });

  test("returns null on full board", () => {
    const board: Board = ["X", "O", "X", "X", "O", "O", "O", "X", "X"];
    expect(_best_move(board)).toBeNull();
  });
});

// ══════════════════════════════════════
//  _minimax
// ══════════════════════════════════════
describe("TestMinimax", () => {
  test("winning position positive", () => {
    const board: Board = ["X", "X", "X", "O", "O", ".", ".", ".", "."];
    expect(_minimax(board, 0, false, "X", "O")).toBe(10);
  });

  test("losing position negative", () => {
    const board: Board = ["O", "O", "O", "X", "X", ".", ".", ".", "."];
    expect(_minimax(board, 0, true, "X", "O")).toBeLessThan(0);
  });

  test("draw zero", () => {
    const board: Board = ["X", "O", "X", "X", "O", "O", "O", "X", "X"];
    expect(_minimax(board, 0, true, "X", "O")).toBe(0);
  });
});