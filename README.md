# Trust & Safety Orchestration Agent

An autonomous Trust & Safety system that uses multi-agent orchestration on AWS to detect, investigate, and resolve policy violations at scale. The system combines event-driven processing, parallel evidence gathering, confidence-scored decision making, and automated enforcement to handle content moderation and safety enforcement with human-in-the-loop escalation for sensitive cases.

## Architecture

![Architecture](docs/architecture.drawio)

The system follows an event-driven pipeline: **Detection > Investigation > Decision > Enforcement**.

1. Behavioral events stream in via Kinesis and are scored for anomalies
2. When thresholds are exceeded, a Step Functions investigation workflow runs evidence gathering in parallel
3. A confidence calculator scores violations; the policy engine routes to autonomous enforcement or human review
4. Enforcement actions execute automatically for high-confidence cases, with full audit trails

## AWS Services Used

| Service | Purpose |
|---------|---------|
| AWS Lambda | Event processing, API handlers, business logic (Python 3.11, arm64) |
| AWS Step Functions | Investigation and bulk action workflow orchestration |
| Amazon DynamoDB | Operational data storage (cases, evidence metadata, audit logs, config) |
| Amazon S3 | Evidence storage, audit archives, configuration backups |
| Amazon ElastiCache (Redis) | Rate limiting, caching, session management |
| Amazon API Gateway | REST API + WebSocket for real-time dashboard updates |
| Amazon Kinesis | Behavioral event streaming |
| Amazon CloudWatch | Monitoring dashboards, alarms, and metrics |

## Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) v2 (configured with credentials)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) v1.90+
- [uv](https://docs.astral.sh/uv/) (auto-installed by `setup.sh` if missing)
- Node.js 18+ and npm (for frontend)
- An AWS account with appropriate permissions

> **Note:** `uv` manages Python versions and dependencies automatically. You don't need to install Python separately — `uv` handles it.

## Quick Start

### Try the UI instantly (no AWS account needed)

```bash
git clone https://github.com/aws-samples/trust-safety-orchestration-agent.git
cd trust-safety-orchestration-agent/frontend
npm install && npm run dev
```

Open http://localhost:5173 — the dashboard runs in **demo mode** with mock data. No backend, no deploy, no AWS credentials required.

### Deploy to AWS (full stack)

```bash
cd trust-safety-orchestration-agent
make quickstart
```

That's it. This installs deps, builds, deploys a lightweight stack (no VPC/Redis), seeds demo data, and starts the frontend connected to your live backend.

### Manual steps (if you prefer)

```bash
./setup.sh                    # Check prereqs, install deps, build
sam deploy --guided \         # Deploy without VPC/Redis (fast, ~2 min)
  --parameter-overrides "UseRedis=false"
python scripts/seed_demo_data.py   # Seed demo data
cd frontend && npm run dev         # Start dashboard
```

### Enterprise / Production deployment (full stack)

For production workloads, deploy with VPC and ElastiCache Redis enabled (the default):

```bash
./setup.sh
sam deploy --guided
```

When prompted for parameters:
- `Environment`: `prod` (or `staging`)
- `UseRedis`: `true` (default — includes VPC, Redis, security groups)
- `RedisNodeType`: `cache.t3.medium` (or larger for high-throughput)
- `PlatformUserApiUrl`: Your platform's internal user API endpoint
- `PlatformMessagingApiUrl`: Your platform's messaging API endpoint

This deploys the full production stack:
- **VPC** with private subnets and VPC endpoints (DynamoDB, S3)
- **ElastiCache Redis** for rate limiting, caching, and session management
- **Security groups** isolating Redis and Lambda traffic
- All Lambda functions run inside the VPC for network-level isolation

```bash
# Seed initial configuration
python scripts/seed_demo_data.py --env prod --region us-east-1

# Build and deploy frontend to your CDN / S3 + CloudFront
cd frontend
cp .env.example .env.production
# Set VITE_API_URL and VITE_WS_URL from SAM deploy outputs
npm run build
# Upload dist/ to your hosting (S3, Amplify, etc.)
```

**Estimated production costs** (moderate traffic, ~1M events/day):
- ElastiCache Redis (cache.t3.medium): ~$50/month
- DynamoDB (on-demand): ~$25-75/month
- Lambda: ~$10-30/month
- API Gateway: ~$5-15/month
- Kinesis (1 shard): ~$15/month
- Other (S3, CloudWatch, SQS): ~$10/month
- **Total: ~$115-195/month**

## Makefile Commands

```bash
make help          # Show all available commands
make setup         # Install all dependencies
make build         # Build SAM application
make deploy        # Deploy (guided)
make deploy-quick  # Deploy (no prompts)
make dev           # Start frontend dev server
make test          # Run backend tests
make seed          # Seed demo data
make clean         # Remove build artifacts
make destroy       # Delete the deployed stack
```

## Manual Deployment

### Backend

```bash
sam build --parallel
sam deploy --guided    # First time (interactive)
sam deploy             # Subsequent deploys
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Set VITE_API_URL and VITE_WS_URL from SAM deploy outputs
npm run build          # Production build
npm run dev            # Local development
```

## Project Structure

```
template.yaml                  # SAM infrastructure-as-code (all AWS resources)
samconfig.toml                 # SAM deployment configuration
statemachines/
  investigation_workflow.asl.json   # Investigation orchestration (ASL)
  bulk_action_workflow.asl.json     # Bulk action orchestration (ASL)
lambdas/
  handlers/                    # API Gateway Lambda handlers
  processors/                  # Event-driven processors (Kinesis, EventBridge, SQS)
  services/                    # Business logic layer
  repositories/                # Data access layer (DynamoDB, S3, Redis)
  tests/                       # Unit, integration, and performance tests
frontend/
  src/                         # React + TypeScript SPA dashboard
docs/                          # Architecture diagram and design docs
scripts/                       # Deployment and utility scripts
docs/                          # Design documents and architecture diagrams
```

## Cost Estimate

This sample uses serverless and on-demand services, so costs scale with usage. For a development/test workload with minimal traffic, expect approximately:

- **Lambda**: Included in free tier for low volumes
- **DynamoDB**: On-demand pricing, minimal cost at low scale
- **ElastiCache Redis**: Starts at ~$0.017/hr for cache.t3.micro
- **API Gateway**: $1.00 per million REST API calls
- **Step Functions**: $0.025 per 1,000 state transitions
- **S3/Kinesis/CloudWatch**: Minimal at low volumes

**Important**: Review the [AWS Pricing](https://aws.amazon.com/pricing/) page and use the [AWS Pricing Calculator](https://calculator.aws/) to estimate costs for your expected workload. Remember to delete resources when no longer needed.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

This sample includes several security best practices:

- All Lambda functions use least-privilege IAM policies
- DynamoDB tables use encryption at rest
- S3 buckets enforce encryption and block public access
- API endpoints require authentication (JWT)
- Audit logs are immutable — enforcement halts if audit logging fails
- Sensitive cases (self-harm, child safety) always escalate to human review

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
