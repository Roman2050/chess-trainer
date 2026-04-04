import chess.pgn
import io
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ParsedMove:
    move_number: int
    color: str        # 'w' | 'b'
    uci: str
    san: str
    fen_after: str


@dataclass
class ParsedGame:
    pgn_raw: str
    white: Optional[str]
    black: Optional[str]
    result: Optional[str]
    opening: Optional[str]
    date_played: Optional[date]
    moves: list[ParsedMove]


def parse_pgn(pgn_text: str) -> ParsedGame:
    """
    Parses a PGN string and returns a structured ParsedGame object.
    Raise a ValueError if the PGN is invalid.
    """
    game = chess.pgn.read_game(io.StringIO(pgn_text))

    if game is None:
        raise ValueError("Invalid PGN: could not parse game")

    headers = game.headers

    # Парсинг дати
    date_played = _parse_date(headers.get("Date"))

    moves = []
    board = game.board()

    for move_number, node in enumerate(game.mainline(), start=1):
        move = node.move
        color = 'w' if board.turn == chess.WHITE else 'b'
        san = board.san(move)
        uci = move.uci()
        board.push(move)

        moves.append(ParsedMove(
            move_number=move_number,
            color=color,
            uci=uci,
            san=san,
            fen_after=board.fen(),
        ))

    return ParsedGame(
        pgn_raw=pgn_text.strip(),
        white=headers.get("White") or None,
        black=headers.get("Black") or None,
        result=headers.get("Result") or None,
        opening=headers.get("Opening") or None,
        date_played=date_played,
        moves=moves,
    )


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """
    Converts the PGN date '2024.01.15' into a date object. 
    Returns None if the date is missing or invalid.
    """
    if not date_str or date_str == "????.??.??":
        return None
    try:
        parts = date_str.split(".")
        if len(parts) == 3 and "?" not in date_str:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None
