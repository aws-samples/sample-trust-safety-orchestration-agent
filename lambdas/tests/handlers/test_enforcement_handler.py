import json
from unittest.mock import patch

from handlers.enforcement_handler import lambda_handler


class TestExecuteSingle:

    @patch("handlers.enforcement_handler.enforcement_engine_service")
    def test_execute_single(self, mock_service, api_gateway_event, lambda_context):
        mock_service.execute_action.return_value = {
            "case_id": "case-001",
            "action": "permanent_ban",
            "action_status": "completed",
        }

        event = api_gateway_event(
            method="POST",
            path="/enforcement/execute",
            body={
                "case_id": "case-001",
                "user_id": "user-123",
                "action": "permanent_ban",
                "violation_type": "harassment",
                "confidence_score": 0.95,
                "is_autonomous": True,
            },
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["case_id"] == "case-001"
        assert body["action_status"] == "completed"

        mock_service.execute_action.assert_called_once_with(
            case_id="case-001",
            user_id="user-123",
            action="permanent_ban",
            violation_type="harassment",
            confidence_score=0.95,
            is_autonomous=True,
            reviewer_id=None,
            duration_hours=None,
        )

    def test_execute_single_missing_fields(self, api_gateway_event, lambda_context):
        event = api_gateway_event(
            method="POST",
            path="/enforcement/execute",
            body={"user_id": "user-123"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Missing required fields" in body["error"]
        assert "case_id" in body["error"]
        assert "action" in body["error"]
        assert "violation_type" in body["error"]
        assert "confidence_score" in body["error"]


class TestExecuteBulk:

    @patch("handlers.enforcement_handler.enforcement_engine_service")
    def test_execute_bulk(self, mock_service, api_gateway_event, lambda_context):
        user_ids = [f"user-{i}" for i in range(10)]
        mock_service.execute_bulk_action.return_value = {
            "case_id": "case-bulk-001",
            "total_users": 10,
            "action_status": "completed",
        }

        event = api_gateway_event(
            method="POST",
            path="/enforcement/bulk",
            body={
                "case_id": "case-bulk-001",
                "user_ids": user_ids,
                "action": "temporary_restriction",
                "violation_type": "spam",
                "attack_pattern": "coordinated_spam",
            },
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["total_users"] == 10
        assert body["action_status"] == "completed"

        mock_service.execute_bulk_action.assert_called_once_with(
            case_id="case-bulk-001",
            user_ids=user_ids,
            action="temporary_restriction",
            violation_type="spam",
            attack_pattern="coordinated_spam",
        )

    def test_execute_bulk_too_many_users(self, api_gateway_event, lambda_context):
        user_ids = [f"user-{i}" for i in range(501)]

        event = api_gateway_event(
            method="POST",
            path="/enforcement/bulk",
            body={
                "case_id": "case-bulk-002",
                "user_ids": user_ids,
                "action": "temporary_restriction",
                "violation_type": "spam",
            },
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Maximum 500" in body["error"]

    def test_execute_bulk_missing_fields(self, api_gateway_event, lambda_context):
        event = api_gateway_event(
            method="POST",
            path="/enforcement/bulk",
            body={"case_id": "case-bulk-003", "action": "temporary_restriction"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Missing required fields" in body["error"]
        assert "user_ids" in body["error"]
        assert "violation_type" in body["error"]
