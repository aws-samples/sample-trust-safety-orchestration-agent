"""Integration tests for the investigation pipeline.

These tests exercise the service layer in sequence (detection -> investigation ->
decision -> enforcement) with all repository/external calls mocked out.
"""

from unittest.mock import patch


from services import (
    confidence_calculator_service,
    policy_engine_service,
    enforcement_engine_service,
    crisis_response_service,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _high_confidence_scam_evidence():
    """Evidence package for a clear scam case."""
    return {
        "message_analysis": {
            "scam_patterns": [
                "crypto_investment",
                "money_transfer",
                "urgency_language",
                "external_link",
            ],
            "threat_indicators": [],
            "sentiment_summary": {"overall": "hostile", "hostility_score": 0.8},
            "has_crisis_indicators": False,
        },
        "image_analysis": {
            "ai_generated_probability": 0.0,
            "reverse_image_matches": [],
            "stock_photo_matches": [],
        },
        "bad_actor_matches": [],
        "previous_reports": [
            {"report_id": "r1"},
            {"report_id": "r2"},
        ],
    }


def _low_confidence_evidence():
    """Evidence package with weak signals that should escalate."""
    return {
        "message_analysis": {
            "scam_patterns": ["external_link"],
            "threat_indicators": [],
            "sentiment_summary": {"overall": "neutral", "hostility_score": 0.2},
            "has_crisis_indicators": False,
        },
        "image_analysis": {
            "ai_generated_probability": 0.0,
            "reverse_image_matches": [],
            "stock_photo_matches": [],
        },
        "bad_actor_matches": [],
        "previous_reports": [],
    }


def _self_harm_evidence():
    """Evidence package with self-harm indicators."""
    return {
        "message_analysis": {
            "scam_patterns": [],
            "threat_indicators": [],
            "sentiment_summary": {"overall": "distressed", "hostility_score": 0.1},
            "has_crisis_indicators": True,
        },
        "image_analysis": {
            "ai_generated_probability": 0.0,
            "reverse_image_matches": [],
            "stock_photo_matches": [],
        },
        "bad_actor_matches": [],
        "previous_reports": [],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFullPipelineAutonomousResolution:
    @patch("repositories.config_repository.get_active_value", return_value=None)
    @patch("services.enforcement_engine_service.blocklist_repository")
    @patch("services.enforcement_engine_service.case_repository")
    @patch("services.enforcement_engine_service.appeal_repository")
    @patch("services.enforcement_engine_service._queue_notification")
    @patch("services.enforcement_engine_service._call_platform_enforcement")
    @patch("services.enforcement_engine_service.audit_repository")
    def test_full_pipeline_autonomous_resolution(
        self,
        mock_enf_audit,
        mock_platform,
        mock_notify,
        mock_appeal,
        mock_case,
        mock_blocklist,
        _mock_config,
    ):
        """High-confidence scam: evidence -> confidence -> policy (autonomous) -> enforcement."""
        mock_enf_audit.write_log.return_value = "audit-auto-001"
        mock_platform.return_value = {"status": "ok"}
        mock_appeal.create_enforcement_appeal_record.return_value = "appeal-auto-001"

        evidence = _high_confidence_scam_evidence()

        # Step 1: Calculate confidence scores
        scores = confidence_calculator_service.calculate_confidence_scores(evidence)
        assert "scam" in scores
        assert scores["scam"] >= 0.75  # should be high enough for autonomous action

        # Step 2: Route decision via policy engine
        routing = policy_engine_service.route_decision(scores)
        assert routing["decision"] == "autonomous"
        assert routing["action"] is not None
        action = routing["action"]

        # Step 3: Execute enforcement
        primary_type, primary_score = confidence_calculator_service.get_primary_violation(scores)
        result = enforcement_engine_service.execute_action(
            case_id="CASE-PIPE-001",
            user_id="scammer-001",
            action=action,
            violation_type=primary_type,
            confidence_score=primary_score,
            is_autonomous=True,
        )

        assert result["action_status"] == "completed"
        assert result["action"] == action
        mock_platform.assert_called_once()
        mock_case.update_case.assert_called_once()


class TestFullPipelineEscalation:
    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_full_pipeline_escalation(self, _mock_config):
        """Low-confidence case: evidence -> confidence -> policy routes to escalation."""
        evidence = _low_confidence_evidence()

        # Step 1: Calculate confidence scores
        scores = confidence_calculator_service.calculate_confidence_scores(evidence)
        assert "scam" in scores

        # Step 2: Route decision via policy engine
        routing = policy_engine_service.route_decision(scores)

        # With only one weak scam pattern, confidence should be below thresholds
        assert routing["decision"] == "escalate"
        assert routing["action"] is None
        assert routing["escalation_reason"] in ("below_threshold", "no_matching_action")


class TestSensitiveCategoryAlwaysEscalates:
    @patch("repositories.config_repository.get_active_value", return_value=None)
    def test_sensitive_category_always_escalates(self, _mock_config):
        """Self-harm must always escalate to human review, regardless of confidence."""
        evidence = _self_harm_evidence()

        scores = confidence_calculator_service.calculate_confidence_scores(evidence)
        # self_harm score is set to 0.95 when crisis indicators present
        assert "self_harm" in scores
        assert scores["self_harm"] == 0.95

        # Even with 0.95 confidence, self_harm is a sensitive category -> escalate
        routing = policy_engine_service.route_decision(scores, has_sensitive_category=True)
        assert routing["decision"] == "escalate"
        assert routing["escalation_reason"] == "sensitive_category"

        # Also test without the flag -- self_harm type alone triggers escalation
        routing2 = policy_engine_service.route_decision(scores, has_sensitive_category=False)
        assert routing2["decision"] == "escalate"
        assert routing2["escalation_reason"] == "sensitive_category"


class TestCrisisDetectionTriggersResources:
    @patch("repositories.config_repository.get_active_value", return_value=None)
    @patch("services.crisis_response_service.case_repository")
    @patch("services.crisis_response_service.audit_repository")
    @patch("repositories.review_queue_repository.add_to_queue", return_value="Q-INT-001")
    @patch("services.crisis_response_service.notification_service")
    def test_crisis_detection_triggers_resources(
        self, mock_notif, mock_queue, mock_audit, mock_case, _mock_config
    ):
        """When crisis indicators are detected, the full pipeline sends wellbeing resources."""
        mock_notif.send_wellbeing_resources.return_value = {
            "sqs_message_id": "msg-int-001",
            "audit_id": "notif-audit-int-001",
        }
        mock_audit.write_log.return_value = "audit-int-crisis-001"

        evidence = _self_harm_evidence()

        # Step 1: Confidence calculation detects crisis
        scores = confidence_calculator_service.calculate_confidence_scores(evidence)
        assert "self_harm" in scores

        # Step 2: Determine this is a crisis and call crisis response
        has_crisis = evidence["message_analysis"].get("has_crisis_indicators", False)
        assert has_crisis is True

        result = crisis_response_service.handle_crisis_detection(
            case_id="CASE-CRISIS-INT-001",
            user_id="victim-int-001",
            crisis_type="self_harm",
            is_victim=True,
        )

        # Crisis resources sent
        mock_notif.send_wellbeing_resources.assert_called_once_with(
            "victim-int-001", "self_harm", "en"
        )

        # Case escalated to priority review
        mock_queue.assert_called_once()
        assert mock_queue.call_args.kwargs["priority"] == "critical"

        # Result confirms the full crisis workflow ran
        assert result["wellbeing_resources_sent"] is True
        assert result["auto_enforcement_blocked"] is True
        assert result["queue_id"] == "Q-INT-001"
