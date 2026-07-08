import copy
import logging
import re

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Severity keyword patterns
# ---------------------------------------------------------------------------

SEVERITY_KEYWORDS: dict[str, list[str]] = {
    "critical": [
        "kill",
        "murder",
        "bomb",
        "shoot",
        "attack",
        "execute",
        "terror",
        "mass shooting",
        "death threat",
        "i will find you",
        "end your life",
        "child abuse",
        "csam",
        "trafficking",
    ],
    "high": [
        "threaten",
        "stalk",
        "assault",
        "rape",
        "hurt you",
        "beat you",
        "destroy you",
        "doxx",
        "revenge porn",
        "self-harm",
        "suicide",
        "cutting",
        "overdose",
        "blackmail",
        "extortion",
    ],
    "medium": [
        "harass",
        "bully",
        "intimidate",
        "slur",
        "hate speech",
        "discriminat",
        "racist",
        "sexist",
        "homophob",
        "transphob",
        "xenophob",
        "derogatory",
        "dehumaniz",
        "impersonat",
        "catfish",
        "scam",
        "fraud",
    ],
    "low": [
        "spam",
        "unsolicited",
        "inappropriate",
        "offensive",
        "rude",
        "disrespect",
        "vulgar",
        "profanity",
        "troll",
        "misleading",
    ],
}

# Pre-compile patterns for each severity level for efficient matching
_SEVERITY_PATTERNS: dict[str, re.Pattern] = {
    level: re.compile("|".join(re.escape(kw) for kw in keywords), re.IGNORECASE)
    for level, keywords in SEVERITY_KEYWORDS.items()
}

# Ordered from most to least severe for classification
_SEVERITY_ORDER = ["critical", "high", "medium", "low"]


# ---------------------------------------------------------------------------
# Content classification
# ---------------------------------------------------------------------------

def classify_content_severity(content: str) -> str:
    """Classify content into a severity level based on keyword pattern matching.

    Returns one of: 'critical', 'high', 'medium', 'low'.
    If no keywords match, defaults to 'low'.
    """
    if not content:
        return "low"

    for severity in _SEVERITY_ORDER:
        pattern = _SEVERITY_PATTERNS[severity]
        if pattern.search(content):
            logger.info(
                "Content classified",
                extra={"severity": severity, "content_length": len(content)},
            )
            return severity

    logger.info(
        "Content classified as low (no keyword matches)",
        extra={"content_length": len(content)},
    )
    return "low"


# ---------------------------------------------------------------------------
# Evidence sanitization
# ---------------------------------------------------------------------------

def _sanitize_labels_only(evidence_package: dict) -> dict:
    """Replace message content with classification labels."""
    sanitized = copy.deepcopy(evidence_package)

    messages = sanitized.get("messages", [])
    for message in messages:
        content = message.get("content", "")
        if content:
            severity = classify_content_severity(content)
            message["content"] = f"[CONTENT REDACTED - Severity: {severity}]"
            message["original_length"] = len(content)
            message["content_severity"] = severity

    # Handle any top-level content field
    if "content" in sanitized and isinstance(sanitized["content"], str):
        content = sanitized["content"]
        severity = classify_content_severity(content)
        sanitized["content"] = f"[CONTENT REDACTED - Severity: {severity}]"
        sanitized["content_severity"] = severity

    # Handle attached media descriptions
    media_items = sanitized.get("media", [])
    for item in media_items:
        if "description" in item:
            severity = classify_content_severity(item["description"])
            item["description"] = f"[DESCRIPTION REDACTED - Severity: {severity}]"
            item["content_severity"] = severity

    sanitized["sanitization_mode"] = "labels_only"
    return sanitized


def _sanitize_blurred(evidence_package: dict) -> dict:
    """Add blur markers to content, indicating it should be rendered with visual blurring."""
    sanitized = copy.deepcopy(evidence_package)

    messages = sanitized.get("messages", [])
    for message in messages:
        content = message.get("content", "")
        if content:
            severity = classify_content_severity(content)
            message["blur"] = True
            message["content_severity"] = severity
            if severity in ("high", "critical"):
                message["blur_intensity"] = "heavy"
            else:
                message["blur_intensity"] = "light"

    media_items = sanitized.get("media", [])
    for item in media_items:
        item["blur"] = True
        description = item.get("description", "")
        if description:
            severity = classify_content_severity(description)
            item["content_severity"] = severity
            item["blur_intensity"] = "heavy" if severity in ("high", "critical") else "light"

    sanitized["sanitization_mode"] = "blurred"
    return sanitized


def _sanitize_full(evidence_package: dict) -> dict:
    """Return the evidence package as-is (full access mode)."""
    sanitized = copy.deepcopy(evidence_package)
    sanitized["sanitization_mode"] = "full"
    return sanitized


_SANITIZERS = {
    "labels_only": _sanitize_labels_only,
    "blurred": _sanitize_blurred,
    "full": _sanitize_full,
}


def sanitize_evidence_package(
    evidence_package: dict,
    reviewer_preference: str = "labels_only",
) -> dict:
    """Return a sanitized copy of the evidence package based on the reviewer's preference.

    Supported preferences:
    - 'labels_only': Replace message content with classification labels (default).
    - 'blurred': Add blur markers to content for visual blurring.
    - 'full': Return content as-is with no sanitization.
    """
    sanitizer = _SANITIZERS.get(reviewer_preference, _sanitize_labels_only)

    sanitized = sanitizer(evidence_package)

    logger.info(
        "Evidence package sanitized",
        extra={
            "mode": reviewer_preference,
            "message_count": len(evidence_package.get("messages", [])),
            "media_count": len(evidence_package.get("media", [])),
        },
    )

    return sanitized
