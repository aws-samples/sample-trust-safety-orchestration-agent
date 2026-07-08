.PHONY: setup build deploy deploy-lite dev clean test seed help quickstart destroy lint

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

quickstart: setup build deploy-lite seed dev ## One command: setup → build → deploy (lite) → seed → start frontend

setup: ## Install all dependencies (backend + frontend)
	uv sync
	cd frontend && npm install

build: ## Build the SAM application
	sam build --parallel

deploy: ## Deploy full stack (VPC + Redis) — for production
	sam deploy --guided

deploy-lite: ## Deploy without VPC/Redis — fast, cheap, for dev/demo
	sam deploy --guided --parameter-overrides "UseRedis=false Environment=dev"

deploy-quick: ## Deploy (no prompts, uses samconfig.toml)
	sam deploy

dev: ## Start frontend dev server
	cd frontend && npm run dev

test: ## Run backend tests
	uv run pytest -v

lint: ## Lint Python code
	uv run ruff check lambdas/

seed: ## Seed demo data into DynamoDB tables
	uv run python scripts/seed_demo_data.py

clean: ## Remove build artifacts
	rm -rf .aws-sam/ frontend/dist/ lambdas/__pycache__/ .venv/

destroy: ## Delete the deployed stack
	sam delete --stack-name trust-safety-orchestration
