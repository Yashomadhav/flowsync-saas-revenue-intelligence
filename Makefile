# =============================================================================
# FlowSync Revenue Intelligence — Makefile
# =============================================================================
# Usage:
#   make dev          → Start frontend only (mock data, no Docker)
#   make full         → Start full stack via Docker Compose
#   make generate     → Generate synthetic data CSVs
#   make ingest       → Run CSV ingestion pipeline
#   make dbt-run      → Run dbt transformations
#   make validate     → Validate row counts
#   make test         → Run all tests
#   make clean        → Stop all services and clean up
# =============================================================================

.PHONY: help dev full backend generate ingest dbt-run validate test \
        typecheck lint install clean stop logs shell-api shell-db

# Default target
.DEFAULT_GOAL := help

# Colors
CYAN  := \033[0;36m
GREEN := \033[0;32m
YELLOW:= \033[0;33m
RED   := \033[0;31m
RESET := \033[0m

# Paths
WEB_DIR  := apps/web
API_DIR  := apps/api
DATA_DIR := data/generators

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
help:
	@echo ""
	@echo "$(CYAN)FlowSync Revenue Intelligence — Available Commands$(RESET)"
	@echo "=================================================="
	@echo ""
	@echo "$(GREEN)Development:$(RESET)"
	@echo "  make dev          Start frontend only (mock data, port 3001)"
	@echo "  make full         Start full stack via Docker Compose"
	@echo "  make backend      Start PostgreSQL + FastAPI only"
	@echo "  make install      Install all dependencies"
	@echo ""
	@echo "$(GREEN)Data Pipeline:$(RESET)"
	@echo "  make generate     Generate synthetic data CSVs"
	@echo "  make ingest       Run CSV → PostgreSQL ingestion"
	@echo "  make dbt-run      Run dbt transformations (all models)"
	@echo "  make dbt-test     Run dbt tests"
	@echo "  make validate     Validate row counts and data quality"
	@echo "  make seed         Full pipeline: generate + ingest + dbt"
	@echo ""
	@echo "$(GREEN)Testing:$(RESET)"
	@echo "  make typecheck    Run TypeScript type checking"
	@echo "  make lint         Run ESLint"
	@echo "  make test         Run all tests"
	@echo "  make test-api     Test FastAPI endpoints"
	@echo ""
	@echo "$(GREEN)Docker:$(RESET)"
	@echo "  make stop         Stop all Docker services"
	@echo "  make clean        Stop services and remove volumes"
	@echo "  make logs         Tail all service logs"
	@echo "  make shell-api    Open shell in API container"
	@echo "  make shell-db     Open psql in database container"
	@echo "  make pgadmin      Start pgAdmin UI (port 5050)"
	@echo ""

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
install:
	@echo "$(CYAN)Installing frontend dependencies...$(RESET)"
	cd $(WEB_DIR) && npm install
	@echo "$(CYAN)Installing Python dependencies...$(RESET)"
	cd $(API_DIR) && pip install -r requirements.txt
	@echo "$(GREEN)✓ All dependencies installed$(RESET)"

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------
dev:
	@echo "$(CYAN)Starting frontend (mock data mode)...$(RESET)"
	@echo "  Landing:   http://localhost:3001"
	@echo "  Dashboard: http://localhost:3001/dashboard"
	@echo ""
	cd $(WEB_DIR) && NEXT_PUBLIC_USE_MOCK_DATA=true npm run dev

full:
	@echo "$(CYAN)Starting full stack...$(RESET)"
	@if [ ! -f .env ]; then cp env.example .env && echo "$(YELLOW)Created .env from env.example$(RESET)"; fi
	docker-compose up --build -d postgres api web
	@echo "$(GREEN)✓ Full stack running$(RESET)"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API:      http://localhost:8000/api/v1/docs"

backend:
	@echo "$(CYAN)Starting backend services...$(RESET)"
	@if [ ! -f .env ]; then cp env.example .env; fi
	docker-compose up --build -d postgres api
	@echo "$(GREEN)✓ Backend running$(RESET)"
	@echo "  API:  http://localhost:8000"
	@echo "  Docs: http://localhost:8000/api/v1/docs"

# ---------------------------------------------------------------------------
# Data Pipeline
# ---------------------------------------------------------------------------
generate:
	@echo "$(CYAN)Generating synthetic data...$(RESET)"
	cd $(DATA_DIR) && python generate_all.py
	@echo "$(GREEN)✓ Data generated in data/output/$(RESET)"

ingest:
	@echo "$(CYAN)Running ingestion pipeline...$(RESET)"
	docker-compose --profile ingest up --abort-on-container-exit ingest
	@echo "$(GREEN)✓ Data ingested$(RESET)"

dbt-run:
	@echo "$(CYAN)Running dbt transformations...$(RESET)"
	docker-compose --profile dbt run --rm dbt dbt run
	@echo "$(GREEN)✓ dbt models built$(RESET)"

dbt-test:
	@echo "$(CYAN)Running dbt tests...$(RESET)"
	docker-compose --profile dbt run --rm dbt dbt test

dbt-docs:
	@echo "$(CYAN)Generating dbt docs...$(RESET)"
	docker-compose --profile dbt run --rm dbt dbt docs generate
	docker-compose --profile dbt run --rm dbt dbt docs serve

validate:
	@echo "$(CYAN)Validating data quality...$(RESET)"
	docker-compose --profile ingest up --abort-on-container-exit validate

seed: generate ingest dbt-run validate
	@echo "$(GREEN)✓ Full data pipeline complete$(RESET)"

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------
typecheck:
	@echo "$(CYAN)Running TypeScript type check...$(RESET)"
	cd $(WEB_DIR) && npx tsc --noEmit
	@echo "$(GREEN)✓ TypeScript: no errors$(RESET)"

lint:
	@echo "$(CYAN)Running ESLint...$(RESET)"
	cd $(WEB_DIR) && npm run lint

test-api:
	@echo "$(CYAN)Testing FastAPI endpoints...$(RESET)"
	@curl -sf http://localhost:8000/health | python -m json.tool || echo "$(RED)API not running$(RESET)"
	@curl -sf http://localhost:8000/api/v1/executive/summary | python -m json.tool | head -20

test: typecheck lint
	@echo "$(GREEN)✓ All tests passed$(RESET)"

# ---------------------------------------------------------------------------
# Docker management
# ---------------------------------------------------------------------------
stop:
	@echo "$(CYAN)Stopping all services...$(RESET)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped$(RESET)"

clean:
	@echo "$(YELLOW)Stopping services and removing volumes...$(RESET)"
	docker-compose down -v --remove-orphans
	@echo "$(GREEN)✓ Clean complete$(RESET)"

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-web:
	docker-compose logs -f web

shell-api:
	docker-compose exec api bash

shell-db:
	docker-compose exec postgres psql -U flowsync -d flowsync_bi

pgadmin:
	@echo "$(CYAN)Starting pgAdmin...$(RESET)"
	docker-compose --profile tools up -d pgadmin
	@echo "$(GREEN)✓ pgAdmin running at http://localhost:5050$(RESET)"
	@echo "  Email:    admin@flowsync.io"
	@echo "  Password: (see PGADMIN_PASSWORD in .env)"

# ---------------------------------------------------------------------------
# Deployment helpers
# ---------------------------------------------------------------------------
build-web:
	@echo "$(CYAN)Building Next.js for production...$(RESET)"
	cd $(WEB_DIR) && npm run build
	@echo "$(GREEN)✓ Build complete$(RESET)"

build-docker:
	@echo "$(CYAN)Building Docker images...$(RESET)"
	docker-compose build
	@echo "$(GREEN)✓ Images built$(RESET)"

push-docker:
	@echo "$(CYAN)Pushing Docker images...$(RESET)"
	docker-compose push

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
env-check:
	@echo "$(CYAN)Checking environment variables...$(RESET)"
	@test -f .env && echo "$(GREEN)✓ .env exists$(RESET)" || echo "$(RED)✗ .env missing — run: cp env.example .env$(RESET)"
	@echo "Required vars:"
	@grep -E "^[A-Z_]+=$$" env.example | sed 's/=.*//' | while read var; do \
		if grep -q "^$$var=" .env 2>/dev/null; then \
			echo "  $(GREEN)✓ $$var$(RESET)"; \
		else \
			echo "  $(RED)✗ $$var (missing)$(RESET)"; \
		fi; \
	done

status:
	@echo "$(CYAN)Service Status:$(RESET)"
	@docker-compose ps 2>/dev/null || echo "No Docker services running"
	@echo ""
	@echo "$(CYAN)Frontend:$(RESET)"
	@curl -sf http://localhost:3001 > /dev/null && echo "  $(GREEN)✓ Running on port 3001$(RESET)" || echo "  $(YELLOW)Not running$(RESET)"
	@curl -sf http://localhost:3000 > /dev/null && echo "  $(GREEN)✓ Running on port 3000$(RESET)" || true
	@echo "$(CYAN)API:$(RESET)"
	@curl -sf http://localhost:8000/health > /dev/null && echo "  $(GREEN)✓ Running on port 8000$(RESET)" || echo "  $(YELLOW)Not running$(RESET)"
