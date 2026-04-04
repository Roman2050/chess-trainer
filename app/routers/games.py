from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import game_service
from app.models.schemas import GameCreateResponse, GameDetailResponse

router = APIRouter(prefix="/games", tags=["games"])


@router.post("/upload", response_model=GameCreateResponse, status_code=201)
async def upload_pgn(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Loads a PGN file and saves the game to the database."""
    if not file.filename.endswith(".pgn"):
        raise HTTPException(status_code=400, detail="File must be a .pgn file")

    content = await file.read()

    try:
        pgn_text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding must be UTF-8")

    try:
        game = game_service.save_game(pgn_text, source="upload", db=db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return GameCreateResponse(
        id=game.id,
        white=game.white,
        black=game.black,
        result=game.result,
        opening=game.opening,
        date_played=game.date_played,
        source=game.source,
        moves_count=len(game.moves),
    )


@router.get("/{game_id}", response_model=GameDetailResponse)
def get_game(game_id: str, db: Session = Depends(get_db)):
    """Returns a game with moves by ID."""
    game = game_service.get_game_by_id(game_id, db)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameDetailResponse(
        id=game.id,
        white=game.white,
        black=game.black,
        result=game.result,
        opening=game.opening,
        date_played=game.date_played,
        source=game.source,
        moves_count=len(game.moves),
        pgn_raw=game.pgn_raw,
        created_at=game.created_at,
        moves=game.moves,
    )


@router.get("/", response_model=list[GameCreateResponse])
def list_games(db: Session = Depends(get_db)):
    """Returns a list of the most recent 50 chess games."""
    games = game_service.get_all_games(db)
    return [
        GameCreateResponse(
            id=g.id,
            white=g.white,
            black=g.black,
            result=g.result,
            opening=g.opening,
            date_played=g.date_played,
            source=g.source,
            moves_count=len(g.moves),
        )
        for g in games
    ]
