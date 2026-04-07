from fastapi import FastAPI
from app.routers import games
from app.routers import games, analysis, profiles, jobs

app = FastAPI(
    title="Chess Trainer API",
    description="Chess game analysis and training system",
    version="0.1.0",
)

app.include_router(games.router)
app.include_router(analysis.router)
app.include_router(profiles.router)
app.include_router(jobs.router)


@app.get("/health")
def health():
    return {"status": "ok"}
