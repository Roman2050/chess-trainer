from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import analysis_service
from app.models.schemas import AnalysisResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run/{game_id}", response_model=AnalysisResponse, status_code=201)
def run_analysis(
    game_id: str,
    player_color: str = "w",
    db: Session = Depends(get_db),
):
    """
    Runs Stockfish analysis for a game.
    player_color: 'w' or 'b'
    Attention: Takes 30–90 seconds depending on the game length.
    """
    if player_color not in ("w", "b"):
        raise HTTPException(status_code=400, detail="player_color must be 'w' or 'b'")

    try:
        analysis = analysis_service.run_analysis(game_id, player_color, db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return analysis


@router.get("/{game_id}", response_model=AnalysisResponse)
def get_analysis(game_id: str, db: Session = Depends(get_db)):
    """Повертає збережений аналіз для партії."""
    from app.models.db import Analysis
    analysis = db.query(Analysis).filter(Analysis.game_id == game_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis