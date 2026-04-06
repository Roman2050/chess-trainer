from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import profile_service
from app.models.schemas import PlayerProfileResponse

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/{player_name}/build", response_model=PlayerProfileResponse, status_code=201)
def build_profile(player_name: str, db: Session = Depends(get_db)):
    """
    Будує або оновлює профіль гравця на основі всіх проаналізованих партій.
    Запускай після того як проаналізував хоча б одну партію.
    """
    try:
        profile = profile_service.build_profile(player_name, db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return PlayerProfileResponse.from_orm_model(profile)


@router.get("/{player_name}", response_model=PlayerProfileResponse)
def get_profile(player_name: str, db: Session = Depends(get_db)):
    """Повертає збережений профіль гравця."""
    profile = profile_service.get_profile(player_name, db)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile for '{player_name}' not found")

    return PlayerProfileResponse.from_orm_model(profile)
