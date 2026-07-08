"""Live data simulator for SafetyAgent demo.

Continuously generates realistic Trust & Safety events that flow through
the pipeline, creating cases, audit logs, anomaly scores, and review queue
items to make the dashboard feel alive during a demo.

Run: python3 scripts/live_simulator.py
Stop: Ctrl+C
"""

import boto3
import json
import uuid
import random
import time
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name="us-west-2")

ENV = "dev"
cases_table = dynamodb.Table(f"tg-cases-{ENV}")
audit_table = dynamodb.Table(f"tg-audit-logs-{ENV}")
review_queue_table = dynamodb.Table(f"tg-review-queue-{ENV}")
metrics_table = dynamodb.Table(f"tg-metrics-{ENV}")
anomaly_table = dynamodb.Table(f"tg-anomaly-scores-{ENV}")

VIOLATION_TYPES = ["scam", "harassment", "fake_profile", "bot_farm", "explicit_content", "repeat_offender"]
VIOLATION_WEIGHTS = [30, 20, 20, 10, 12, 8]
PRIORITIES = ["critical", "high", "medium", "low"]
ACTIONS = ["warning", "content_removal", "temp_suspension", "permanent_ban", "rate_limit"]

DISPLAY_NAMES = [
    "CryptoKing99", "LovelyLisa2024", "TravelDude42", "SweetHeart_xo",
    "InvestorPro", "FitnessGuru88", "DreamDate777", "WineAndDine",
    "AdventureSeeker", "GymRat2025", "BeachBum_22", "CoffeeAddict",
    "MusicLover_23", "BookwormBella", "SunshineSmile", "NightOwl_NYC",
    "YogaLife_Om", "ChefAtHome", "HikingHero", "UrbanExplorer",
    "QuickBuck_Pro", "SweetTalker01", "FakeLove99", "MoneyMoves_X",
    "TooGoodToBeTrue", "RomanceScammer", "PuppyDad_Rex", "WanderlustSoul",
]

SCAM_NARRATIVES = [
    "Crypto investment pitch after 3 messages",
    "Requesting wire transfer for 'emergency'",
    "Sending external links to fake trading platform",
    "Love-bombing followed by financial request",
    "Fake military deployment money scam",
]

HARASSMENT_NARRATIVES = [
    "Repeated unwanted messages after being unmatched",
    "Escalating hostile language in conversation",
    "Threatening messages after rejection",
    "Multiple accounts targeting same victim",
]

FAKE_PROFILE_NARRATIVES = [
    "Stock photo detected via reverse image search",
    "AI-generated profile image detected (0.94 confidence)",
    "Profile data inconsistencies across fields",
    "Stolen photos from Instagram public profile",
]

active_cases = {}
stats = {"created": 0, "resolved_auto": 0, "resolved_human": 0, "escalated": 0}


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] {msg}")


def create_anomaly_detection():
    """Simulate a behavioral anomaly being detected."""
    user_id = f"user-{uuid.uuid4().hex[:12]}"
    violation = random.choices(VIOLATION_TYPES, weights=VIOLATION_WEIGHTS)[0]
    anomaly_score = round(random.uniform(0.55, 0.98), 3)
    name = random.choice(DISPLAY_NAMES)

    anomaly_table.put_item(Item={
        "user_id": user_id,
        "anomaly_score": Decimal(str(anomaly_score)),
        "factors": {
            "message_velocity": Decimal(str(round(random.uniform(1.5, 12.0), 1))),
            "report_count": random.randint(0, 6),
            "account_age_days": random.randint(0, 30),
            "response_rate": Decimal(str(round(random.uniform(0.01, 0.4), 2))),
        },
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "ttl": int((datetime.now(timezone.utc) + timedelta(hours=12)).timestamp()),
    })

    if anomaly_score >= 0.5:
        create_case(user_id, name, violation, anomaly_score)


def create_case(user_id, display_name, violation, anomaly_score):
    """Create a new investigation case."""
    now = datetime.now(timezone.utc)
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    confidence = round(random.uniform(0.4, 0.98), 2)

    item = {
        "case_id": case_id,
        "user_id": user_id,
        "display_name": display_name,
        "status": "detected",
        "violation_type": violation,
        "confidence_score": Decimal(str(confidence)),
        "anomaly_score": Decimal(str(anomaly_score)),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    cases_table.put_item(Item=item)

    write_audit("case_created", case_id, user_id, violation)
    stats["created"] += 1
    log(f"NEW CASE {case_id} | {display_name} | {violation} | confidence={confidence}")

    active_cases[case_id] = {
        "case_id": case_id,
        "user_id": user_id,
        "display_name": display_name,
        "violation": violation,
        "confidence": confidence,
        "status": "detected",
        "created_at": now,
    }


def progress_case(case_id):
    """Move a case through the pipeline."""
    if case_id not in active_cases:
        return

    case = active_cases[case_id]
    now = datetime.now(timezone.utc)
    current = case["status"]

    transitions = {
        "detected": "investigating",
        "investigating": "decision_pending",
        "decision_pending": None,
    }

    if current == "decision_pending":
        handle_decision(case_id)
        return

    next_status = transitions.get(current)
    if not next_status:
        return

    case["status"] = next_status
    cases_table.update_item(
        Key={"case_id": case_id},
        UpdateExpression="SET #s = :s, updated_at = :t",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": next_status, ":t": now.isoformat()},
    )

    event_map = {"investigating": "investigation_started", "decision_pending": "confidence_calculated"}
    write_audit(event_map.get(next_status, next_status), case_id, case["user_id"], case["violation"])

    if next_status == "investigating":
        log(f"  INVESTIGATING {case_id} | evidence assembly started")
    elif next_status == "decision_pending":
        log(f"  SCORED {case_id} | confidence={case['confidence']}")


def handle_decision(case_id):
    """Make autonomous or escalation decision."""
    if case_id not in active_cases:
        return

    case = active_cases[case_id]
    now = datetime.now(timezone.utc)
    confidence = case["confidence"]
    violation = case["violation"]

    sensitive = violation in ("self_harm", "child_safety", "illegal_activity")

    if sensitive or confidence < 0.75:
        # Escalate to human review
        priority = "critical" if sensitive else ("high" if confidence >= 0.6 else "medium")
        review_queue_table.put_item(Item={
            "queue_id": f"Q-{uuid.uuid4().hex[:8].upper()}",
            "case_id": case_id,
            "user_id": case["user_id"],
            "priority": priority,
            "status": "pending",
            "violation_type": violation,
            "confidence_score": Decimal(str(confidence)),
            "added_at": now.isoformat(),
            "created_at": now.isoformat(),
            "estimated_review_minutes": random.choice([5, 10, 15, 20]),
        })
        cases_table.update_item(
            Key={"case_id": case_id},
            UpdateExpression="SET #s = :s, updated_at = :t",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": "escalated", ":t": now.isoformat()},
        )
        write_audit("case_escalated", case_id, case["user_id"], violation)
        stats["escalated"] += 1
        log(f"  ESCALATED {case_id} | {violation} @ {confidence} → {priority} priority queue")
        del active_cases[case_id]

    else:
        # Autonomous enforcement
        if confidence >= 0.90:
            action = "permanent_ban"
        elif confidence >= 0.75:
            action = random.choice(["temp_suspension", "content_removal", "rate_limit"])
        else:
            action = "warning"

        cases_table.update_item(
            Key={"case_id": case_id},
            UpdateExpression="SET #s = :s, updated_at = :t, resolved_at = :r, resolution = :a, is_autonomous = :auto",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":s": "resolved",
                ":t": now.isoformat(),
                ":r": now.isoformat(),
                ":a": action,
                ":auto": True,
            },
        )
        write_audit("enforcement_executed", case_id, case["user_id"], violation, action=action)
        stats["resolved_auto"] += 1
        log(f"  ENFORCED {case_id} | {action} (autonomous) | {violation} @ {confidence}")
        del active_cases[case_id]


def write_audit(event_type, case_id, user_id, violation_type, action=None):
    now = datetime.now(timezone.utc)
    item = {
        "audit_id": f"AUD-{uuid.uuid4().hex[:10].upper()}",
        "timestamp": now.isoformat(),
        "case_id": case_id,
        "event_type": event_type,
        "user_id": user_id,
        "violation_type": violation_type,
    }
    if action:
        item["action"] = action
    audit_table.put_item(Item=item)


def update_aggregate_metrics():
    """Update the aggregate metrics that the dashboard queries."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total = stats["created"]
    autonomous = stats["resolved_auto"]
    escalated = stats["escalated"]

    metrics_table.put_item(Item={
        "metric_name": "cases_processed",
        "timestamp": today_start.isoformat(),
        "value": Decimal(str(total + 287)),
        "ttl": int((now + timedelta(hours=24)).timestamp()),
    })
    metrics_table.put_item(Item={
        "metric_name": "autonomous_resolutions",
        "timestamp": (now - timedelta(hours=1)).isoformat(),
        "value": Decimal(str(autonomous + 218)),
        "ttl": int((now + timedelta(hours=24)).timestamp()),
    })
    metrics_table.put_item(Item={
        "metric_name": "total_resolutions",
        "timestamp": (now - timedelta(hours=1)).isoformat(),
        "value": Decimal(str(autonomous + escalated + 287)),
        "ttl": int((now + timedelta(hours=24)).timestamp()),
    })
    avg_time = round(random.uniform(6.5, 11.0), 1)
    metrics_table.put_item(Item={
        "metric_name": "avg_resolution_time_minutes",
        "timestamp": now.isoformat(),
        "value": Decimal(str(avg_time)),
        "ttl": int((now + timedelta(hours=24)).timestamp()),
    })
    # Anomaly detections for elevated threat tracking
    metrics_table.put_item(Item={
        "metric_name": "anomaly_detections",
        "timestamp": now.isoformat(),
        "value": Decimal(str(random.randint(20, 45))),
        "ttl": int((now + timedelta(hours=24)).timestamp()),
    })


def run_simulation():
    print("=" * 60)
    print("  SafetyAgent Live Demo Simulator")
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    cycle = 0
    consecutive_errors = 0
    while True:
        cycle += 1
        try:
            print(f"\n--- Cycle {cycle} ---")

            for _ in range(random.randint(1, 3)):
                create_anomaly_detection()

            time.sleep(random.uniform(1.0, 2.0))

            case_ids = list(active_cases.keys())
            random.shuffle(case_ids)
            for cid in case_ids[:random.randint(1, min(3, len(case_ids) or 1))]:
                progress_case(cid)
                time.sleep(random.uniform(0.5, 1.5))

            if cycle % 3 == 0:
                update_aggregate_metrics()
                total = stats["created"]
                auto = stats["resolved_auto"]
                esc = stats["escalated"]
                pending = len(active_cases)
                rate = round(auto / max(auto + esc, 1) * 100, 1)
                print(f"  [STATS] created={total} auto={auto} escalated={esc} pending={pending} rate={rate}%")

            if cycle % 5 == 0:
                resolve_escalated_case()

            consecutive_errors = 0
            time.sleep(random.uniform(2.0, 5.0))

        except KeyboardInterrupt:
            raise
        except Exception as e:
            consecutive_errors += 1
            backoff = min(2 ** consecutive_errors, 30)
            log(f"ERROR (attempt {consecutive_errors}): {e} — retrying in {backoff}s")
            time.sleep(backoff)


def resolve_escalated_case():
    """Simulate a human reviewer resolving a queued case."""
    now = datetime.now(timezone.utc)
    resp = review_queue_table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr("status").eq("pending"),
        Limit=5,
    )
    items = resp.get("Items", [])
    if not items:
        return

    item = random.choice(items)
    action = random.choice(["permanent_ban", "temp_suspension", "content_removal", "warning"])

    review_queue_table.update_item(
        Key={"queue_id": item["queue_id"]},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": "completed"},
    )

    cases_table.update_item(
        Key={"case_id": item["case_id"]},
        UpdateExpression="SET #s = :s, updated_at = :t, resolved_at = :r, resolution = :a, is_autonomous = :auto",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "resolved",
            ":t": now.isoformat(),
            ":r": now.isoformat(),
            ":a": action,
            ":auto": False,
        },
    )

    write_audit("decision_submitted", item["case_id"], item["user_id"], item["violation_type"], action=action)
    stats["resolved_human"] += 1
    log(f"  HUMAN REVIEW {item['case_id']} → {action}")


if __name__ == "__main__":
    try:
        run_simulation()
    except KeyboardInterrupt:
        print("\n\nSimulator stopped.")
        print(f"Final stats: {json.dumps(stats, indent=2)}")
