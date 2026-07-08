import logging
from datetime import datetime, timezone

from services import notification_service
from repositories import audit_repository, case_repository

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Crisis templates with localized hotline numbers
# ---------------------------------------------------------------------------

CRISIS_TEMPLATES = {
    "self_harm": {
        "en": {
            "title": "Help is available",
            "message": (
                "If you or someone you know is struggling, please reach out. "
                "You are not alone."
            ),
            "hotlines": [
                {"name": "National Suicide Prevention Lifeline", "number": "988"},
                {"name": "Crisis Text Line", "contact": "Text HOME to 741741"},
            ],
        },
        "es": {
            "title": "Hay ayuda disponible",
            "message": (
                "Si tu o alguien que conoces esta pasando por un momento dificil, "
                "por favor busca ayuda. No estas solo/a."
            ),
            "hotlines": [
                {"name": "Linea Nacional de Prevencion del Suicidio", "number": "988"},
                {"name": "Linea de Crisis por Texto", "contact": "Envia HOLA al 741741"},
            ],
        },
    },
    "domestic_violence": {
        "en": {
            "title": "Support resources",
            "message": (
                "Your safety matters. Confidential support is available 24/7."
            ),
            "hotlines": [
                {"name": "National Domestic Violence Hotline", "number": "1-800-799-7233"},
                {"name": "Crisis Text Line", "contact": "Text START to 741741"},
            ],
        },
        "es": {
            "title": "Recursos de apoyo",
            "message": (
                "Tu seguridad importa. El apoyo confidencial esta disponible las 24 horas."
            ),
            "hotlines": [
                {"name": "Linea Nacional de Violencia Domestica", "number": "1-800-799-7233"},
                {"name": "Linea de Crisis por Texto", "contact": "Envia INICIO al 741741"},
            ],
        },
    },
    "sexual_assault": {
        "en": {
            "title": "Support resources",
            "message": (
                "You deserve support. Trained staff are available to help, confidentially."
            ),
            "hotlines": [
                {"name": "RAINN National Sexual Assault Hotline", "number": "1-800-656-4673"},
                {"name": "Crisis Text Line", "contact": "Text HOME to 741741"},
            ],
        },
        "es": {
            "title": "Recursos de apoyo",
            "message": (
                "Mereces apoyo. Personal capacitado esta disponible para ayudarte de forma confidencial."
            ),
            "hotlines": [
                {"name": "RAINN Linea Nacional de Agresion Sexual", "number": "1-800-656-4673"},
                {"name": "Linea de Crisis por Texto", "contact": "Envia HOLA al 741741"},
            ],
        },
    },
    "general": {
        "en": {
            "title": "Resources available to you",
            "message": "If you need support, help is just a call or text away.",
            "hotlines": [
                {"name": "National Suicide Prevention Lifeline", "number": "988"},
                {"name": "Crisis Text Line", "contact": "Text HOME to 741741"},
                {"name": "National Domestic Violence Hotline", "number": "1-800-799-7233"},
                {"name": "RAINN (Sexual Assault)", "number": "1-800-656-4673"},
            ],
        },
        "es": {
            "title": "Recursos disponibles para ti",
            "message": "Si necesitas apoyo, la ayuda esta a solo una llamada o mensaje.",
            "hotlines": [
                {"name": "Linea Nacional de Prevencion del Suicidio", "number": "988"},
                {"name": "Linea de Crisis por Texto", "contact": "Envia HOLA al 741741"},
                {"name": "Linea Nacional de Violencia Domestica", "number": "1-800-799-7233"},
                {"name": "RAINN (Agresion Sexual)", "number": "1-800-656-4673"},
            ],
        },
    },
}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def get_crisis_template(crisis_type: str, locale: str = "en") -> dict:
    """Return a localized crisis template with hotline numbers.

    Falls back to 'general' crisis type if the specific type is not found,
    and falls back to English if the locale is not available.
    """
    type_templates = CRISIS_TEMPLATES.get(crisis_type, CRISIS_TEMPLATES["general"])
    template = type_templates.get(locale) or type_templates.get("en")
    return template


def handle_crisis_detection(
    case_id: str,
    user_id: str,
    crisis_type: str,
    is_victim: bool = False,
) -> dict:
    """Handle a detected crisis situation.

    Escalates the case to a priority review queue and sends wellbeing resources
    if the user is identified as a victim.

    IMPORTANT: This function NEVER autonomously bans victims. Victim cases are
    always routed to human review with explicit protective flags.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Update case status to escalated with crisis metadata
    case_repository.update_case(
        case_id,
        status="escalated",
        crisis_type=crisis_type,
        is_victim=is_victim,
        crisis_detected_at=now,
        # Explicitly mark that automated enforcement is blocked for victims
        auto_enforcement_blocked=is_victim,
    )

    # Add to priority review queue via the review_queue_repository
    # Import here to access the review_queue_repository directly
    from repositories import review_queue_repository

    escalation_reason = f"Crisis detected: {crisis_type}"
    if is_victim:
        escalation_reason += " (victim identified - NO automated enforcement)"

    queue_id = review_queue_repository.add_to_queue(
        case_id=case_id,
        priority="critical",
        escalation_reason=escalation_reason,
        estimated_review_minutes=2,
    )

    # Send wellbeing resources to victims
    wellbeing_result = None
    if is_victim:
        wellbeing_result = send_wellbeing_resources(user_id, crisis_type)

    # Audit the crisis detection and escalation
    audit_id = audit_repository.write_log(
        event_type="crisis_detected",
        action="escalate_to_priority_review",
        case_id=case_id,
        user_id=user_id,
        reasoning=(
            f"Crisis type={crisis_type}, is_victim={is_victim}. "
            f"Escalated to priority review queue. "
            f"{'Wellbeing resources sent.' if is_victim else 'No wellbeing resources sent (not identified as victim).'}"
        ),
    )

    # Append audit trail to the case
    case_repository.append_audit_trail_id(case_id, audit_id)

    logger.info(
        "Crisis detection handled",
        extra={
            "case_id": case_id,
            "user_id": user_id,
            "crisis_type": crisis_type,
            "is_victim": is_victim,
            "queue_id": queue_id,
            "audit_id": audit_id,
        },
    )

    return {
        "case_id": case_id,
        "queue_id": queue_id,
        "audit_id": audit_id,
        "crisis_type": crisis_type,
        "is_victim": is_victim,
        "wellbeing_resources_sent": is_victim,
        "wellbeing_result": wellbeing_result,
        "auto_enforcement_blocked": is_victim,
    }


def send_wellbeing_resources(user_id: str, crisis_type: str, locale: str = "en") -> dict:
    """Send wellbeing resources to a user by delegating to notification_service.

    Returns the notification result dict.
    """
    result = notification_service.send_wellbeing_resources(user_id, crisis_type, locale)

    logger.info(
        "Wellbeing resources delegated to notification service",
        extra={"user_id": user_id, "crisis_type": crisis_type},
    )

    return result
