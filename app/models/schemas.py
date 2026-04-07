from pydantic import BaseModel, field_validator
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


class AnalysisResponse(BaseModel):
    id: str
    game_id: str
    player_color: str
    acpl: Optional[float]
    acpl_opening: Optional[float]
    acpl_middlegame: Optional[float]
    acpl_endgame: Optional[float]
    blunders: int
    mistakes: int
    inaccuracies: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileResultsSchema(BaseModel):
    wins: int
    draws: int
    losses: int
    win_rate: Optional[float]


class ProfileAccuracySchema(BaseModel):
    acpl: Optional[float]
    acpl_opening: Optional[float]
    acpl_middlegame: Optional[float]
    acpl_endgame: Optional[float]


class ProfileErrorsSchema(BaseModel):
    blunders: int
    mistakes: int
    inaccuracies: int
    blunders_per_game: Optional[float]


class PlayerProfileResponse(BaseModel):
    id: str
    player_name: str
    games_count: int
    results: Optional[ProfileResultsSchema]
    accuracy: Optional[ProfileAccuracySchema]
    errors: Optional[ProfileErrorsSchema]
    openings: Optional[dict[str, int]]
    weaknesses: Optional[list[str]]
    report_text: Optional[str]
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, profile: "PlayerProfile") -> "PlayerProfileResponse":
        pj = profile.profile_json or {}
        return cls(
            id=profile.id,
            player_name=profile.player_name,
            games_count=profile.games_count,
            results=pj.get("results"),
            accuracy=pj.get("accuracy"),
            errors=pj.get("errors"),
            openings=pj.get("openings"),
            weaknesses=pj.get("weaknesses"),
            report_text=profile.report_text,
            updated_at=profile.updated_at,
        )


class ReportResponse(BaseModel):
    player_name: str
    report_text: str
    updated_at: datetime
    

class JobCreateRequest(BaseModel):
    player_name: str
    player_color: str = "w"
    game_type: str = "rapid"
    limit: int = 20

    @field_validator("player_color")
    @classmethod
    def validate_color(cls, v):
        if v not in ("w", "b"):
            raise ValueError("player_color must be 'w' or 'b'")
        return v

    @field_validator("game_type")
    @classmethod
    def validate_game_type(cls, v):
        valid = {"bullet", "blitz", "rapid", "classical"}
        if v not in valid:
            raise ValueError(f"game_type must be one of {valid}")
        return v

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v):
        if not 1 <= v <= 40:
            raise ValueError("limit must be between 1 and 40")
        return v


class JobResponse(BaseModel):
    id: str
    player_name: str
    player_color: str
    game_type: str
    status: str
    total_games: int
    processed: int
    failed: int
    error: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}