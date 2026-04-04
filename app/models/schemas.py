from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class MoveSchema(BaseModel):
    move_number: int
    color: str
    uci: str
    san: str
    fen_after: Optional[str] = None

    model_config = {"from_attributes": True}


class GameCreateResponse(BaseModel):
    id: str
    white: Optional[str]
    black: Optional[str]
    result: Optional[str]
    opening: Optional[str]
    date_played: Optional[date]
    source: str
    moves_count: int


class GameDetailResponse(GameCreateResponse):
    pgn_raw: str
    created_at: datetime
    moves: list[MoveSchema]

    model_config = {"from_attributes": True}
    