import pytest
from app.utils.pgn_parser import parse_pgn, ParsedGame


class TestParsePgn:

    def test_valid_pgn_returns_parsed_game(self, valid_pgn):
        result = parse_pgn(valid_pgn)
        assert isinstance(result, ParsedGame)

    def test_parses_player_names(self, valid_pgn):
        result = parse_pgn(valid_pgn)
        assert result.white == "Magnus"
        assert result.black == "Hikaru"

    def test_parses_result(self, valid_pgn):
        result = parse_pgn(valid_pgn)
        assert result.result == "1-0"

    def test_parses_opening(self, valid_pgn):
        result = parse_pgn(valid_pgn)
        assert result.opening == "Sicilian Defense"

    def test_parses_date(self, valid_pgn):
        from datetime import date
        result = parse_pgn(valid_pgn)
        assert result.date_played == date(2024, 1, 15)

    def test_parses_correct_move_count(self, valid_pgn):
        result = parse_pgn(valid_pgn)
        # 5 full moves = 10 half-moves
        assert len(result.moves) == 10

    def test_moves_have_correct_colors(self, valid_pgn):
        result = parse_pgn(valid_pgn)
        white_moves = [m for m in result.moves if m.color == 'w']
        black_moves = [m for m in result.moves if m.color == 'b']
        assert len(white_moves) == 5
        assert len(black_moves) == 5

    def test_moves_have_uci_format(self, valid_pgn):
        result = parse_pgn(valid_pgn)
        first_move = result.moves[0]
        assert first_move.uci == "e2e4"
        assert first_move.san == "e4"

    def test_moves_have_fen_after(self, valid_pgn):
        result = parse_pgn(valid_pgn)
        for move in result.moves:
            assert move.fen_after is not None
            assert len(move.fen_after) > 0

    def test_invalid_pgn_raises_value_error(self, empty_pgn):
        with pytest.raises(ValueError, match="Invalid PGN"):
            parse_pgn(empty_pgn)

    def test_no_moves_pgn_raises_value_error(self, no_moves_pgn):
        with pytest.raises(ValueError, match="no moves"):
            parse_pgn(no_moves_pgn)

    def test_pgn_raw_preserved(self, valid_pgn):
        result = parse_pgn(valid_pgn)
        assert result.pgn_raw == valid_pgn.strip()

    def test_missing_optional_fields_are_none(self):
        minimal_pgn = "1. e4 e5 2. Nf3 Nc6 *"
        result = parse_pgn(minimal_pgn)
        assert result.white is None
        assert result.opening is None
        assert result.date_played is None
