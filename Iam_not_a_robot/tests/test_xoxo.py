"""Unit tests for XOXO (tic-tac-toe) helper functions."""

import pytest

from handlers import _is_winner, _best_move, _minimax


# ══════════════════════════════════════
#  _is_winner
# ══════════════════════════════════════
class TestIsWinner:
    """Tests for the _is_winner function."""

    @pytest.mark.parametrize("board, player, expected", [
        # ── Winning cases ──
        # Horizontal (top row)
        (['X', 'X', 'X', '.', '.', '.', '.', '.', '.'], 'X', True),
        # Horizontal (middle row)
        (['.', '.', '.', 'O', 'O', 'O', '.', '.', '.'], 'O', True),
        # Vertical (left column)
        (['X', '.', '.', 'X', '.', '.', 'X', '.', '.'], 'X', True),
        # Diagonal (top-left to bottom-right)
        (['X', '.', '.', '.', 'X', '.', '.', '.', 'X'], 'X', True),
        # Anti-diagonal (top-right to bottom-left)
        (['.', '.', 'X', '.', 'X', '.', 'X', '.', '.'], 'X', True),

        # ── Non-winning cases ──
        # Empty board
        (['.'] * 9, 'X', False),
        # Draw
        (['X', 'O', 'X', 'X', 'O', 'O', 'O', 'X', 'X'], 'X', False),
        # X wins but we check O
        (['X', 'X', 'X', '.', '.', '.', '.', '.', '.'], 'O', False),
    ])
    def test_is_winner(self, board, player, expected):
        assert _is_winner(board, player) is expected


# ══════════════════════════════════════
#  _best_move
# ══════════════════════════════════════
class TestBestMove:
    """Tests for the _best_move function."""

    def test_wins_when_possible(self):
        # X has two in a row at 0, 1 → should play 2 to win
        board = ['X', 'X', '.', 'O', 'O', '.', '.', '.', '.']
        assert _best_move(board) == 2

    def test_blocks_opponent(self):
        # O is about to win at 2, X must block
        board = ['O', 'O', '.', 'X', 'X', '.', '.', '.', '.']
        assert _best_move(board) == 2

    def test_center_on_empty(self):
        board = ['.'] * 9
        assert _best_move(board) == 4

    def test_returns_none_on_full_board(self):
        board = ['X', 'O', 'X', 'X', 'O', 'O', 'O', 'X', 'X']
        assert _best_move(board) is None


# ══════════════════════════════════════
#  _minimax
# ══════════════════════════════════════
class TestMinimax:
    """Tests for the _minimax function."""

    def test_winning_position_positive(self):
        board = ['X', 'X', 'X', 'O', 'O', '.', '.', '.', '.']
        assert _minimax(board, 0, False, 'X', 'O') == 10

    def test_losing_position_negative(self):
        board = ['O', 'O', 'O', 'X', 'X', '.', '.', '.', '.']
        assert _minimax(board, 0, True, 'X', 'O') < 0

    def test_draw_zero(self):
        board = ['X', 'O', 'X', 'X', 'O', 'O', 'O', 'X', 'X']
        assert _minimax(board, 0, True, 'X', 'O') == 0