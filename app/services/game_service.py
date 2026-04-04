from sqlalchemy.orm import Session

from app.models.db import Game, Move
from app.utils.pgn_parser import parse_pgn, ParsedGame


def save_game(pgn_text: str, source: str, db: Session) -> Game:
    """
    Takes a PGN file and saves the Game and Moves to the database.
    Returns the saved Game object.
    """
    parsed = parse_pgn(pgn_text)
    return _persist_game(parsed, source, db)


def get_game_by_id(game_id: str, db: Session) -> Game | None:
    return db.query(Game).filter(Game.id == game_id).first()


def get_all_games(db: Session, limit: int = 50) -> list[Game]:
    return db.query(Game).order_by(Game.created_at.desc()).limit(limit).all()


# --- private ---

def _persist_game(parsed: ParsedGame, source: str, db: Session) -> Game:
    game = Game(
        pgn_raw=parsed.pgn_raw,
        white=parsed.white,
        black=parsed.black,
        result=parsed.result,
        opening=parsed.opening,
        date_played=parsed.date_played,
        source=source,
    )
    db.add(game)
    db.flush()  # We retrieve the game.id for the commit after the moves are added.

    moves = [
        Move(
            game_id=game.id,
            move_number=m.move_number,
            color=m.color,
            uci=m.uci,
            san=m.san,
            fen_after=m.fen_after,
        )
        for m in parsed.moves
    ]
    db.bulk_save_objects(moves)
    db.commit()
    db.refresh(game)

    return game
