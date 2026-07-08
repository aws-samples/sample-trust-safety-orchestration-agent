from unittest.mock import patch

from services import anomaly_detection_service as svc


class TestGetAccountTier:
    def test_new_account(self):
        assert svc.get_account_tier(0) == "new"
        assert svc.get_account_tier(29) == "new"

    def test_established_account(self):
        assert svc.get_account_tier(30) == "established"
        assert svc.get_account_tier(179) == "established"

    def test_veteran_account(self):
        assert svc.get_account_tier(180) == "veteran"
        assert svc.get_account_tier(365) == "veteran"


class TestCalculateAnomalyScore:
    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_normal_behavior_low_score(self, _mock):
        result = svc.calculate_anomaly_score("user-1", {
            "message_velocity": 10,
            "response_rate": 0.5,
            "profile_view_rate": 50,
            "match_accept_rate": 0.5,
            "recent_report_count": 0,
            "account_age_days": 90,
        })
        assert result["anomaly_score"] == 0.0
        assert result["factors"] == []
        assert result["account_tier"] == "established"
        assert result["exceeds_investigation_trigger"] is False

    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_high_message_velocity(self, _mock):
        result = svc.calculate_anomaly_score("user-2", {
            "message_velocity": 100,
            "account_age_days": 10,
        })
        contrib = min((100 - 50) / 100, 0.3)
        assert result["anomaly_score"] == round(contrib, 4)
        assert any(f["factor"] == "high_message_velocity" for f in result["factors"])
        assert result["account_tier"] == "new"

    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_multiple_flags_compound(self, _mock):
        result = svc.calculate_anomaly_score("user-3", {
            "message_velocity": 150,
            "response_rate": 0.01,
            "profile_view_rate": 500,
            "match_accept_rate": 0.99,
            "recent_report_count": 5,
            "account_age_days": 5,
        })
        assert result["anomaly_score"] == 1.0
        assert result["exceeds_investigation_trigger"] is True
        assert len(result["factors"]) == 5

    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_score_capped_at_1(self, _mock):
        result = svc.calculate_anomaly_score("user-4", {
            "message_velocity": 999,
            "response_rate": 0.0,
            "profile_view_rate": 9999,
            "match_accept_rate": 1.0,
            "recent_report_count": 100,
            "account_age_days": 1,
        })
        assert result["anomaly_score"] == 1.0

    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_reports_only(self, _mock):
        result = svc.calculate_anomaly_score("user-5", {
            "recent_report_count": 2,
            "account_age_days": 200,
        })
        assert result["anomaly_score"] == 0.2
        assert result["account_tier"] == "veteran"

    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_low_response_rate_flag(self, _mock):
        result = svc.calculate_anomaly_score("user-6", {
            "response_rate": 0.01,
            "account_age_days": 60,
        })
        assert result["anomaly_score"] == 0.2
        assert result["factors"][0]["factor"] == "low_response_rate"


class TestBatchCalculateScores:
    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_batch(self, _mock):
        users = [
            ("u1", {"account_age_days": 10}),
            ("u2", {"recent_report_count": 3, "account_age_days": 100}),
        ]
        results = svc.batch_calculate_scores(users)
        assert len(results) == 2
        assert results[0]["user_id"] == "u1"
        assert results[1]["user_id"] == "u2"
