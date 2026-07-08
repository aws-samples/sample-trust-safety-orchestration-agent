#!/bin/bash
set -e

echo "============================================"
echo "  Trust & Safety Orchestration Agent Setup"
echo "============================================"
echo ""

# Check prerequisites
command -v aws >/dev/null 2>&1 || { echo "ERROR: AWS CLI not found. Install: https://aws.amazon.com/cli/"; exit 1; }
command -v sam >/dev/null 2>&1 || { echo "ERROR: SAM CLI not found. Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "ERROR: Node.js not found. Install: https://nodejs.org/"; exit 1; }

# Install uv if not present
if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv (fast Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✓ All prerequisites found (uv $(uv --version 2>/dev/null | head -1))"
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "ERROR: AWS credentials not configured. Run: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
echo "✓ AWS Account: $ACCOUNT_ID"
echo "✓ Region: $REGION"
echo ""

# Install Python dependencies via uv
echo "Installing Python dependencies (uv sync)..."
uv sync -q
echo "✓ Python dependencies installed"

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend && npm install --silent && cd ..
echo "✓ Frontend dependencies installed"

# Build
echo ""
echo "Building SAM application..."
sam build --parallel
echo "✓ Build complete"

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Deploy:     sam deploy --guided"
echo "  2. Seed data:  python scripts/seed_demo_data.py"
echo "  3. Frontend:   cd frontend && npm run dev"
echo ""
echo "Or use: make deploy"
echo ""
