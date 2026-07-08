from unittest.mock import patch, MagicMock

from services import crisis_response_service as svc


class TestHandleCrisisDetection:
    @patch("services.crisis_response_service.case_repository")
    @patch("services.crisis_response_service.audit_repository")
    @patch("repositories.review_queue_repository.add_to_queue", return_value="Q-001")
    @patch("services.crisis_response_service.notification_service")
    def test_handle_crisis_detection_sends_resources(
        self, mock_notif, mock_queue, mock_audit, mock_case
    ):
        """When a victim is detected, wellbeing resources must be sent and audit logged."""
        mock_notif.send_wellbeing_resources.return_value = {
            "sqs_message_id": "msg-001",
            "audit_id": "notif-audit-001",
        }
        mock_audit.write_log.return_value = "audit-crisis-001"

        result = svc.handle_crisis_detection(
            case_id="CASE-CRISIS-001",
            user_id="victim-user-001",
            crisis_type="self_harm",
            is_victim=True,
        )

        # Wellbeing resources sent via notification service
        mock_notif.send_wellbeing_resources.assert_called_once_with(
            "victim-user-001", "self_harm", "en"
        )

        # Audit log written
        mock_audit.write_log.assert_called_once()
        audit_kwargs = mock_audit.write_log.call_args.kwargs
        assert audit_kwargs["event_type"] == "crisis_detected"
        assert "victim" in audit_kwargs["reasoning"].lower()

        # Result reflects that resources were sent
        assert result["wellbeing_resources_sent"] is True
        assert result["wellbeing_result"] is not None
        assert result["crisis_type"] == "self_harm"
        assert result["queue_id"] == "Q-001"

    @patch("services.crisis_response_service.case_repository")
    @patch("services.crisis_response_service.audit_repository")
    @patch("repositories.review_queue_repository.add_to_queue", return_value="Q-002")
    @patch("services.crisis_response_service.notification_service")
    def test_crisis_never_autonomously_bans(
        self, mock_notif, mock_queue, mock_audit, mock_case
    ):
        """Crisis cases for victims must block autonomous enforcement and never trigger a ban."""
        mock_notif.send_wellbeing_resources.return_value = {
            "sqs_message_id": "msg-002",
            "audit_id": "notif-audit-002",
        }
        mock_audit.write_log.return_value = "audit-crisis-002"

        result = svc.handle_crisis_detection(
            case_id="CASE-CRISIS-002",
            user_id="victim-user-002",
            crisis_type="domestic_violence",
            is_victim=True,
        )

        # Case must be set to escalated, NOT resolved or banned
        mock_case.update_case.assert_called_once()
        update_kwargs = mock_case.update_case.call_args.kwargs
        assert update_kwargs["status"] == "escalated"
        assert update_kwargs["auto_enforcement_blocked"] is True

        # Return value confirms auto enforcement is blocked
        assert result["auto_enforcement_blocked"] is True

    @patch("services.crisis_response_service.case_repository")
    @patch("services.crisis_response_service.audit_repository")
    @patch("repositories.review_queue_repository.add_to_queue", return_value="Q-003")
    @patch("services.crisis_response_service.notification_service")
    def test_crisis_escalates_to_human(
        self, mock_notif, mock_queue, mock_audit, mock_case
    ):
        """All crisis cases must be escalated to priority human review queue."""
        mock_audit.write_log.return_value = "audit-crisis-003"

        result = svc.handle_crisis_detection(
            case_id="CASE-CRISIS-003",
            user_id="user-003",
            crisis_type="sexual_assault",
            is_victim=False,
        )

        # Added to priority review queue
        mock_queue.assert_called_once()
        queue_kwargs = mock_queue.call_args.kwargs
        assert queue_kwargs["priority"] == "critical"
        assert queue_kwargs["case_id"] == "CASE-CRISIS-003"
        assert "crisis" in queue_kwargs["escalation_reason"].lower()

        # Case status is escalated
        mock_case.update_case.assert_called_once()
        assert mock_case.update_case.call_args.kwargs["status"] == "escalated"

        # Non-victim does not get wellbeing resources
        mock_notif.send_wellbeing_resources.assert_not_called()
        assert result["wellbeing_resources_sent"] is False
        assert result["wellbeing_result"] is None


class TestGetCrisisTemplate:
    def test_known_type_english(self):
        template = svc.get_crisis_template("self_harm", "en")
        assert template["title"] == "Help is available"
        assert len(template["hotlines"]) > 0

    def test_known_type_spanish(self):
        template = svc.get_crisis_template("self_harm", "es")
        assert template["title"] == "Hay ayuda disponible"

    def test_unknown_type_falls_back_to_general(self):
        template = svc.get_crisis_template("unknown_crisis_type", "en")
        assert template["title"] == "Resources available to you"

    def test_unknown_locale_falls_back_to_english(self):
        template = svc.get_crisis_template("self_harm", "fr")
        assert template["title"] == "Help is available"
