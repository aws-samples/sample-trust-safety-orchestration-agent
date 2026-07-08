from unittest.mock import patch

from services import policy_engine_service as svc


@patch("repositories.config_repository.get_active_value", return_value=None)
class TestShouldEscalateToHuman:
    def test_sensitive_category_always_escalates(self, _mock):
        assert svc.should_escalate_to_human("self_harm", 0.99) is True
        assert svc.should_escalate_to_human("child_safety", 0.99) is True
        assert svc.should_escalate_to_human("illegal_activity", 0.99) is True

    def test_has_sensitive_flag_escalates(self, _mock):
        assert svc.should_escalate_to_human("scam", 0.99, has_sensitive_category=True) is True

    def test_high_confidence_scam_no_escalate(self, _mock):
        assert svc.should_escalate_to_human("scam", 0.95) is False

    def test_low_confidence_scam_escalates(self, _mock):
        assert svc.should_escalate_to_human("scam", 0.5) is True

    def test_borderline_harassment(self, _mock):
        assert svc.should_escalate_to_human("harassment", 0.75) is False
        assert svc.should_escalate_to_human("harassment", 0.74) is True


@patch("repositories.config_repository.get_active_value", return_value=None)
class TestGetEnforcementAction:
    def test_sensitive_returns_escalate(self, _mock):
        assert svc.get_enforcement_action("self_harm", 0.99) == "escalate"
        assert svc.get_enforcement_action("child_safety", 1.0) == "escalate"

    def test_high_confidence_scam_permanent_ban(self, _mock):
        assert svc.get_enforcement_action("scam", 0.95) == "permanent_ban"

    def test_moderate_confidence_temp_suspension(self, _mock):
        assert svc.get_enforcement_action("scam", 0.80) == "temporary_suspension"

    def test_repeat_offender_lower_threshold(self, _mock):
        action = svc.get_enforcement_action("scam", 0.82, is_repeat_offender=True)
        assert action == "permanent_ban"

    def test_bot_farm_permanent_ban(self, _mock):
        assert svc.get_enforcement_action("bot_farm", 0.90) == "permanent_ban"

    def test_below_all_thresholds_escalates(self, _mock):
        assert svc.get_enforcement_action("scam", 0.3) == "escalate"


@patch("repositories.config_repository.get_active_value", return_value=None)
class TestRouteDecision:
    def test_no_scores_escalates(self, _mock):
        result = svc.route_decision({})
        assert result["decision"] == "escalate"
        assert result["escalation_reason"] == "no_confidence_scores"

    def test_high_confidence_autonomous(self, _mock):
        result = svc.route_decision({"scam": 0.95})
        assert result["decision"] == "autonomous"
        assert result["action"] == "permanent_ban"
        assert result["primary_violation"] == "scam"

    def test_sensitive_escalates(self, _mock):
        result = svc.route_decision({"self_harm": 0.95})
        assert result["decision"] == "escalate"
        assert result["escalation_reason"] == "sensitive_category"

    def test_low_confidence_escalates(self, _mock):
        result = svc.route_decision({"scam": 0.3})
        assert result["decision"] == "escalate"
        assert result["escalation_reason"] == "below_threshold"

    def test_sensitive_flag_override(self, _mock):
        result = svc.route_decision({"scam": 0.99}, has_sensitive_category=True)
        assert result["decision"] == "escalate"
        assert result["escalation_reason"] == "sensitive_category"

    def test_moderate_confidence_routes_to_temp_suspension(self, _mock):
        result = svc.route_decision({"harassment": 0.80})
        assert result["decision"] == "autonomous"
        assert result["action"] == "temporary_suspension"
