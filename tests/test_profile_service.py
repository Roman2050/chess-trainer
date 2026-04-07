import pytest
from app.services.profile_service import _aggregate, _detect_weaknesses, _get_outcome


class TestGetOutcome:

    def test_white_wins(self):
        assert _get_outcome("1-0", "w") == "win"

    def test_white_loses(self):
        assert _get_outcome("0-1", "w") == "loss"

    def test_black_wins(self):
        assert _get_outcome("0-1", "b") == "win"

    def test_black_loses(self):
        assert _get_outcome("1-0", "b") == "loss"

    def test_draw(self):
        assert _get_outcome("1/2-1/2", "w") == "draw"
        assert _get_outcome("1/2-1/2", "b") == "draw"

    def test_unknown_result_is_draw(self):
        assert _get_outcome("*", "w") == "draw"


class TestDetectWeaknesses:

    def test_no_weaknesses_for_strong_player(self):
        result = _detect_weaknesses(
            acpl=20,
            acpl_opening=15,
            acpl_middlegame=20,
            acpl_endgame=25,
            blunders=0,
            games_count=10,
        )
        assert result == []

    def test_detects_high_acpl(self):
        result = _detect_weaknesses(
            acpl=60, acpl_opening=None,
            acpl_middlegame=None, acpl_endgame=None,
            blunders=0, games_count=5,
        )
        assert "High overall error rate" in result

    def test_detects_weak_opening(self):
        result = _detect_weaknesses(
            acpl=20, acpl_opening=50,
            acpl_middlegame=20, acpl_endgame=20,
            blunders=0, games_count=5,
        )
        assert "Weak opening play" in result

    def test_detects_frequent_blunders(self):
        result = _detect_weaknesses(
            acpl=30, acpl_opening=None,
            acpl_middlegame=None, acpl_endgame=None,
            blunders=10, games_count=5,
        )
        assert "Frequent blunders" in result

    def test_multiple_weaknesses(self):
        result = _detect_weaknesses(
            acpl=70, acpl_opening=60,
            acpl_middlegame=80, acpl_endgame=70,
            blunders=20, games_count=5,
        )
        assert len(result) >= 3


class TestAggregate:

    def _make_game(self, game_id, white, black, result, opening=None):
        class FakeGame:
            pass
        g = FakeGame()
        g.id = game_id
        g.white = white
        g.black = black
        g.result = result
        g.opening = opening
        return g

    def _make_analysis(self, game_id, color, acpl=30.0, blunders=0,
                       mistakes=1, inaccuracies=2):
        class FakeAnalysis:
            pass
        a = FakeAnalysis()
        a.game_id = game_id
        a.player_color = color
        a.acpl = acpl
        a.acpl_opening = acpl
        a.acpl_middlegame = acpl
        a.acpl_endgame = acpl
        a.blunders = blunders
        a.mistakes = mistakes
        a.inaccuracies = inaccuracies
        return a

    def test_aggregate_basic_structure(self):
        games = [self._make_game("g1", "Magnus", "Hikaru", "1-0", "Sicilian")]
        analyses = [self._make_analysis("g1", "w")]

        result = _aggregate("Magnus", games, analyses)

        assert result["player_name"] == "Magnus"
        assert "results" in result
        assert "accuracy" in result
        assert "errors" in result
        assert "openings" in result
        assert "weaknesses" in result

    def test_aggregate_counts_wins(self):
        games = [
            self._make_game("g1", "Magnus", "Hikaru", "1-0"),
            self._make_game("g2", "Magnus", "Anish", "0-1"),
            self._make_game("g3", "Magnus", "Ian", "1/2-1/2"),
        ]
        analyses = [
            self._make_analysis("g1", "w"),
            self._make_analysis("g2", "w"),
            self._make_analysis("g3", "w"),
        ]

        result = _aggregate("Magnus", games, analyses)
        assert result["results"]["wins"] == 1
        assert result["results"]["losses"] == 1
        assert result["results"]["draws"] == 1

    def test_aggregate_top_openings(self):
        games = [
            self._make_game("g1", "Magnus", "A", "1-0", "Sicilian Defense"),
            self._make_game("g2", "Magnus", "B", "1-0", "Sicilian Defense"),
            self._make_game("g3", "Magnus", "C", "1-0", "Italian Game"),
        ]
        analyses = [
            self._make_analysis("g1", "w"),
            self._make_analysis("g2", "w"),
            self._make_analysis("g3", "w"),
        ]

        result = _aggregate("Magnus", games, analyses)
        assert result["openings"]["Sicilian Defense"] == 2
        assert result["openings"]["Italian Game"] == 1

    def test_aggregate_skips_games_without_analysis(self):
        games = [
            self._make_game("g1", "Magnus", "A", "1-0"),
            self._make_game("g2", "Magnus", "B", "1-0"),  # without analysis
        ]
        analyses = [self._make_analysis("g1", "w")]

        result = _aggregate("Magnus", games, analyses)
        assert result["games_count"] == 2
        assert result["analyzed_count"] == 1