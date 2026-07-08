import json
import pytest
from unittest.mock import patch, MagicMock

from handlers.anomaly_handler import lambda_handler


class TestAnalyzeAnomalies:

    @patch("handlers.anomaly_handler.anomaly_detection_service")
    def test_analyze_anomalies(self, mock_service, api_gateway_event, lambda_context):
        mock_service.calculate_anomaly_score.side_effect = [
            {"user_id": "user-001", "anomaly_score": 0.85, "risk_level": "high"},
            {"user_id": "user-002", "anomaly_score": 0.30, "risk_level": "low"},
        ]

        event = api_gateway_event(
            method="POST",
            path="/anomaly/analyze",
            body={
                "user_ids": ["user-001", "user-002"],
                "behavioral_metrics": {
                    "user-001": {"message_rate": 100, "report_count": 5},
                    "user-002": {"message_rate": 10, "report_count": 0},
                },
            },
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert len(body["results"]) == 2
        assert body["results"][0]["user_id"] == "user-001"
        assert body["results"][0]["anomaly_score"] == 0.85
        assert body["results"][1]["user_id"] == "user-002"
        assert "processing_time_ms" in body

        assert mock_service.calculate_anomaly_score.call_count == 2
        mock_service.calculate_anomaly_score.assert_any_call(
            "user-001", {"message_rate": 100, "report_count": 5}
        )
        mock_service.calculate_anomaly_score.assert_any_call(
            "user-002", {"message_rate": 10, "report_count": 0}
        )

    def test_analyze_too_many_users(self, api_gateway_event, lambda_context):
        user_ids = [f"user-{i}" for i in range(101)]

        event = api_gateway_event(
            method="POST",
            path="/anomaly/analyze",
            body={"user_ids": user_ids},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Maximum 100" in body["error"]

    def test_analyze_missing_user_ids(self, api_gateway_event, lambda_context):
        event = api_gateway_event(
            method="POST",
            path="/anomaly/analyze",
            body={},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "user_ids is required" in body["error"]
