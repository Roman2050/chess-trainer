from sqlalchemy.orm import Session
from datetime import datetime

from app.models.db import Game, Analysis, PlayerProfile


def build_profile(player_name: str, db: Session) -> PlayerProfile:
    """
    Aggregates all analyses of the player's games into a single profile.
    If the profile exists — updates it.
    """
    games_as_white = db.query(Game).filter(Game.white == player_name).all()
    games_as_black = db.query(Game).filter(Game.black == player_name).all()

    all_games = games_as_white + games_as_black

    if not all_games:
        raise ValueError(f"No games found for player '{player_name}'")

    game_ids = [g.id for g in all_games]
    analyses = db.query(Analysis).filter(Analysis.game_id.in_(game_ids)).all()

    if not analyses:
        raise ValueError(f"No analyzed games found for player '{player_name}'")

    profile_json = _aggregate(player_name, all_games, analyses)

    profile = db.query(PlayerProfile).filter(
        PlayerProfile.player_name == player_name
    ).first()

    if profile:
        profile.games_count = profile_json["games_count"]
        profile.profile_json = profile_json
        profile.updated_at = datetime.utcnow()
    else:
        profile = PlayerProfile(
            player_name=player_name,
            games_count=profile_json["games_count"],
            profile_json=profile_json,
        )
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile


def get_profile(player_name: str, db: Session) -> PlayerProfile | None:
    return db.query(PlayerProfile).filter(
        PlayerProfile.player_name == player_name
    ).first()


# --- private ---

def _aggregate(
    player_name: str,
    games: list[Game],
    analyses: list[Analysis],
) -> dict:
    """Builds a JSON profile from aggregated metrics."""

    analyses_by_game = {a.game_id: a for a in analyses}

    wins = draws = losses = 0
    acpl_values = []
    blunders = mistakes = inaccuracies = 0
    openings: dict[str, int] = {}

    acpl_opening_values     = []
    acpl_middlegame_values  = []
    acpl_endgame_values     = []

    for game in games:
        analysis = analyses_by_game.get(game.id)
        if not analysis:
            continue

        # Result
        result = game.result
        color = analysis.player_color
        outcome = _get_outcome(result, color)
        if outcome == "win":
            wins += 1
        elif outcome == "draw":
            draws += 1
        else:
            losses += 1

        # ACPL
        if analysis.acpl is not None:
            acpl_values.append(analysis.acpl)
        if analysis.acpl_opening is not None:
            acpl_opening_values.append(analysis.acpl_opening)
        if analysis.acpl_middlegame is not None:
            acpl_middlegame_values.append(analysis.acpl_middlegame)
        if analysis.acpl_endgame is not None:
            acpl_endgame_values.append(analysis.acpl_endgame)

        # Mistakes
        blunders     += analysis.blunders
        mistakes     += analysis.mistakes
        inaccuracies += analysis.inaccuracies

        # Openings
        if game.opening:
            openings[game.opening] = openings.get(game.opening, 0) + 1

    def avg(lst): return round(sum(lst) / len(lst), 1) if lst else None

    analyzed_count = len(acpl_values)

    return {
        "player_name": player_name,
        "games_count": len(games),
        "analyzed_count": analyzed_count,
        "results": {
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "win_rate": round(wins / analyzed_count * 100, 1) if analyzed_count else None,
        },
        "accuracy": {
            "acpl": avg(acpl_values),
            "acpl_opening": avg(acpl_opening_values),
            "acpl_middlegame": avg(acpl_middlegame_values),
            "acpl_endgame": avg(acpl_endgame_values),
        },
        "errors": {
            "blunders": blunders,
            "mistakes": mistakes,
            "inaccuracies": inaccuracies,
            "blunders_per_game": round(blunders / analyzed_count, 2) if analyzed_count else None,
        },
        "openings": dict(
            sorted(openings.items(), key=lambda x: x[1], reverse=True)[:5]
        ),
        "weaknesses": _detect_weaknesses(
            avg(acpl_values),
            avg(acpl_opening_values),
            avg(acpl_middlegame_values),
            avg(acpl_endgame_values),
            blunders,
            analyzed_count,
        ),
    }


def _get_outcome(result: str | None, color: str) -> str:
    if result == "1-0":
        return "win" if color == "w" else "loss"
    if result == "0-1":
        return "win" if color == "b" else "loss"
    return "draw"


def _detect_weaknesses(
    acpl: float | None,
    acpl_opening: float | None,
    acpl_middlegame: float | None,
    acpl_endgame: float | None,
    blunders: int,
    games_count: int,
) -> list[str]:
    """Simple rules for identifying weaknesses."""
    weaknesses = []

    if acpl and acpl > 50:
        weaknesses.append("High overall error rate")
    if acpl_opening and acpl_opening > 40:
        weaknesses.append("Weak opening play")
    if acpl_middlegame and acpl_middlegame > 60:
        weaknesses.append("Weak middlegame play")
    if acpl_endgame and acpl_endgame > 60:
        weaknesses.append("Weak endgame play")
    if games_count and blunders / games_count > 1.5:
        weaknesses.append("Frequent blunders")

    return weaknesses


def save_report(player_name: str, report_text: str, db: Session) -> None:
    """Saves the LLM report to the player's profile."""
    profile = db.query(PlayerProfile).filter(
        PlayerProfile.player_name == player_name
    ).first()
    if profile:
        profile.report_text = report_text
        profile.updated_at = datetime.utcnow()
        db.commit()
