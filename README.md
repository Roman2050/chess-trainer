# Chess Trainer API

  

Backend system for chess game analysis, player profiling, and AI-powered coaching reports.

  

## Tech Stack

- **FastAPI** — REST API

- **PostgreSQL** — storage

- **Stockfish** — engine analysis

- **Ollama / Anthropic** — LLM reports

- **python-chess** — PGN parsing

  

## Quick Start

  

### Prerequisites

- Docker

- Python 3.12+

- [uv](https://docs.astral.sh/uv/)

- [Stockfish](https://stockfishchess.org/download/)

- [Ollama](https://ollama.com/download) + `ollama pull llama3.2`

  

### Setup

```bash

git clone https://github.com/YOUR_USERNAME/chess-trainer.git

cd chess-trainer

cp .env.example .env

# Edit .env — add your STOCKFISH_PATH

docker compose up -d   # starts PostgreSQL

uv sync

uv run alembic upgrade head

uv run uvicorn app.main:app --reload

```

  

API docs: http://localhost:8000/docs

  
  

## Workflow

  

1.POST /games/upload              → upload PGN file

2.POST /analysis/run/{game_id}    → run Stockfish (30–90s)

3.POST /profiles/{name}/build     → aggregate stats

4.POST /profiles/{name}/report    → generate coaching report

  
  

## Project Structure

  

app/

├── routers/      # HTTP endpoints

├── services/     # business logic

├── models/       # ORM + Pydantic schemas

└── utils/        # parser, validators