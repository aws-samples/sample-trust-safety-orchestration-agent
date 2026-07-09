from unittest.mock import patch

from services import escalation_service as svc


class TestCalculatePriority:
    def test_sensitive_category_always_critical(self):
        assert svc.calculate_priority("self_harm", 0.5, "sensitive_category") == "critical"

    def test_system_error_always_high(self):
        assert svc.calculate_priority("scam", 0.5, "system_error") == "high"

    def test_high_weight_high_confidence(self):
        result = svc.calculate_priority("child_safety", 0.9, "below_threshold")
        assert result == "critical"

    def test_low_weight_low_confidence(self):
        result = svc.calculate_priority("explicit_content", 0.1, "below_threshold")
        assert result == "medium"

    def test_medium_range(self):
        result = svc.calculate_priority("fake_profile", 0.5, "below_threshold")
        assert result == "medium"

    def test_harassment_high_confidence(self):
        result = svc.calculate_priority("harassment", 0.9, "below_threshold")
        assert result == "critical"


class TestEscalateCase:
    @patch("repositories.audit_repository.write_log")
    @patch("repositories.case_repository.update_case_status")
    @patch("repositories.review_queue_repository.add_to_queue", return_value="Q-test123")
    @patch("services.precedent_matcher_service.find_similar_cases", return_value=[])
    def test_basic_escalation(self, mock_prec, mock_queue, mock_status, mock_audit):
        result = svc.escalate_case(
            case_id="CASE-001",
            user_id="user-001",
            reason="below_threshold",
        )
        assert result["queue_id"] == "Q-test123"
        assert result["priority"] in ("critical", "high", "medium", "low")
        assert result["escalation_reason"] == "below_threshold"
        mock_status.assert_called_once_with("CASE-001", "escalated")

    @patch("repositories.audit_repository.write_log")
    @patch("repositories.case_repository.update_case_status")
    @patch("repositories.review_queue_repository.add_to_queue", return_value="Q-test456")
    @patch("services.precedent_matcher_service.find_similar_cases", return_value=[])
    def test_escalation_with_confidence(self, mock_prec, mock_queue, mock_status, mock_audit):
        result = svc.escalate_case(
            case_id="CASE-002",
            user_id="user-002",
            confidence={"scores": {"scam": 0.9}, "primary_violation": "scam", "primary_score": 0.9},
            reason="sensitive_category",
        )
        assert result["priority"] == "critical"

    @patch("repositories.audit_repository.write_log")
    @patch("repositories.case_repository.update_case_status")
    @patch("repositories.review_queue_repository.add_to_queue", return_value="Q-test789")
    @patch("services.precedent_matcher_service.find_similar_cases", return_value=[
        {"case_id": "CASE-OLD-1"}, {"case_id": "CASE-OLD-2"},
    ])
    def test_precedent_cases_included(self, mock_prec, mock_queue, mock_status, mock_audit):
        result = svc.escalate_case(
            case_id="CASE-003",
            user_id="user-003",
            evidence={"some": "evidence"},
        )
        assert result["precedent_count"] == 2

    @patch("repositories.audit_repository.write_log")
    @patch("repositories.case_repository.update_case_status")
    @patch("repositories.review_queue_repository.add_to_queue", return_value="Q-test")
    @patch("services.precedent_matcher_service.find_similar_cases", side_effect=Exception("fail"))
    def test_precedent_failure_graceful(self, mock_prec, mock_queue, mock_status, mock_audit):
        result = svc.escalate_case(
            case_id="CASE-004",
            user_id="user-004",
            evidence={"some": "evidence"},
        )
        assert result["precedent_count"] == 0
