from unittest.mock import patch, MagicMock

import pytest

from services import enforcement_engine_service as svc


class TestExecuteAction:
    @patch("services.enforcement_engine_service.case_repository")
    @patch("services.enforcement_engine_service.appeal_repository")
    @patch("services.enforcement_engine_service._queue_notification")
    @patch("services.enforcement_engine_service._call_platform_enforcement")
    @patch("services.enforcement_engine_service.audit_repository")
    def test_execute_action_basic(
        self, mock_audit, mock_platform, mock_notify, mock_appeal, mock_case
    ):
        """Verify all steps called in the correct order for a basic enforcement."""
        mock_audit.write_log.return_value = "audit-001"
        mock_platform.return_value = {"status": "ok"}
        mock_appeal.create_enforcement_appeal_record.return_value = "appeal-001"

        result = svc.execute_action(
            case_id="CASE-001",
            user_id="user-123",
            action="warning",
            violation_type="harassment",
            confidence_score=0.80,
        )

        # 1. Audit log written first
        mock_audit.write_log.assert_called_once()
        audit_kwargs = mock_audit.write_log.call_args
        assert audit_kwargs.kwargs["event_type"] == "enforcement"
        assert audit_kwargs.kwargs["action"] == "warning"

        # 2. Platform enforcement API called
        mock_platform.assert_called_once_with("user-123", "warning", {})

        # 3. Appeal record created
        mock_appeal.create_enforcement_appeal_record.assert_called_once_with(
            case_id="CASE-001",
            user_id="user-123",
            enforcement_action="warning",
        )

        # 4. Notification queued
        mock_notify.assert_called_once()

        # 5. Case updated to resolved
        mock_case.update_case.assert_called_once()
        update_kwargs = mock_case.update_case.call_args
        assert update_kwargs.kwargs["status"] == "resolved"
        assert update_kwargs.kwargs["enforcement_action"] == "warning"

        # 6. Audit trail appended to case
        mock_case.append_audit_trail_id.assert_called_once_with("CASE-001", "audit-001")

        # Verify return value shape
        assert result["case_id"] == "CASE-001"
        assert result["action"] == "warning"
        assert result["action_status"] == "completed"
        assert result["audit_trail_id"] == "audit-001"
        assert result["appeal_id"] == "appeal-001"
        assert result["user_notified"] is True
        assert "response_time_ms" in result

    @patch("services.enforcement_engine_service.case_repository")
    @patch("services.enforcement_engine_service.appeal_repository")
    @patch("services.enforcement_engine_service._queue_notification")
    @patch("services.enforcement_engine_service._call_platform_enforcement")
    @patch("services.enforcement_engine_service.audit_repository")
    @patch("services.enforcement_engine_service.blocklist_repository")
    def test_execute_action_permanent_ban_updates_blocklist(
        self, mock_blocklist, mock_audit, mock_platform, mock_notify, mock_appeal, mock_case
    ):
        """permanent_ban action must add the user to the blocklist."""
        mock_audit.write_log.return_value = "audit-002"
        mock_platform.return_value = {"status": "ok"}
        mock_appeal.create_enforcement_appeal_record.return_value = "appeal-002"

        svc.execute_action(
            case_id="CASE-002",
            user_id="user-456",
            action="permanent_ban",
            violation_type="scam",
            confidence_score=0.95,
        )

        mock_blocklist.add_bad_actor.assert_called_once()
        bl_kwargs = mock_blocklist.add_bad_actor.call_args
        assert bl_kwargs.kwargs["source_platform"] == "platform"
        assert bl_kwargs.kwargs["ban_reason"] == "scam"
        # fingerprint_hash and signature_hash should be sha256 hex strings
        assert len(bl_kwargs.kwargs["fingerprint_hash"]) == 64
        assert len(bl_kwargs.kwargs["signature_hash"]) == 64

    @patch("services.enforcement_engine_service.case_repository")
    @patch("services.enforcement_engine_service.appeal_repository")
    @patch("services.enforcement_engine_service._queue_notification")
    @patch("services.enforcement_engine_service._call_platform_enforcement")
    @patch("services.enforcement_engine_service.audit_repository")
    def test_execute_action_creates_appeal_record(
        self, mock_audit, mock_platform, mock_notify, mock_appeal, mock_case
    ):
        """Every enforcement action must create an appeal record."""
        mock_audit.write_log.return_value = "audit-003"
        mock_platform.return_value = {"status": "ok"}
        mock_appeal.create_enforcement_appeal_record.return_value = "appeal-003"

        result = svc.execute_action(
            case_id="CASE-003",
            user_id="user-789",
            action="temporary_suspension",
            violation_type="fake_profile",
            confidence_score=0.85,
            duration_hours=48,
        )

        mock_appeal.create_enforcement_appeal_record.assert_called_once_with(
            case_id="CASE-003",
            user_id="user-789",
            enforcement_action="temporary_suspension",
        )
        assert result["appeal_id"] == "appeal-003"

    def test_execute_action_invalid_action_raises(self):
        """Invalid action type must raise ValueError."""
        with pytest.raises(ValueError, match="Invalid enforcement action"):
            svc.execute_action(
                case_id="CASE-X",
                user_id="user-X",
                action="delete_account",
                violation_type="scam",
                confidence_score=0.9,
            )


class TestExecuteBulkAction:
    @patch("services.enforcement_engine_service.case_repository")
    @patch("services.enforcement_engine_service._call_platform_enforcement")
    @patch("services.enforcement_engine_service.audit_repository")
    def test_execute_bulk_action(self, mock_audit, mock_platform, mock_case):
        """Bulk action calls enforcement API for each user."""
        mock_audit.write_log.return_value = "audit-bulk-001"
        mock_platform.return_value = {"status": "ok"}

        user_ids = [f"user-{i}" for i in range(5)]
        result = svc.execute_bulk_action(
            case_id="CASE-BULK-001",
            user_ids=user_ids,
            action="temporary_suspension",
            violation_type="bot_farm",
            attack_pattern="credential_stuffing",
        )

        assert mock_platform.call_count == 5
        assert result["total_users"] == 5
        assert result["succeeded"] == 5
        assert result["failed"] == 0
        assert result["failed_user_ids"] == []
        assert result["audit_trail_id"] == "audit-bulk-001"

    @patch("services.enforcement_engine_service.case_repository")
    @patch("services.enforcement_engine_service._call_platform_enforcement")
    @patch("services.enforcement_engine_service.audit_repository")
    def test_execute_bulk_max_500(self, mock_audit, mock_platform, mock_case):
        """Bulk action must handle exactly 500 users and reject >500."""
        mock_audit.write_log.return_value = "audit-bulk-002"
        mock_platform.return_value = {"status": "ok"}

        # Exactly 500 should succeed
        user_ids_500 = [f"user-{i}" for i in range(500)]
        result = svc.execute_bulk_action(
            case_id="CASE-BULK-002",
            user_ids=user_ids_500,
            action="warning",
            violation_type="scam",
        )
        assert result["total_users"] == 500
        assert result["succeeded"] == 500
        assert mock_platform.call_count == 500

        # 501 should raise
        user_ids_501 = [f"user-{i}" for i in range(501)]
        with pytest.raises(ValueError, match="Bulk action limited to 500 users"):
            svc.execute_bulk_action(
                case_id="CASE-BULK-003",
                user_ids=user_ids_501,
                action="warning",
                violation_type="scam",
            )


class TestPlatformApiCallFormat:
    @patch("urllib.request.urlopen")
    @patch("services.enforcement_engine_service.PLATFORM_USER_API_URL", "https://api.platform.test/v1")
    def test_platform_api_call_format(self, mock_urlopen):
        """Verify the HTTP request payload and headers sent to the Platform API."""
        import json

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"status": "ok"}).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        svc._call_platform_enforcement("user-abc", "temporary_suspension", {"duration_hours": 24})

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]

        # URL should target the user
        assert req.full_url == "https://api.platform.test/v1/user-abc/enforce"

        # Headers
        assert req.get_header("Content-type") == "application/json"

        # Payload
        payload = json.loads(req.data.decode())
        assert payload["action"] == "temporary_suspension"
        assert payload["duration_hours"] == 24
