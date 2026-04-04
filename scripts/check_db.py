# scripts/check_db.py
from app.database import SessionLocal
from app.models.db import Game, Move, Analysis, PlayerProfile


def main():
    db = SessionLocal()
    try:
        print("Games:", db.query(Game).count())
        print("Moves:", db.query(Move).count())
        print("Analyses:", db.query(Analysis).count())
        print("Profiles:", db.query(PlayerProfile).count())
        print("✅ DB connection OK")
    finally:
        db.close()


if __name__ == "__main__":
    main()