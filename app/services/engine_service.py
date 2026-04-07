import chess
import chess.engine
from dataclasses import dataclass
from typing import Optional

from app.config import settings

@dataclass
class MoveEvaluation:
    uci: str
    eval_cp: Optional[int]   # Evaluation BEFORE the move (from White's perspective)
    best_move: Optional[str] # Best move in this position


def analyze_game(moves_uci: list[str], depth_override: int = None) -> list[MoveEvaluation]:
    """
    Analyzes a game with moves in UCI format.
    Returns evaluations and the best move for each position.
    Only one Stockfish process is used for the entire game — do not launch separately for each move.
    """
    results = []
    board = chess.Board()

    depth = depth_override or settings.engine_depth

    with chess.engine.SimpleEngine.popen_uci(settings.stockfish_path) as engine:
        for uci in moves_uci:
            move = chess.Move.from_uci(uci)

            info = engine.analyse(
                board,
                chess.engine.Limit(depth=depth),
            )

            score = info["score"].white()
            eval_cp = score.score(mate_score=10000)

            pv = info.get("pv")
            best_move = pv[0].uci() if pv else None

            results.append(MoveEvaluation(
                uci=uci,
                eval_cp=eval_cp,
                best_move=best_move,
            ))

            board.push(move)

    return results