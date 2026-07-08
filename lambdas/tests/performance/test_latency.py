"""Performance benchmarks for compute-bound service functions.

These tests measure wall-clock latency of pure computation (all external
dependencies mocked). They use simple time.time() deltas and assert that
the operations complete within the specified budget.
"""

import time
from unittest.mock import patch

from services import anomaly_detection_service
from services import confidence_calculator_service


class TestAnomalyScoreLatency:
    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_anomaly_score_calculation_under_10ms(self, _mock_config):
        """Single-user anomaly score calculation must complete in <10ms."""
        metrics = {
            "message_velocity": 80,
            "response_rate": 0.03,
            "profile_view_rate": 300,
            "match_accept_rate": 0.97,
            "recent_report_count": 3,
            "account_age_days": 15,
        }

        start = time.time()
        result = anomaly_detection_service.calculate_anomaly_score("perf-user-1", metrics)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 10, f"Anomaly score took {elapsed_ms:.2f}ms, expected <10ms"
        assert "anomaly_score" in result

    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_batch_anomaly_100_users_under_100ms(self, _mock_config):
        """Batch anomaly scoring for 100 users must complete in <100ms."""
        user_metrics = [
            (
                f"perf-user-{i}",
                {
                    "message_velocity": 50 + i,
                    "response_rate": max(0.01, 0.5 - i * 0.005),
                    "profile_view_rate": 100 + i * 2,
                    "match_accept_rate": min(0.99, 0.5 + i * 0.005),
                    "recent_report_count": i % 5,
                    "account_age_days": 10 + i,
                },
            )
            for i in range(100)
        ]

        start = time.time()
        results = anomaly_detection_service.batch_calculate_scores(user_metrics)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 100, f"Batch scoring took {elapsed_ms:.2f}ms, expected <100ms"
        assert len(results) == 100
        # Verify results are structurally sound
        assert all("anomaly_score" in r for r in results)
        assert all("user_id" in r for r in results)


class TestConfidenceCalculationLatency:
    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_confidence_calculation_under_10ms(self, _mock_config):
        """Single confidence score calculation must complete in <10ms."""
        evidence = {
            "message_analysis": {
                "scam_patterns": ["crypto_investment", "money_transfer", "urgency_language"],
                "threat_indicators": ["explicit_threat"],
                "sentiment_summary": {"overall": "hostile", "hostility_score": 0.85},
                "has_crisis_indicators": False,
            },
            "image_analysis": {
                "ai_generated_probability": 0.8,
                "reverse_image_matches": [{"url": "https://example.com/img1"}],
                "stock_photo_matches": [{"id": "stock-1"}],
            },
            "bad_actor_matches": [
                {"confidence_score": 0.92, "platform": "other"},
            ],
            "previous_reports": [
                {"report_id": f"r{i}"} for i in range(5)
            ],
        }

        start = time.time()
        scores = confidence_calculator_service.calculate_confidence_scores(evidence)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 10, f"Confidence calc took {elapsed_ms:.2f}ms, expected <10ms"
        assert isinstance(scores, dict)
        assert len(scores) > 0
