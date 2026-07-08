import json
import logging
import os
from datetime import datetime, timezone

import boto3
from functools import lru_cache

from repositories import audit_repository

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Notification templates
# ---------------------------------------------------------------------------

TEMPLATES = {
    "enforcement": {
        "en": {
            "subject": "Action taken on your account",
            "body": (
                "We reviewed your activity and found a violation of our community guidelines "
                "related to {violation_type}.\n\n"
                "Action taken: {action}\n\n"
                "We take the safety of our community seriously. If you believe this was a "
                "mistake, you can submit an appeal within 30 days by going to "
                "Settings > Account > Appeal a Decision.\n\n"
                "Reference ID: {enforcement_id}"
            ),
        },
        "es": {
            "subject": "Accion tomada en tu cuenta",
            "body": (
                "Revisamos tu actividad y encontramos una violacion de nuestras normas "
                "comunitarias relacionada con {violation_type}.\n\n"
                "Accion tomada: {action}\n\n"
                "Nos tomamos muy en serio la seguridad de nuestra comunidad. Si crees que "
                "esto fue un error, puedes enviar una apelacion dentro de los 30 dias "
                "yendo a Configuracion > Cuenta > Apelar una Decision.\n\n"
                "ID de referencia: {enforcement_id}"
            ),
        },
    },
    "appeal_acknowledgment": {
        "en": {
            "subject": "We received your appeal",
            "body": (
                "Thank you for submitting your appeal (ID: {appeal_id}). We understand "
                "this is important to you.\n\n"
                "A member of our Trust & Safety team will review your case. You can "
                "expect a response within {expected_review_time}.\n\n"
                "We will notify you as soon as a decision has been made."
            ),
        },
        "es": {
            "subject": "Recibimos tu apelacion",
            "body": (
                "Gracias por enviar tu apelacion (ID: {appeal_id}). Entendemos que "
                "esto es importante para ti.\n\n"
                "Un miembro de nuestro equipo de Confianza y Seguridad revisara tu caso. "
                "Puedes esperar una respuesta dentro de {expected_review_time}.\n\n"
                "Te notificaremos tan pronto como se haya tomado una decision."
            ),
        },
    },
    "crisis_resources": {
        "en": {
            "subject": "Resources available to you",
            "body": (
                "We care about your wellbeing. If you or someone you know is in crisis, "
                "please reach out to one of these resources:\n\n"
                "- National Suicide Prevention Lifeline: 988 (call or text)\n"
                "- Crisis Text Line: Text HOME to 741741\n"
                "- National Domestic Violence Hotline: 1-800-799-7233\n"
                "- RAINN (Sexual Assault): 1-800-656-4673\n\n"
                "You are not alone. Help is available 24/7.\n\n"
                "Crisis type: {crisis_type}"
            ),
        },
        "es": {
            "subject": "Recursos disponibles para ti",
            "body": (
                "Nos importa tu bienestar. Si tu o alguien que conoces esta en crisis, "
                "comunicate con uno de estos recursos:\n\n"
                "- Linea Nacional de Prevencion del Suicidio: 988 (llamar o enviar mensaje)\n"
                "- Linea de Crisis por Texto: Envia HOLA al 741741\n"
                "- Linea Nacional de Violencia Domestica: 1-800-799-7233\n"
                "- RAINN (Agresion Sexual): 1-800-656-4673\n\n"
                "No estas solo/a. La ayuda esta disponible las 24 horas.\n\n"
                "Tipo de crisis: {crisis_type}"
            ),
        },
    },
}


# ---------------------------------------------------------------------------
# SQS helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_sqs_client():
    return boto3.client("sqs")


def _get_queue_url() -> str:
    return os.environ["NOTIFICATION_QUEUE_URL"]


def _send_to_queue(message: dict) -> str:
    """Send a notification message to the SQS queue. Returns the SQS message ID."""
    resp = _get_sqs_client().send_message(
        QueueUrl=_get_queue_url(),
        MessageBody=json.dumps(message, default=str),
        MessageGroupId=message.get("user_id", "default"),
    )
    return resp["MessageId"]


# ---------------------------------------------------------------------------
# Template retrieval
# ---------------------------------------------------------------------------

def get_notification_template(
    notification_type: str,
    violation_type: str | None = None,
    action: str | None = None,
    locale: str = "en",
) -> dict:
    """Return a template dict with 'subject' and 'body' for the given notification type.

    Falls back to English if the requested locale is not available.
    """
    type_templates = TEMPLATES.get(notification_type, {})
    template = type_templates.get(locale) or type_templates.get("en")
    if template is None:
        logger.warning(
            "No template found",
            extra={"notification_type": notification_type, "locale": locale},
        )
        return {"subject": "Notification", "body": ""}

    return {
        "subject": template["subject"],
        "body": template["body"],
    }


# ---------------------------------------------------------------------------
# Public notification functions
# ---------------------------------------------------------------------------

def send_enforcement_notification(
    user_id: str,
    enforcement_id: str,
    violation_type: str,
    action: str,
    locale: str = "en",
) -> dict:
    """Queue both in-app and email notifications for an enforcement action.

    Returns a dict with the SQS message IDs and audit log ID.
    """
    template = get_notification_template("enforcement", violation_type, action, locale)
    formatted_body = template["body"].format(
        violation_type=violation_type,
        action=action,
        enforcement_id=enforcement_id,
    )

    base_payload = {
        "user_id": user_id,
        "notification_type": "enforcement",
        "enforcement_id": enforcement_id,
        "violation_type": violation_type,
        "action": action,
        "subject": template["subject"],
        "body": formatted_body,
        "locale": locale,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }

    # Queue in-app notification
    in_app_msg = {**base_payload, "channel": "in_app"}
    in_app_id = _send_to_queue(in_app_msg)

    # Queue email notification
    email_msg = {**base_payload, "channel": "email"}
    email_id = _send_to_queue(email_msg)

    # Audit log
    audit_id = audit_repository.write_log(
        event_type="notification_sent",
        action="enforcement_notification",
        user_id=user_id,
        violation_type=violation_type,
        reasoning=f"Enforcement notification sent for action={action}, enforcement_id={enforcement_id}",
    )

    logger.info(
        "Enforcement notification sent",
        extra={
            "user_id": user_id,
            "enforcement_id": enforcement_id,
            "in_app_message_id": in_app_id,
            "email_message_id": email_id,
        },
    )

    return {
        "in_app_message_id": in_app_id,
        "email_message_id": email_id,
        "audit_id": audit_id,
    }


def send_appeal_acknowledgment(
    user_id: str,
    appeal_id: str,
    expected_review_time: str = "24-48 hours",
) -> dict:
    """Send an appeal acknowledgment notification to the user.

    Returns a dict with the SQS message ID and audit log ID.
    """
    template = get_notification_template("appeal_acknowledgment")
    formatted_body = template["body"].format(
        appeal_id=appeal_id,
        expected_review_time=expected_review_time,
    )

    payload = {
        "user_id": user_id,
        "notification_type": "appeal_acknowledgment",
        "appeal_id": appeal_id,
        "channel": "in_app",
        "subject": template["subject"],
        "body": formatted_body,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }

    sqs_id = _send_to_queue(payload)

    audit_id = audit_repository.write_log(
        event_type="notification_sent",
        action="appeal_acknowledgment",
        user_id=user_id,
        reasoning=f"Appeal acknowledgment sent for appeal_id={appeal_id}",
    )

    logger.info(
        "Appeal acknowledgment sent",
        extra={"user_id": user_id, "appeal_id": appeal_id, "sqs_message_id": sqs_id},
    )

    return {
        "sqs_message_id": sqs_id,
        "audit_id": audit_id,
    }


def send_wellbeing_resources(
    user_id: str,
    crisis_type: str,
    locale: str = "en",
) -> dict:
    """Send wellbeing and crisis resources to a user.

    Returns a dict with the SQS message ID and audit log ID.
    """
    template = get_notification_template("crisis_resources", locale=locale)
    formatted_body = template["body"].format(crisis_type=crisis_type)

    payload = {
        "user_id": user_id,
        "notification_type": "crisis_resources",
        "crisis_type": crisis_type,
        "channel": "in_app",
        "subject": template["subject"],
        "body": formatted_body,
        "locale": locale,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }

    sqs_id = _send_to_queue(payload)

    audit_id = audit_repository.write_log(
        event_type="notification_sent",
        action="wellbeing_resources",
        user_id=user_id,
        reasoning=f"Wellbeing resources sent for crisis_type={crisis_type}",
    )

    logger.info(
        "Wellbeing resources sent",
        extra={"user_id": user_id, "crisis_type": crisis_type, "sqs_message_id": sqs_id},
    )

    return {
        "sqs_message_id": sqs_id,
        "audit_id": audit_id,
    }
