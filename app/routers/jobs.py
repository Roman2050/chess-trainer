from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import job_service
from app.models.schemas import JobCreateRequest, JobResponse
from app.utils.validators import validate_uuid

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/analyze", response_model=JobResponse, status_code=202)
def start_analysis(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Runs a background analysis of the player's games from Lichess.
    Returns a job_id for tracking progress.
    Status 202 = accepted for processing.
    """
    job = job_service.create_job(
        player_name=request.player_name,
        player_color=request.player_color,
        game_type=request.game_type,
        limit=request.limit,
        db=db,
    )

    background_tasks.add_task(
        job_service.run_job,
        job_id=job.id,
        player_name=request.player_name,
        player_color=request.player_color,
        game_type=request.game_type,
        limit=request.limit,
    )

    return job


@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Returns the current status and progress of the job."""
    validate_uuid(job_id, "job_id")

    job = job_service.get_job(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job