import json
import logging

from services import metrics_aggregation_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        path = event.get("path", "") or event.get("resource", "")

        if path.endswith("/metrics/realtime"):
            return _handle_realtime_metrics()
        elif path.endswith("/metrics"):
            return _handle_prometheus_metrics()
        elif path.endswith("/actions/recent"):
            return _handle_recent_actions()
        else:
            return _response(404, {"error": f"Unknown path: {path}"})

    except ValueError as e:
        return _response(400, {"error": str(e)})
    except Exception:
        logger.exception("Handler error")
        return _response(500, {"error": "Internal server error"})


def _handle_realtime_metrics():
    metrics = metrics_aggregation_service.get_realtime_metrics()
    return _response(200, metrics)


def _handle_prometheus_metrics():
    metrics = metrics_aggregation_service.get_realtime_metrics()

    lines = []
    lines.append('# HELP platform_safety_score Platform safety score (0-100)')
    lines.append('# TYPE platform_safety_score gauge')
    lines.append(f'platform_safety_score {metrics["platform_safety_score"]}')

    lines.append('# HELP cases_processed_today Total cases processed today')
    lines.append('# TYPE cases_processed_today counter')
    lines.append(f'cases_processed_today {metrics["cases_processed_today"]}')

    lines.append('# HELP autonomous_resolution_rate Autonomous resolution rate')
    lines.append('# TYPE autonomous_resolution_rate gauge')
    lines.append(f'autonomous_resolution_rate {metrics["autonomous_resolution_rate"]}')

    lines.append('# HELP avg_resolution_time_minutes Average resolution time in minutes')
    lines.append('# TYPE avg_resolution_time_minutes gauge')
    lines.append(f'avg_resolution_time_minutes {metrics["avg_resolution_time_minutes"]}')

    lines.append('# HELP review_queue_depth Current review queue depth')
    lines.append('# TYPE review_queue_depth gauge')
    lines.append(f'review_queue_depth {metrics["review_queue_depth"]}')

    lines.append('# HELP elevated_threat_level Whether threat level is elevated')
    lines.append('# TYPE elevated_threat_level gauge')
    lines.append(f'elevated_threat_level {1 if metrics["elevated_threat_level"] else 0}')

    for vtype, count in metrics.get("threat_distribution", {}).items():
        lines.append(f'threat_distribution{{violation_type="{vtype}"}} {count}')

    for stage, count in metrics.get("active_cases_by_stage", {}).items():
        lines.append(f'active_cases_by_stage{{stage="{stage}"}} {count}')

    text_body = "\n".join(lines) + "\n"

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/plain", "Access-Control-Allow-Origin": "*"},
        "body": text_body,
    }


def _handle_recent_actions():
    from repositories import audit_repository

    logs = audit_repository.query_by_event_type("enforcement", limit=20)
    return _response(200, {"recent_actions": logs})


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=str),
    }
