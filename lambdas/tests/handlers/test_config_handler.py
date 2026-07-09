import json
from unittest.mock import patch

from handlers.config_handler import lambda_handler


class TestGetCurrentConfig:

    @patch("handlers.config_handler.config_repository")
    def test_get_current_config(self, mock_repo, api_gateway_event, lambda_context):
        mock_configs = [
            {"config_key": "threshold_harassment", "value": {"autonomous_threshold": 0.90}},
            {"config_key": "threshold_spam", "value": {"autonomous_threshold": 0.85}},
        ]
        mock_repo.get_all_active_configs.return_value = mock_configs

        event = api_gateway_event(method="GET", path="/config/current")
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["configs"] == mock_configs
        mock_repo.get_all_active_configs.assert_called_once()


class TestUpdateThresholds:

    @patch("handlers.config_handler.audit_service")
    @patch("handlers.config_handler.config_repository")
    def test_update_thresholds(self, mock_repo, mock_audit, api_gateway_event, lambda_context):
        mock_repo.validate_threshold.return_value = (True, None)
        mock_repo.get_active_value.return_value = {"autonomous_threshold": 0.85}
        mock_repo.update_config.return_value = "v2"

        request_body = {
            "violation_type": "harassment",
            "autonomous_threshold": 0.90,
            "investigation_trigger_threshold": 0.60,
        }
        event = api_gateway_event(
            method="PUT",
            path="/config/thresholds",
            body=request_body,
            claims={"sub": "admin-001"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["config_key"] == "threshold_harassment"
        assert body["version_id"] == "v2"
        assert body["status"] == "updated"

        mock_repo.update_config.assert_called_once_with(
            "threshold_harassment", request_body, "admin-001"
        )
        mock_audit.log_config_change.assert_called_once_with(
            admin_id="admin-001",
            config_key="threshold_harassment",
            previous_value={"autonomous_threshold": 0.85},
            new_value=request_body,
        )

    @patch("handlers.config_handler.config_repository")
    def test_update_thresholds_missing_violation_type(self, mock_repo, api_gateway_event, lambda_context):
        event = api_gateway_event(
            method="PUT",
            path="/config/thresholds",
            body={"autonomous_threshold": 0.90},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "violation_type is required" in body["error"]

    @patch("handlers.config_handler.config_repository")
    def test_update_thresholds_invalid_threshold(self, mock_repo, api_gateway_event, lambda_context):
        mock_repo.validate_threshold.return_value = (False, "Threshold must be between 0 and 1")

        event = api_gateway_event(
            method="PUT",
            path="/config/thresholds",
            body={"violation_type": "harassment", "autonomous_threshold": 1.5},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "autonomous_threshold" in body["error"]
        assert "Threshold must be between 0 and 1" in body["error"]


class TestRollbackConfig:

    @patch("handlers.config_handler.audit_service")
    @patch("handlers.config_handler.config_repository")
    def test_rollback_config(self, mock_repo, mock_audit, api_gateway_event, lambda_context):
        mock_repo.get_active_value.return_value = {"autonomous_threshold": 0.90}
        mock_repo.rollback_config.return_value = "v3"

        event = api_gateway_event(
            method="POST",
            path="/config/rollback",
            body={"config_key": "threshold_harassment", "version_id": "v1"},
            claims={"sub": "admin-001"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["config_key"] == "threshold_harassment"
        assert body["new_version_id"] == "v3"
        assert body["rolled_back_to"] == "v1"
        assert body["status"] == "rolled_back"

        mock_repo.rollback_config.assert_called_once_with(
            "threshold_harassment", "v1", "admin-001"
        )
        mock_audit.log_config_change.assert_called_once_with(
            admin_id="admin-001",
            config_key="threshold_harassment",
            previous_value={"autonomous_threshold": 0.90},
            new_value={"rolled_back_to": "v1"},
        )

    def test_rollback_missing_fields(self, api_gateway_event, lambda_context):
        event = api_gateway_event(
            method="POST",
            path="/config/rollback",
            body={"version_id": "v1"},
        )
        result = lambda_handler(event, lambda_context)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "config_key and version_id are required" in body["error"]
