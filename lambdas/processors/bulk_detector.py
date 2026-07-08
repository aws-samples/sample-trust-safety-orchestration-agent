import json
import logging
import os
from datetime import datetime, timezone, timedelta

import boto3

from repositories import case_repository, audit_repository, metrics_repository

logger = logging.getLogger(__name__)

BULK_ACTION_STATE_MACHINE_ARN = os.environ.get("BULK_ACTION_STATE_MACHINE_ARN", "")
PROFILES_PER_HOUR_THRESHOLD = 50


def lambda_handler(event, context):
    logger.info("Bulk detector invoked")

    now = datetime.now(timezone.utc)
    one_hour_ago = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:00Z")
    now_str = now.strftime("%Y-%m-%dT%H:%M:00Z")

    recent_metrics = metrics_repository.get_metric_values(
        metric_name="profile_creations",
        start_time=one_hour_ago,
        end_time=now_str,
    )

    ip_rates = _aggregate_by_ip_range(recent_metrics)

    for ip_range, count in ip_rates.items():
        if count > PROFILES_PER_HOUR_THRESHOLD:
            logger.warning(
                "Bulk profile creation detected",
                extra={"ip_range": ip_range, "count": count},
            )

            case = case_repository.create_case(
                user_id=f"bulk-{ip_range}",
                trigger_source="bulk_detection",
                violation_type="bot_farm",
            )

            _start_bulk_action(case["case_id"], ip_range, count)

            audit_repository.write_log(
                event_type="bulk_detection",
                action="bulk_action_triggered",
                case_id=case["case_id"],
                reasoning=f"IP range {ip_range} created {count} profiles in the last hour (threshold: {PROFILES_PER_HOUR_THRESHOLD})",
            )

    metrics_repository.record_metric("bulk_detection_runs", 1)

    return None


def _aggregate_by_ip_range(metric_items):
    ip_rates = {}
    for item in metric_items:
        dimensions = item.get("dimensions", {})
        ip_range = dimensions.get("ip_range")
        if ip_range:
            ip_rates[ip_range] = ip_rates.get(ip_range, 0) + float(item.get("value", 0))
    return ip_rates


def _start_bulk_action(case_id, ip_range, count):
    if not BULK_ACTION_STATE_MACHINE_ARN:
        logger.warning("Bulk action state machine ARN not configured")
        return

    sfn = boto3.client("stepfunctions")
    sfn.start_execution(
        stateMachineArn=BULK_ACTION_STATE_MACHINE_ARN,
        name=f"bulk-{case_id}",
        input=json.dumps({
            "case_id": case_id,
            "ip_range": ip_range,
            "profile_count": count,
            "trigger_source": "bulk_detection",
        }),
    )

    logger.info(
        "Bulk action Step Functions execution started",
        extra={"case_id": case_id, "state_machine": BULK_ACTION_STATE_MACHINE_ARN},
    )
