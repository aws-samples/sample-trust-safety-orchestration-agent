import json
from unittest.mock import patch

from handlers.review_handler import lambda_handler


class TestGetReviewQueue:

    @patch("handlers.review_handler.review_queue_repository")
    def test_get_review_queue(self, mock_repo, api_gateway_event, lambda_context):
        mock_cases = [
            {"case_id": "case-001", "priority": "high"},
            {"case_id": "case-002", "priority": "medium"},
        ]
        mock_repo.get_queue.return_value = (mock_cases, None)
        mock_repo.get_queue_depth.return_value = {"high": 3, "medium": 5, "low": 2}

        event = api_gateway_event(method="GET", path="/review-queue")
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["cases"] == mock_cases
        assert body["total_count"] == 10
        assert body["queue_depth_by_priority"] == {"high": 3, "medium": 5, "low": 2}
        mock_repo.get_queue.assert_called_once_with(priority_filter=None, limit=20)

    @patch("handlers.review_handler.review_queue_repository")
    def test_get_review_queue_with_priority_filter(self, mock_repo, api_gateway_event, lambda_context):
        mock_cases = [{"case_id": "case-001", "priority": "high"}]
        mock_repo.get_queue.return_value = (mock_cases, None)
        mock_repo.get_queue_depth.return_value = {"high": 3}

        event = api_gateway_event(
            method="GET",
            path="/review-queue",
            query_params={"priority": "high", "limit": "10"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["cases"] == mock_cases
        mock_repo.get_queue.assert_called_once_with(priority_filter="high", limit=10)


class TestSubmitDecision:

    @patch("handlers.review_handler.audit_service")
    @patch("handlers.review_handler.reviewer_wellbeing_service")
    @patch("handlers.review_handler.feedback_loop_service")
    @patch("handlers.review_handler.enforcement_engine_service")
    @patch("handlers.review_handler.case_repository")
    def test_submit_decision_approve(
        self, mock_case_repo, mock_enforcement, mock_feedback,
        mock_wellbeing, mock_audit, api_gateway_event, lambda_context,
    ):
        mock_case_repo.get_case.return_value = {
            "case_id": "case-001",
            "user_id": "user-123",
            "violation_type": "harassment",
            "confidence_score": 0.92,
            "content_severity": "high",
        }
        mock_enforcement.execute_action.return_value = {
            "case_id": "case-001",
            "action_status": "completed",
        }

        event = api_gateway_event(
            method="POST",
            path="/review-queue/case-001/decision",
            body={"decision": "approve_action", "action": "permanent_ban", "notes": "Clear violation"},
            path_params={"caseId": "case-001"},
            claims={"sub": "reviewer-42"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["action_status"] == "completed"

        mock_enforcement.execute_action.assert_called_once_with(
            case_id="case-001",
            user_id="user-123",
            action="permanent_ban",
            violation_type="harassment",
            confidence_score=0.92,
            is_autonomous=False,
            reviewer_id="reviewer-42",
        )
        mock_feedback.record_decision_feedback.assert_called_once()
        mock_wellbeing.track_exposure.assert_called_once_with(
            reviewer_id="reviewer-42",
            case_id="case-001",
            content_severity="high",
        )
        mock_audit.log_enforcement_action.assert_called_once()

    @patch("handlers.review_handler.audit_service")
    @patch("handlers.review_handler.reviewer_wellbeing_service")
    @patch("handlers.review_handler.feedback_loop_service")
    @patch("handlers.review_handler.case_repository")
    def test_submit_decision_dismiss(
        self, mock_case_repo, mock_feedback, mock_wellbeing, mock_audit,
        api_gateway_event, lambda_context,
    ):
        mock_case_repo.get_case.return_value = {
            "case_id": "case-002",
            "user_id": "user-456",
            "violation_type": "spam",
            "confidence_score": 0.55,
            "content_severity": "low",
        }

        event = api_gateway_event(
            method="POST",
            path="/review-queue/case-002/decision",
            body={"decision": "dismiss"},
            path_params={"caseId": "case-002"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["action_status"] == "dismissed"
        assert body["case_id"] == "case-002"

        mock_case_repo.update_case_status.assert_called_once_with("case-002", "resolved")

    @patch("handlers.review_handler.audit_service")
    @patch("handlers.review_handler.reviewer_wellbeing_service")
    @patch("handlers.review_handler.feedback_loop_service")
    @patch("handlers.review_handler.escalation_service")
    @patch("handlers.review_handler.case_repository")
    def test_submit_decision_escalate(
        self, mock_case_repo, mock_escalation, mock_feedback,
        mock_wellbeing, mock_audit, api_gateway_event, lambda_context,
    ):
        mock_case_repo.get_case.return_value = {
            "case_id": "case-003",
            "user_id": "user-789",
            "violation_type": "self_harm",
            "confidence_score": 0.80,
            "content_severity": "critical",
        }
        mock_escalation.escalate_case.return_value = {
            "case_id": "case-003",
            "escalation_status": "escalated",
        }

        event = api_gateway_event(
            method="POST",
            path="/review-queue/case-003/decision",
            body={"decision": "escalate"},
            path_params={"caseId": "case-003"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["escalation_status"] == "escalated"

        mock_escalation.escalate_case.assert_called_once_with(
            case_id="case-003",
            user_id="user-789",
            reason="reviewer_escalation",
        )

    def test_submit_decision_missing_case_id(self, api_gateway_event, lambda_context):
        event = api_gateway_event(
            method="POST",
            path="/review-queue/decision",
            body={"decision": "approve_action", "action": "permanent_ban"},
            path_params={},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "caseId is required" in body["error"]

    @patch("handlers.review_handler.case_repository")
    def test_submit_decision_case_not_found(self, mock_case_repo, api_gateway_event, lambda_context):
        mock_case_repo.get_case.return_value = None

        event = api_gateway_event(
            method="POST",
            path="/review-queue/case-999/decision",
            body={"decision": "approve_action", "action": "permanent_ban"},
            path_params={"caseId": "case-999"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 404
        body = json.loads(result["body"])
        assert "not found" in body["error"]

    @patch("handlers.review_handler.case_repository")
    def test_submit_decision_invalid_decision(self, mock_case_repo, api_gateway_event, lambda_context):
        mock_case_repo.get_case.return_value = {
            "case_id": "case-001",
            "user_id": "user-123",
            "violation_type": "spam",
            "confidence_score": 0.70,
        }

        event = api_gateway_event(
            method="POST",
            path="/review-queue/case-001/decision",
            body={"decision": "invalid_value"},
            path_params={"caseId": "case-001"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Invalid decision" in body["error"]


class TestCheckStaleCases:

    @patch("handlers.review_handler.escalation_service")
    def test_check_stale_cases(self, mock_escalation, lambda_context):
        mock_alerts = [
            {"case_id": "case-old-1", "age_hours": 48},
            {"case_id": "case-old-2", "age_hours": 72},
        ]
        mock_escalation.check_queue_age_alerts.return_value = mock_alerts

        event = {"action": "check_stale_cases"}
        result = lambda_handler(event, lambda_context)

        assert result["alerts"] == mock_alerts
        mock_escalation.check_queue_age_alerts.assert_called_once()
