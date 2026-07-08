from unittest.mock import patch

from services import confidence_calculator_service as svc


@patch("repositories.config_repository.get_active_value", return_value=None)
class TestCalculateConfidenceScores:
    def test_empty_evidence(self, _mock):
        scores = svc.calculate_confidence_scores({})
        assert scores == {}

    def test_scam_patterns(self, _mock):
        evidence = {
            "message_analysis": {
                "scam_patterns": [{"pattern": "send money"}, {"pattern": "gift card"}],
            }
        }
        scores = svc.calculate_confidence_scores(evidence)
        assert "scam" in scores
        assert scores["scam"] > 0

    def test_threat_indicators(self, _mock):
        evidence = {
            "message_analysis": {
                "threat_indicators": [{"indicator": "kill"}, {"indicator": "stalk"}],
            }
        }
        scores = svc.calculate_confidence_scores(evidence)
        assert "harassment" in scores
        assert scores["harassment"] == 0.5

    def test_crisis_indicator_sets_self_harm(self, _mock):
        evidence = {
            "message_analysis": {
                "has_crisis_indicators": True,
            }
        }
        scores = svc.calculate_confidence_scores(evidence)
        assert scores["self_harm"] == 0.95

    def test_fake_profile_ai_generated(self, _mock):
        evidence = {
            "image_analysis": {
                "ai_generated_probability": 0.9,
            }
        }
        scores = svc.calculate_confidence_scores(evidence)
        assert "fake_profile" in scores
        assert scores["fake_profile"] > 0.3

    def test_bad_actor_match(self, _mock):
        evidence = {
            "bad_actor_matches": [
                {"confidence_score": 0.95},
            ]
        }
        scores = svc.calculate_confidence_scores(evidence)
        assert "repeat_offender" in scores
        assert scores["repeat_offender"] == 0.95

    def test_report_boost(self, _mock):
        evidence = {
            "message_analysis": {
                "scam_patterns": [{"pattern": "send money"}],
            },
            "previous_reports": [{"id": 1}, {"id": 2}, {"id": 3}],
        }
        scores = svc.calculate_confidence_scores(evidence)
        assert scores["scam"] > 0.2

    def test_report_boost_capped(self, _mock):
        evidence = {
            "message_analysis": {
                "scam_patterns": [{"pattern": "p"}],
            },
            "previous_reports": [{"id": i} for i in range(20)],
        }
        scores = svc.calculate_confidence_scores(evidence)
        assert scores["scam"] <= 1.0

    def test_hostile_sentiment_boosts_scam(self, _mock):
        evidence = {
            "message_analysis": {
                "scam_patterns": [{"pattern": "money"}],
                "sentiment_summary": {"overall": "hostile"},
            }
        }
        scores = svc.calculate_confidence_scores(evidence)
        assert scores["scam"] >= 0.3

    def test_stock_photo_contributes_to_fake_profile(self, _mock):
        evidence = {
            "image_analysis": {
                "stock_photo_matches": [{"url": "stock.com/1"}],
            }
        }
        scores = svc.calculate_confidence_scores(evidence)
        assert "fake_profile" in scores
        assert scores["fake_profile"] == 0.3


class TestGetPrimaryViolation:
    def test_empty_returns_unknown(self):
        vtype, score = svc.get_primary_violation({})
        assert vtype == "unknown"
        assert score == 0.0

    def test_returns_highest(self):
        vtype, score = svc.get_primary_violation({"scam": 0.8, "harassment": 0.3})
        assert vtype == "scam"
        assert score == 0.8
