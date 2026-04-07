import pytest
from app.utils.pgn_parser import ParsedGame, ParsedMove


# --- PGN fixtures ---

VALID_PGN = """[Event "Test Game"]
[White "Magnus"]
[Black "Hikaru"]
[Result "1-0"]
[Date "2024.01.15"]
[Opening "Sicilian Defense"]

1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6 1-0"""

EMPTY_PGN = "not a pgn at all"

NO_MOVES_PGN = """[Event "Empty"]
[White "A"]
[Black "B"]
[Result "*"]

*"""


@pytest.fixture
def valid_pgn() -> str:
    return VALID_PGN


@pytest.fixture
def empty_pgn() -> str:
    return EMPTY_PGN


@pytest.fixture
def no_moves_pgn() -> str:
    return NO_MOVES_PGN


# --- Analysis fixtures ---

def make_move(number: int, color: str, eval_cp: int, best_move: str = "e2e4") -> object:
    """A factory for mock-moves."""
    class FakeMove:
        move_number = number
        uci = "e2e4"
    m = FakeMove()
    m.move_number = number
    m.color = color
    m.eval_cp = eval_cp
    m.best_move = best_move
    m.uci = "e2e4"
    return m


@pytest.fixture
def sample_moves_white():
    """A game where White is playing — a typical sequence of moves."""
    return [
        make_move(1, 'w', eval_cp=20),   # the Whites are up by +0.20
        make_move(2, 'b', eval_cp=10),   # the Blacks' response
        make_move(3, 'w', eval_cp=30),   # white
        make_move(4, 'b', eval_cp=20),   # black
        make_move(5, 'w', eval_cp=250),  # The Whites made a blunder (loss >200)
        make_move(6, 'b', eval_cp=200),  # black
    ]