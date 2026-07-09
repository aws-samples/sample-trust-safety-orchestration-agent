"""Seed demo data into DynamoDB tables for dashboard demonstration.

Usage:
    python scripts/seed_demo_data.py
    python scripts/seed_demo_data.py --env staging --region us-west-2
"""

import argparse
import boto3
import json
import uuid
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

parser = argparse.ArgumentParser(description="Seed demo data")
parser.add_argument("--env", default="dev", help="Environment name (default: dev)")
parser.add_argument("--region", default=None, help="AWS region (default: from AWS config)")
args = parser.parse_args()

session = boto3.Session(region_name=args.region)
dynamodb = session.resource("dynamodb")
sts = session.client("sts")
cognito = session.client("cognito-idp")
cf = session.client("cloudformation")

ENV = args.env
ACCOUNT_ID = sts.get_caller_identity()["Account"]
print(f"Seeding data for env={ENV}, account={ACCOUNT_ID}, region={session.region_name}")

cases_table = dynamodb.Table(f"tg-cases-{ENV}")
audit_table = dynamodb.Table(f"tg-audit-logs-{ENV}")
review_queue_table = dynamodb.Table(f"tg-review-queue-{ENV}")
metrics_table = dynamodb.Table(f"tg-metrics-{ENV}")
anomaly_table = dynamodb.Table(f"tg-anomaly-scores-{ENV}")
reviewer_state_table = dynamodb.Table(f"tg-reviewer-state-{ENV}")
config_table = dynamodb.Table(f"tg-config-{ENV}")
blocklist_table = dynamodb.Table(f"tg-blocklist-{ENV}")
evidence_table = dynamodb.Table(f"tg-evidence-metadata-{ENV}")

now = datetime.now(timezone.utc)

VIOLATION_TYPES = ["scam", "harassment", "fake_profile", "bot_farm", "explicit_content", "repeat_offender"]
STATUSES = ["detected", "investigating", "decision_pending", "escalated", "resolved"]
PRIORITIES = ["critical", "high", "medium", "low"]
ACTIONS = ["warning", "content_removal", "temp_suspension", "permanent_ban", "rate_limit"]

fake_names = [
    "CryptoKing99", "LovelyLisa2024", "TravelDude42", "SweetHeart_xo",
    "InvestorPro", "FitnessGuru88", "DreamDate777", "WineAndDine",
    "AdventureSeeker", "GymRat2025", "BeachBum_22", "CoffeeAddict",
    "MusicLover_23", "BookwormBella", "SunshineSmile", "NightOwl_NYC",
    "YogaLife_Om", "ChefAtHome", "HikingHero", "UrbanExplorer",
    "ArtfulDodger", "TechNomad99", "PuppyDad_Rex", "WanderlustSoul",
    "FoodieInLA", "DancerDiva", "SkaterBoi21", "NatureLover_22",
    "SilverFox55", "GamerGirl_X"
]


def seed_cases():
    print("Seeding cases...")
    cases = []
    for i in range(45):
        ts = now - timedelta(hours=random.randint(0, 72), minutes=random.randint(0, 59))
        status = random.choices(STATUSES, weights=[10, 15, 12, 8, 55])[0]
        violation = random.choices(
            VIOLATION_TYPES, weights=[25, 20, 20, 10, 15, 10]
        )[0]
        confidence = round(random.uniform(0.3, 0.99), 2)
        case_id = f"CASE-DEMO-{uuid.uuid4().hex[:8].upper()}"
        user_id = f"user-{uuid.uuid4().hex[:12]}"

        item = {
            "case_id": case_id,
            "user_id": user_id,
            "display_name": random.choice(fake_names),
            "status": status,
            "violation_type": violation,
            "confidence_score": Decimal(str(confidence)),
            "created_at": ts.isoformat(),
            "updated_at": now.isoformat(),
        }
        if status == "resolved":
            item["resolved_at"] = (ts + timedelta(minutes=random.randint(3, 45))).isoformat()
            item["resolution"] = random.choice(ACTIONS)
            item["is_autonomous"] = random.random() > 0.3

        cases_table.put_item(Item=item)
        cases.append(item)

    print(f"  Created {len(cases)} cases")
    return cases


def seed_audit_logs(cases):
    print("Seeding audit logs...")
    count = 0
    event_types = [
        "case_created", "investigation_started", "evidence_assembled",
        "confidence_calculated", "enforcement_executed", "case_escalated",
        "decision_submitted", "autonomous_action"
    ]
    for case in cases:
        num_logs = random.randint(2, 6)
        base_ts = datetime.fromisoformat(case["created_at"])
        for j in range(num_logs):
            log_ts = base_ts + timedelta(minutes=j * random.randint(1, 10))
            event_type = event_types[min(j, len(event_types) - 1)]
            item = {
                "audit_id": f"AUD-{uuid.uuid4().hex[:10].upper()}",
                "timestamp": log_ts.isoformat(),
                "case_id": case["case_id"],
                "event_type": event_type,
                "user_id": case["user_id"],
                "action": random.choice(ACTIONS) if "enforcement" in event_type or "autonomous" in event_type else None,
                "violation_type": case["violation_type"],
                "details": json.dumps({"source": "demo_seed"}),
            }
            item = {k: v for k, v in item.items() if v is not None}
            audit_table.put_item(Item=item)
            count += 1
    print(f"  Created {count} audit log entries")


def seed_review_queue():
    print("Seeding review queue...")
    count = 0
    for i in range(18):
        ts = now - timedelta(hours=random.randint(0, 12), minutes=random.randint(0, 59))
        priority = random.choices(PRIORITIES, weights=[15, 25, 40, 20])[0]
        violation = random.choice(VIOLATION_TYPES)
        item = {
            "queue_id": f"Q-DEMO-{uuid.uuid4().hex[:8].upper()}",
            "case_id": f"CASE-DEMO-{uuid.uuid4().hex[:8].upper()}",
            "user_id": f"user-{uuid.uuid4().hex[:12]}",
            "priority": priority,
            "status": "pending",
            "violation_type": violation,
            "confidence_score": Decimal(str(round(random.uniform(0.4, 0.89), 2))),
            "added_at": ts.isoformat(),
            "created_at": ts.isoformat(),
            "estimated_review_minutes": random.choice([5, 10, 15, 20]),
        }
        review_queue_table.put_item(Item=item)
        count += 1
    print(f"  Created {count} review queue items")


def seed_anomaly_scores():
    print("Seeding anomaly scores...")
    count = 0
    for i in range(30):
        user_id = f"user-{uuid.uuid4().hex[:12]}"
        item = {
            "user_id": user_id,
            "anomaly_score": Decimal(str(round(random.uniform(0.1, 0.95), 3))),
            "factors": {
                "message_velocity": Decimal(str(round(random.uniform(0, 50), 1))),
                "report_count": random.randint(0, 8),
                "account_age_days": random.randint(1, 365),
                "response_rate": Decimal(str(round(random.uniform(0.1, 1.0), 2))),
            },
            "calculated_at": now.isoformat(),
            "ttl": int((now + timedelta(hours=24)).timestamp()),
        }
        anomaly_table.put_item(Item=item)
        count += 1
    print(f"  Created {count} anomaly scores")


def seed_reviewer_state():
    print("Seeding reviewer state...")
    reviewer_id = "b891b3a0-2001-703f-7c41-f541441cb3d1"
    today = now.strftime("%Y-%m-%d")
    item = {
        "reviewer_id": reviewer_id,
        "date": today,
        "cases_reviewed_today": 12,
        "harmful_exposures_today": 4,
        "exposure_threshold": 15,
        "needs_break": False,
        "last_wellness_prompt": (now - timedelta(hours=2)).isoformat(),
        "ttl": int((now + timedelta(hours=24)).timestamp()),
    }
    reviewer_state_table.put_item(Item=item)
    print("  Created reviewer state for admin user")


def seed_config():
    print("Seeding config entries...")
    configs = [
        {"config_key": "threshold_scam", "violation_type": "scam",
         "autonomous_threshold": Decimal("0.90"), "investigation_trigger_threshold": Decimal("0.50")},
        {"config_key": "threshold_harassment", "violation_type": "harassment",
         "autonomous_threshold": Decimal("0.85"), "investigation_trigger_threshold": Decimal("0.45")},
        {"config_key": "threshold_fake_profile", "violation_type": "fake_profile",
         "autonomous_threshold": Decimal("0.88"), "investigation_trigger_threshold": Decimal("0.55")},
        {"config_key": "threshold_bot_farm", "violation_type": "bot_farm",
         "autonomous_threshold": Decimal("0.85"), "investigation_trigger_threshold": Decimal("0.60")},
    ]
    for cfg in configs:
        version_id = f"v-{uuid.uuid4().hex[:8]}"
        item = {
            "config_key": cfg["config_key"],
            "version_id": version_id,
            "value": json.dumps({
                "violation_type": cfg["violation_type"],
                "autonomous_threshold": str(cfg["autonomous_threshold"]),
                "investigation_trigger_threshold": str(cfg["investigation_trigger_threshold"]),
            }),
            "updated_by": "admin@safetyagent.example.com",
            "updated_at": now.isoformat(),
            "is_active": True,
        }
        config_table.put_item(Item=item)
    print(f"  Created {len(configs)} config entries")


def seed_blocklist():
    print("Seeding blocklist entries...")
    count = 0
    for i in range(8):
        item = {
            "hash_type": random.choice(["email_hash", "phone_hash", "device_fingerprint"]),
            "hash_value": f"sha256:{uuid.uuid4().hex}",
            "source_platform": random.choice(["partner_a", "partner_c", "partner_b", "platform"]),
            "violation_type": random.choice(VIOLATION_TYPES),
            "added_at": (now - timedelta(days=random.randint(1, 90))).isoformat(),
            "confidence": Decimal(str(round(random.uniform(0.85, 0.99), 2))),
        }
        blocklist_table.put_item(Item=item)
        count += 1
    print(f"  Created {count} blocklist entries")


def seed_evidence_metadata(cases):
    print("Seeding evidence metadata...")
    count = 0
    evidence_types = ["message_analysis", "image_analysis", "profile_metadata", "cross_platform_intel"]
    for case in cases[:20]:
        for etype in random.sample(evidence_types, k=random.randint(2, 4)):
            item = {
                "case_id": case["case_id"],
                "evidence_type": etype,
                "collected_at": case["created_at"],
                "s3_key": f"evidence/{case['case_id']}/{etype}.json",
                "status": "collected",
            }
            evidence_table.put_item(Item=item)
            count += 1
    print(f"  Created {count} evidence metadata records")


def seed_cognito_user():
    print("Seeding Cognito demo user...")
    stack_name = "trust-safety-orch-dev" if ENV == "dev" else f"trust-safety-orchestration"
    try:
        resp = cf.describe_stacks(StackName=stack_name)
        outputs = {o["OutputKey"]: o["OutputValue"] for o in resp["Stacks"][0]["Outputs"]}
        user_pool_id = outputs.get("CognitoUserPoolId")
    except Exception:
        print("  Skipped — could not find stack outputs for Cognito User Pool ID")
        return

    username = "admin"
    password = "SafetyAdmin123!"
    try:
        cognito.admin_get_user(UserPoolId=user_pool_id, Username=username)
        print(f"  User '{username}' already exists — skipped")
    except cognito.exceptions.UserNotFoundException:
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[{"Name": "custom:role", "Value": "admin"}],
            TemporaryPassword=password,
        )
        cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=username,
            Password=password,
            Permanent=True,
        )
        print(f"  Created user '{username}' with password '{password}'")


if __name__ == "__main__":
    print("=== SafetyAgent Demo Data Seeder ===\n")

    # Verify tables exist before seeding
    try:
        cases_table.table_status
    except Exception as e:
        print(f"ERROR: Cannot access DynamoDB tables. Have you deployed the stack?")
        print(f"  Run: sam deploy --guided --parameter-overrides \"UseRedis=false\"")
        print(f"  Detail: {e}")
        raise SystemExit(1)

    try:
        cases = seed_cases()
        seed_audit_logs(cases)
        seed_review_queue()
        seed_anomaly_scores()
        seed_reviewer_state()
        seed_config()
        seed_blocklist()
        seed_evidence_metadata(cases)
        seed_cognito_user()
        print("\n✓ Done! Demo data seeded successfully.")
        print(f"  Tables populated in env={ENV}, region={session.region_name}")
        print(f"  Login: username=admin, password=SafetyAdmin123!")
        print(f"  Start the frontend: cd frontend && npm run dev")
    except Exception as e:
        print(f"\nERROR: Seeding failed — {e}")
        print("  Make sure the stack is fully deployed (check CloudFormation console).")
        raise SystemExit(1)
