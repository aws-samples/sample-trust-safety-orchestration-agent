import json
from unittest.mock import patch

from handlers.case_handler import lambda_handler


class TestGetCaseEvidence:

    @patch("handlers.case_handler.content_sanitization_service")
    @patch("handlers.case_handler.evidence_repository")
    @patch("handlers.case_handler.case_repository")
    def test_get_evidence(
        self, mock_case_repo, mock_evidence_repo, mock_sanitization,
        api_gateway_event, lambda_context,
    ):
        mock_case_repo.get_case.return_value = {
            "case_id": "case-001",
            "status": "under_review",
            "created_at": "2026-04-28T10:00:00Z",
            "updated_at": "2026-04-28T12:00:00Z",
        }
        raw_evidence = {
            "messages": [{"id": "msg-1", "text": "offensive content"}],
            "reports": [{"reporter_id": "user-100"}],
        }
        mock_evidence_repo.get_evidence_package.return_value = raw_evidence
        mock_evidence_repo.get_evidence_metadata.return_value = {
            "total_items": 2,
            "collected_at": "2026-04-28T11:00:00Z",
        }
        sanitized_evidence = {
            "messages": [{"id": "msg-1", "text": "[REDACTED]"}],
            "reports": [{"reporter_id": "user-100"}],
        }
        mock_sanitization.sanitize_evidence_package.return_value = sanitized_evidence

        event = api_gateway_event(
            method="GET",
            path="/cases/case-001/evidence",
            path_params={"caseId": "case-001"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["case_id"] == "case-001"
        assert body["status"] == "under_review"
        assert body["evidence_package"] == sanitized_evidence
        assert body["evidence_metadata"]["total_items"] == 2
        assert body["created_at"] == "2026-04-28T10:00:00Z"
        assert body["updated_at"] == "2026-04-28T12:00:00Z"

        mock_evidence_repo.get_evidence_package.assert_called_once_with("case-001")
        mock_sanitization.sanitize_evidence_package.assert_called_once_with(
            raw_evidence, "labels_only"
        )

    def test_get_evidence_missing_case_id(self, api_gateway_event, lambda_context):
        event = api_gateway_event(
            method="GET",
            path="/cases/evidence",
            path_params={},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "caseId is required" in body["error"]


class TestGetActiveCases:

    @patch("handlers.case_handler.case_repository")
    def test_get_active_cases(self, mock_case_repo, api_gateway_event, lambda_context):
        mock_cases = [
            {"case_id": "case-001", "status": "investigating", "violation_type": "harassment"},
            {"case_id": "case-002", "status": "under_review", "violation_type": "spam"},
            {"case_id": "case-003", "status": "investigating", "violation_type": "scam"},
        ]
        mock_case_repo.get_active_cases.return_value = (mock_cases, None)

        event = api_gateway_event(method="GET", path="/cases/active")
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["cases"] == mock_cases
        assert body["count"] == 3
        mock_case_repo.get_active_cases.assert_called_once_with(limit=50)
