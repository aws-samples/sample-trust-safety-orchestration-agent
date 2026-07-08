from unittest.mock import patch

from services import content_analysis_service as svc


class TestDetectScamPatterns:
    def test_no_scam(self):
        assert svc.detect_scam_patterns("Hello, how are you?") == []

    def test_single_pattern(self):
        results = svc.detect_scam_patterns("Please send money to my account")
        assert len(results) == 1
        assert results[0]["pattern"] == "send money"

    def test_multiple_patterns(self):
        results = svc.detect_scam_patterns("Send money via western union or gift card")
        assert len(results) == 3

    def test_case_insensitive(self):
        results = svc.detect_scam_patterns("SEND MONEY NOW")
        assert len(results) == 1


class TestDetectThreatIndicators:
    def test_no_threats(self):
        assert svc.detect_threat_indicators("You're really nice") == []

    def test_threat_detected(self):
        results = svc.detect_threat_indicators("I will find where you live")
        assert len(results) == 1
        assert results[0]["indicator"] == "find where you live"
        assert results[0]["severity"] == "high"

    def test_multiple_threats(self):
        results = svc.detect_threat_indicators("I will stalk you and get revenge")
        assert len(results) == 2


class TestDetectCrisisIndicators:
    def test_no_crisis(self):
        assert svc.detect_crisis_indicators("Having a great day") is None

    def test_crisis_detected(self):
        result = svc.detect_crisis_indicators("I want to kill myself")
        assert result is not None
        assert result["type"] == "self_harm"
        assert result["matched_pattern"] == "kill myself"

    def test_self_harm(self):
        result = svc.detect_crisis_indicators("I just want to cut myself")
        assert result is not None
        assert result["matched_pattern"] == "cut myself"


class TestAnalyzeMessages:
    @patch("services.content_analysis_service._invoke_bedrock", return_value={})
    def test_empty_messages(self, _mock):
        result = svc.analyze_messages([])
        assert result["message_count"] == 0
        assert result["has_scam_indicators"] is False

    @patch("services.content_analysis_service._invoke_bedrock", return_value={})
    def test_scam_messages(self, _mock):
        msgs = [{"content": "Send money via gift card please"}]
        result = svc.analyze_messages(msgs)
        assert result["has_scam_indicators"] is True
        assert len(result["scam_patterns"]) == 2

    @patch("services.content_analysis_service._invoke_bedrock", return_value={})
    def test_crisis_messages(self, _mock):
        msgs = [{"content": "I want to end my life"}]
        result = svc.analyze_messages(msgs)
        assert result["has_crisis_indicators"] is True
        assert result["crisis_indicators"]["type"] == "self_harm"

    @patch("services.content_analysis_service._invoke_bedrock", return_value={})
    def test_clean_messages(self, _mock):
        msgs = [{"content": "What's your favorite restaurant?"}]
        result = svc.analyze_messages(msgs)
        assert result["has_scam_indicators"] is False
        assert result["has_threat_indicators"] is False
        assert result["has_crisis_indicators"] is False
