from datetime import datetime
from sqlalchemy.orm import Session

from app.models.db import AnalysisJob, Game
from app.services import lichess_service, game_service, analysis_service, profile_service
from app.database import SessionLocal


def create_job(
    player_name: str,
    player_color: str,
    game_type: str,
    limit: int,
    db: Session,
) -> AnalysisJob:
    """Creates a job and saves it to the database."""
    job = AnalysisJob(
        player_name=player_name,
        player_color=player_color,
        game_type=game_type,
        source="lichess",
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(job_id: str, db: Session) -> AnalysisJob | None:
    return db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()


def run_job(job_id: str, player_name: str, player_color: str, game_type: str, limit: int) -> None:
    """
    Background task. Creates its own database session—it does not use the session from the HTTP request.
    The HTTP session is closed before the background task completes.
    """
    db = SessionLocal()

    try:
        _update_status(job_id, "running", db)

        # 1. Downloading a PGN file from Lichess
        pgn_list = lichess_service.fetch_pgn(player_name, game_type, limit)

        _set_total(job_id, len(pgn_list), db)

        if not pgn_list:
            _update_status(job_id, "done", db)
            return

        # 2. We analyze every game
        for pgn_text in pgn_list:
            _process_single_game(job_id, pgn_text, player_name, player_color, db)

        # 3. We create a profile after all the analyses have been completed
        try:
            profile_service.build_profile(player_name, db)
        except ValueError:
            pass  # A profile is created only if test results are available

        _update_status(job_id, "done", db)

    except Exception as e:
        _update_status(job_id, "failed", db, error=str(e))

    finally:
        db.close()


# --- private ---

def _process_single_game(
    job_id: str,
    pgn_text: str,
    player_name: str,
    player_color: str,
    db: Session,
) -> None:
    """Parses, saves, and analyzes a single game. Updates the job counter."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()

    try:
        # Зберігаємо партію
        game = game_service.save_game(pgn_text, source="lichess", db=db)

        # Determine the player's color in this particular game
        color = _detect_color(game, player_name, player_color)

        # Let's analyze
        analysis_service.run_analysis(
            game_id=game.id,
            player_color=color,
            db=db,
            depth_override=12,  # Reduced depth for bulk
        )

        job.processed += 1

    except Exception:
        job.failed += 1

    finally:
        job.updated_at = datetime.utcnow()
        db.commit()


def _detect_color(game: Game, player_name: str, fallback: str) -> str:
    """Determines a player's color in a game based on their name."""
    if game.white and player_name.lower() in game.white.lower():
        return 'w'
    if game.black and player_name.lower() in game.black.lower():
        return 'b'
    return fallback


def _update_status(job_id: str, status: str, db: Session, error: str = None) -> None:
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if job:
        job.status = status
        job.updated_at = datetime.utcnow()
        if error:
            job.error = error
        db.commit()


def _set_total(job_id: str, total: int, db: Session) -> None:
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if job:
        job.total_games = total
        db.commit()