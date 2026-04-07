import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer,
    Float, Date, DateTime, ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Game(Base):
    __tablename__ = "games"

    id          = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    pgn_raw     = Column(Text, nullable=False)
    white       = Column(String(100), nullable=True)
    black       = Column(String(100), nullable=True)
    result      = Column(String(10), nullable=True)    # "1-0" | "0-1" | "1/2-1/2"
    opening     = Column(String(200), nullable=True)
    date_played = Column(Date, nullable=True)
    source      = Column(String(50), default="upload") # "upload" | "lichess"
    created_at  = Column(DateTime, default=datetime.utcnow)

    moves    = relationship("Move", back_populates="game", cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="game", uselist=False, cascade="all, delete-orphan")


class Move(Base):
    __tablename__ = "moves"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    game_id     = Column(UUID(as_uuid=False), ForeignKey("games.id"), nullable=False)
    move_number = Column(Integer, nullable=False)
    color       = Column(String(1), nullable=False)  # 'w' | 'b'
    uci         = Column(String(10), nullable=False)
    san         = Column(String(10), nullable=False)
    fen_after   = Column(Text, nullable=True)
    eval_cp     = Column(Integer, nullable=True)     # This will be populated in after Stockfish.
    best_move   = Column(String(10), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="moves")


class Analysis(Base):
    __tablename__ = "analyses"

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    game_id         = Column(UUID(as_uuid=False), ForeignKey("games.id"), unique=True, nullable=False)
    player_color    = Column(String(1), nullable=False)
    acpl            = Column(Float, nullable=True)
    acpl_opening    = Column(Float, nullable=True)
    acpl_middlegame = Column(Float, nullable=True)
    acpl_endgame    = Column(Float, nullable=True)
    blunders        = Column(Integer, default=0)     # loss > 200cp
    mistakes        = Column(Integer, default=0)     # loss 100–200cp
    inaccuracies    = Column(Integer, default=0)     # loss 50–100cp
    raw_json        = Column(JSONB, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    game = relationship("Game", back_populates="analysis")


class PlayerProfile(Base):
    __tablename__ = "player_profiles"

    id           = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    player_name  = Column(String(100), unique=True, nullable=False)
    games_count  = Column(Integer, default=0)
    profile_json = Column(JSONB, nullable=True)
    report_text  = Column(Text, nullable=True)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    