import io
import chess.pgn
import httpx

LICHESS_API_URL = "https://lichess.org/api/games/user/{username}"

VALID_GAME_TYPES = {"bullet", "blitz", "rapid", "classical"}
MAX_GAMES_LIMIT  = 40


def fetch_pgn(
    username: str,
    game_type: str,
    limit: int,
) -> list[str]:
    """
    Loads games from the Lichess API.
    Returns a list of PGN lines (one game = one line).
    """
    if game_type not in VALID_GAME_TYPES:
        raise ValueError(f"Invalid game_type '{game_type}'. Must be one of: {VALID_GAME_TYPES}")

    if limit > MAX_GAMES_LIMIT:
        raise ValueError(f"Limit cannot exceed {MAX_GAMES_LIMIT}")

    response = httpx.get(
        LICHESS_API_URL.format(username=username),
        params={
            "max": limit,
            "perfType": game_type,
            "pgnInJson": "false",
            "moves": "true",
            "tags": "true",
            "clocks": "false",
            "evals": "false",
        },
        headers={"Accept": "application/x-chess-pgn"},
        timeout=60.0,
    )

    if response.status_code == 404:
        raise ValueError(f"Lichess user '{username}' not found")

    response.raise_for_status()

    return _split_pgn(response.text)


def _split_pgn(raw: str) -> list[str]:
    """Splits a single large PGN file into individual games."""
    games = []
    stream = io.StringIO(raw)

    while True:
        game = chess.pgn.read_game(stream)
        if game is None:
            break

        exporter = chess.pgn.StringExporter(headers=True, variations=False, comments=False)
        pgn_str = game.accept(exporter)

        if pgn_str and pgn_str.strip():
            games.append(pgn_str.strip())

    return games