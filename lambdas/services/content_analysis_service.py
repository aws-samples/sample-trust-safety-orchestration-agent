import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)

BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

SCAM_PATTERNS = [
    "send money", "wire transfer", "western union", "gift card",
    "cryptocurrency", "bitcoin", "investment opportunity", "guaranteed return",
    "verify your account", "click this link", "whatsapp", "telegram",
    "cashapp", "venmo me", "bank account", "social security",
]

THREAT_KEYWORDS = [
    "kill", "hurt", "attack", "stalk", "find where you live",
    "come to your house", "follow you", "watch you", "revenge",
    "regret", "pay for this", "destroy",
]

CRISIS_KEYWORDS = [
    "kill myself", "end my life", "suicide", "want to die",
    "no reason to live", "better off dead", "self harm", "cut myself",
    "overdose", "jump off",
]


def _invoke_bedrock(prompt: str) -> dict:
    client = boto3.client("bedrock-runtime")
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    })
    try:
        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=body,
            contentType="application/json",
        )
        result = json.loads(response["body"].read())
        return result
    except Exception as e:
        logger.error("Bedrock invocation failed", extra={"error": str(e)})
        return {}


def detect_scam_patterns(content: str) -> list[dict]:
    content_lower = content.lower()
    matches = []
    for pattern in SCAM_PATTERNS:
        if pattern in content_lower:
            matches.append({"pattern": pattern, "confidence": 0.8})
    return matches


def detect_threat_indicators(content: str) -> list[dict]:
    content_lower = content.lower()
    indicators = []
    for keyword in THREAT_KEYWORDS:
        if keyword in content_lower:
            indicators.append({"indicator": keyword, "severity": "high"})
    return indicators


def detect_crisis_indicators(content: str) -> dict | None:
    content_lower = content.lower()
    for keyword in CRISIS_KEYWORDS:
        if keyword in content_lower:
            return {"type": "self_harm", "matched_pattern": keyword, "confidence": 0.9}
    return None


def analyze_messages(messages: list[dict]) -> dict:
    all_content = " ".join(m.get("content", "") for m in messages if m.get("content"))

    scam_patterns = detect_scam_patterns(all_content)
    threat_indicators = detect_threat_indicators(all_content)
    crisis_indicators = detect_crisis_indicators(all_content)

    sentiment = _analyze_sentiment_batch(messages)

    return {
        "message_count": len(messages),
        "sentiment_summary": sentiment,
        "scam_patterns": scam_patterns,
        "threat_indicators": threat_indicators,
        "crisis_indicators": crisis_indicators,
        "has_scam_indicators": len(scam_patterns) > 0,
        "has_threat_indicators": len(threat_indicators) > 0,
        "has_crisis_indicators": crisis_indicators is not None,
    }


def _analyze_sentiment_batch(messages: list[dict]) -> dict:
    if not messages:
        return {"overall": "neutral", "negative_ratio": 0.0}

    sample = messages[:50]
    content_sample = "\n".join(
        m.get("content", "")[:200] for m in sample if m.get("content")
    )

    if not content_sample.strip():
        return {"overall": "neutral", "negative_ratio": 0.0}

    prompt = (
        "Analyze the sentiment of these messages from a dating app user. "
        "Respond ONLY with a JSON object: "
        '{"overall": "positive|neutral|negative|hostile", "negative_ratio": 0.0-1.0, '
        '"hostility_score": 0.0-1.0}\n\n'
        f"Messages:\n{content_sample}"
    )

    result = _invoke_bedrock(prompt)
    if not result:
        return {"overall": "neutral", "negative_ratio": 0.0}

    try:
        text = result.get("content", [{}])[0].get("text", "{}")
        return json.loads(text)
    except (json.JSONDecodeError, IndexError, KeyError):
        return {"overall": "neutral", "negative_ratio": 0.0}
