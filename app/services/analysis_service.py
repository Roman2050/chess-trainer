from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.db import Game, Move, Analysis
from app.services.engine_service import analyze_game, MoveEvaluation


# Mistake classification thresholds (in centipawns)
BLUNDER_THRESHOLD     = 200
MISTAKE_THRESHOLD     = 100
INACCURACY_THRESHOLD  = 50

# Game phases (by move number)
OPENING_END     = 15
MIDDLEGAME_END  = 35


@dataclass
class AnalysisResult:
    game_id: str
    player_color: str
    acpl: float
    acpl_opening: Optional[float]
    acpl_middlegame: Optional[float]
    acpl_endgame: Optional[float]
    blunders: int
    mistakes: int
    inaccuracies: int


def run_analysis(game_id: str, player_color: str, db: Session, depth_override: int = None) -> Analysis:
    """
    Runs Stockfish analysis for a game.
    Saves results in analyses + updates moves.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    existing = db.query(Analysis).filter(Analysis.game_id == game_id).first()
    if existing:
        raise ValueError(f"Game {game_id} already analyzed")

    moves = sorted(game.moves, key=lambda m: m.move_number)
    moves_uci = [m.uci for m in moves]

    evaluations = analyze_game(moves_uci, depth_override=depth_override)

    _update_moves(moves, evaluations, db)

    result = _calc_metrics(game_id, player_color, moves, evaluations)

    analysis = Analysis(
        game_id=game_id,
        player_color=player_color,
        acpl=result.acpl,
        acpl_opening=result.acpl_opening,
        acpl_middlegame=result.acpl_middlegame,
        acpl_endgame=result.acpl_endgame,
        blunders=result.blunders,
        mistakes=result.mistakes,
        inaccuracies=result.inaccuracies,
        raw_json={"evaluations": [
            {"uci": e.uci, "eval_cp": e.eval_cp, "best_move": e.best_move}
            for e in evaluations
        ]},
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis


# --- private ---

def _update_moves(
    moves: list[Move],
    evaluations: list[MoveEvaluation],
    db: Session,
) -> None:
    """Records eval_cp and best_move for each move."""
    for move, evaluation in zip(moves, evaluations):
        move.eval_cp = evaluation.eval_cp
        move.best_move = evaluation.best_move
    db.commit()


def _calc_metrics(
    game_id: str,
    player_color: str,
    moves: list[Move],
    evaluations: list[MoveEvaluation],
) -> AnalysisResult:
    """
    Calculates ACPL and mistake for a given color.
    ACPL = average loss in centimetre points relative to the best move.
    """
    player_moves = [
        (m, e) for m, e in zip(moves, evaluations)
        if m.color == player_color
    ]

    losses = []
    blunders = mistakes = inaccuracies = 0

    opening_losses    = []
    middlegame_losses = []
    endgame_losses    = []

    for i, (move, evaluation) in enumerate(player_moves):
        # eval before the player's move
        eval_before = evaluation.eval_cp

        # eval after the player's move = eval of the opponent's next move
        # if this is the last move, there is no loss
        move_index = moves.index(move)
        if move_index + 1 < len(evaluations):
            eval_after = evaluations[move_index + 1].eval_cp
        else:
            continue

        if eval_before is None or eval_after is None:
            continue

        # a loss, always from the player's perspective
        if player_color == 'w':
            loss = eval_before - eval_after
        else:
            loss = eval_after - eval_before

        loss = max(0, loss)  # A loss cannot be negative
        losses.append(loss)

        # classification
        if loss >= BLUNDER_THRESHOLD:
            blunders += 1
        elif loss >= MISTAKE_THRESHOLD:
            mistakes += 1
        elif loss >= INACCURACY_THRESHOLD:
            inaccuracies += 1

        # game phases
        half_move = move.move_number
        if half_move <= OPENING_END:
            opening_losses.append(loss)
        elif half_move <= MIDDLEGAME_END:
            middlegame_losses.append(loss)
        else:
            endgame_losses.append(loss)

    def avg(lst): return round(sum(lst) / len(lst), 1) if lst else None

    return AnalysisResult(
        game_id=game_id,
        player_color=player_color,
        acpl=avg(losses) or 0.0,
        acpl_opening=avg(opening_losses),
        acpl_middlegame=avg(middlegame_losses),
        acpl_endgame=avg(endgame_losses),
        blunders=blunders,
        mistakes=mistakes,
        inaccuracies=inaccuracies,
    )