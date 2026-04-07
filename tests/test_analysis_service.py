import pytest
from app.services.analysis_service import (
    _calc_metrics,
    BLUNDER_THRESHOLD,
    MISTAKE_THRESHOLD,
    INACCURACY_THRESHOLD,
)
from app.services.engine_service import MoveEvaluation


def make_eval(uci: str, eval_cp: int, best_move: str = "e2e4") -> MoveEvaluation:
    return MoveEvaluation(uci=uci, eval_cp=eval_cp, best_move=best_move)


def make_move(number: int, color: str, uci: str = "e2e4"):
    class FakeMove:
        pass
    m = FakeMove()
    m.move_number = number
    m.color = color
    m.uci = uci
    return m


class TestCalcMetrics:

    def _run(self, moves, evals, color="w"):
        return _calc_metrics("test-id", color, moves, evals)

    def test_perfect_game_has_zero_acpl(self):
        """If a player always makes the best move, ACPL = 0."""
        moves = [make_move(i, 'w' if i % 2 == 1 else 'b') for i in range(1, 7)]
        evals = [make_eval("e2e4", 20) for _ in moves]

        result = self._run(moves, evals, color='w')
        assert result.acpl == 0.0

    def test_detects_blunder(self):
        """A loss of more than 200 CP is a blunder."""
        moves = [
            make_move(1, 'w'),  # the white pieces move
            make_move(2, 'b'),  # black
            make_move(3, 'w'),  # white — blunder
            make_move(4, 'b'),
        ]
        evals = [
            make_eval("e2e4", 20),
            make_eval("e7e5", 10),
            make_eval("d2d4", 20),    # before White's move +20
            make_eval("d7d5", -200),  # after White's move -200 → loss of 220
        ]
        result = self._run(moves, evals, color='w')
        assert result.blunders == 1

    def test_detects_mistake(self):
        """Losing 100–200 CP = a mistake."""
        moves = [make_move(1, 'w'), make_move(2, 'b')]
        evals = [
            make_eval("e2e4", 50),
            make_eval("e7e5", -80),  # White loses 130
        ]
        result = self._run(moves, evals, color='w')
        assert result.mistakes == 1
        assert result.blunders == 0

    def test_detects_inaccuracy(self):
        """Втрата 50–100cp = inaccuracy."""
        moves = [make_move(1, 'w'), make_move(2, 'b')]
        evals = [
            make_eval("e2e4", 30),
            make_eval("e7e5", -40),  # loss 70cp
        ]
        result = self._run(moves, evals, color='w')
        assert result.inaccuracies == 1

    def test_black_perspective(self):
        """For Black, the loss is calculated in reverse."""
        moves = [make_move(1, 'w'), make_move(2, 'b'), make_move(3, 'w')]
        evals = [
            make_eval("e2e4", 20),
            make_eval("e7e5", 10),   # Black pieces move
            make_eval("d2d4", 250),  # After Black's move, Black's position worsened
        ]
        result = self._run(moves, evals, color='b')
        assert result.blunders == 1

    def test_phase_separation(self):
        """The moves are distributed across the phases of the game."""
        # 20 moves: opening(1-15), middlegame(16-35)
        moves = []
        evals = []
        for i in range(1, 21):
            color = 'w' if i % 2 == 1 else 'b'
            moves.append(make_move(i, color))
            evals.append(make_eval("e2e4", 20))

        result = self._run(moves, evals, color='w')
        assert result.acpl_opening is not None
        assert result.acpl_middlegame is not None
        assert result.acpl_endgame is None  # There are no moves left in the endgame

    def test_game_id_preserved(self):
        moves = [make_move(1, 'w'), make_move(2, 'b')]
        evals = [make_eval("e2e4", 20), make_eval("e7e5", 10)]
        result = self._run(moves, evals)
        assert result.game_id == "test-id"