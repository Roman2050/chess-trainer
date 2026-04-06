import httpx
from app.config import settings


REPORT_PROMPT = """You are an expert chess coach. Analyze the player profile below and write a coaching report.

Player: {player_name}
Games analyzed: {analyzed_count}

RESULTS:
- Wins: {wins} | Draws: {draws} | Losses: {losses}
- Win rate: {win_rate}%

ACCURACY (ACPL — lower is better, <30 is strong):
- Overall ACPL: {acpl}
- Opening ACPL: {acpl_opening}
- Middlegame ACPL: {acpl_middlegame}
- Endgame ACPL: {acpl_endgame}

ERRORS:
- Blunders: {blunders} total ({blunders_per_game}/game)
- Mistakes: {mistakes}
- Inaccuracies: {inaccuracies}

TOP OPENINGS: {openings}

DETECTED WEAKNESSES: {weaknesses}

Write a coaching report with these sections:
1. Overall Assessment (2-3 sentences)
2. Key Weaknesses (specific, actionable)
3. Training Recommendations (3 concrete steps)

Be direct and specific. Do not mention that you are an AI."""


def generate_report(profile_json: dict) -> str:
    """
    Generates a text report based on the player's profile.
    Selects a provider from the configuration.
    """
    prompt = _build_prompt(profile_json)

    if settings.llm_provider == "ollama":
        return _call_ollama(prompt)
    elif settings.llm_provider == "anthropic":
        return _call_anthropic(prompt)
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")


# --- private ---

def _build_prompt(p: dict) -> str:
    results  = p.get("results") or {}
    accuracy = p.get("accuracy") or {}
    errors   = p.get("errors") or {}

    return REPORT_PROMPT.format(
        player_name=p.get("player_name", "Unknown"),
        analyzed_count=p.get("analyzed_count", 0),
        wins=results.get("wins", 0),
        draws=results.get("draws", 0),
        losses=results.get("losses", 0),
        win_rate=results.get("win_rate", "N/A"),
        acpl=accuracy.get("acpl", "N/A"),
        acpl_opening=accuracy.get("acpl_opening", "N/A"),
        acpl_middlegame=accuracy.get("acpl_middlegame", "N/A"),
        acpl_endgame=accuracy.get("acpl_endgame", "N/A"),
        blunders=errors.get("blunders", 0),
        blunders_per_game=errors.get("blunders_per_game", 0),
        mistakes=errors.get("mistakes", 0),
        inaccuracies=errors.get("inaccuracies", 0),
        openings=p.get("openings", {}),
        weaknesses=p.get("weaknesses", []),
    )


def _call_ollama(prompt: str) -> str:
    """Calls the local Ollama model."""
    response = httpx.post(
        f"{settings.ollama_url}/api/generate",
        json={
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        },
        timeout=120.0,  # An LLM can take a long time to think
    )
    response.raise_for_status()
    return response.json()["response"]


def _call_anthropic(prompt: str) -> str:
    """Викликає Anthropic API."""
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set")

    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["content"][0]["text"]