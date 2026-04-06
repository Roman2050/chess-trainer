from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import profile_service, llm_service
from app.models.schemas import PlayerProfileResponse, ReportResponse

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/{player_name}/build", response_model=PlayerProfileResponse, status_code=201)
def build_profile(player_name: str, db: Session = Depends(get_db)):
    """
    Builds or updates a player profile based on all analyzed games.
    Run this after analyzing at least one game.
    """
    try:
        profile = profile_service.build_profile(player_name, db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return PlayerProfileResponse.from_orm_model(profile)


@router.get("/{player_name}", response_model=PlayerProfileResponse)
def get_profile(player_name: str, db: Session = Depends(get_db)):
    """Retrieves the saved player profile."""
    profile = profile_service.get_profile(player_name, db)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile for '{player_name}' not found")

    return PlayerProfileResponse.from_orm_model(profile)



@router.post("/{player_name}/report", response_model=ReportResponse)
def generate_report(player_name: str, db: Session = Depends(get_db)):
    """
    Generates a text report through the LLM based on the saved profile.
    Requires a previously built profile via /build.
    Takes 15–60 seconds depending on the model.
    """
    profile = profile_service.get_profile(player_name, db)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Profile for '{player_name}' not found. Run /build first.",
        )

    if not profile.profile_json:
        raise HTTPException(
            status_code=422,
            detail="Profile has no data to generate report from",
        )

    try:
        report_text = llm_service.generate_report(profile.profile_json)
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM service unavailable: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Save the report to your profile
    profile_service.save_report(player_name, report_text, db)

    return ReportResponse(
        player_name=player_name,
        report_text=report_text,
        updated_at=profile.updated_at,
    )