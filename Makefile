# Makefile
# FlyReady Lab - Docker & Development Commands
# Usage: make <command>

.PHONY: help build up down logs shell test clean deploy

# Default target
help:
	@echo "FlyReady Lab - Available Commands"
	@echo "=================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev           - Start development environment"
	@echo "  make dev-down      - Stop development environment"
	@echo "  make logs          - View application logs"
	@echo "  make shell         - Open shell in app container"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-int      - Run integration tests only"
	@echo "  make coverage      - Run tests with coverage"
	@echo ""
	@echo "Production:"
	@echo "  make build         - Build production images"
	@echo "  make up            - Start production environment"
	@echo "  make down          - Stop production environment"
	@echo "  make deploy        - Full production deployment"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate    - Run database migrations"
	@echo "  make db-rollback   - Rollback last migration"
	@echo "  make db-shell      - Open PostgreSQL shell"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean         - Remove containers and volumes"
	@echo "  make prune         - Deep clean Docker resources"
	@echo "  make status        - Show container status"

# =============================================================================
# Development
# =============================================================================

dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "Development environment started!"
	@echo "Application: http://localhost:8501"
	@echo "API: http://localhost:8000"

dev-down:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

dev-rebuild:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

logs:
	docker-compose logs -f flyready-app

logs-api:
	docker-compose logs -f api

logs-all:
	docker-compose logs -f

shell:
	docker-compose exec flyready-app /bin/bash

shell-api:
	docker-compose exec api /bin/bash

# =============================================================================
# Testing
# =============================================================================

test:
	docker-compose exec flyready-app pytest -v

test-unit:
	docker-compose exec flyready-app pytest tests/unit -v

test-int:
	docker-compose exec flyready-app pytest tests/integration -v

coverage:
	docker-compose exec flyready-app pytest --cov=src --cov-report=html --cov-report=term

lint:
	docker-compose exec flyready-app ruff check src/
	docker-compose exec flyready-app mypy src/

format:
	docker-compose exec flyready-app ruff format src/

# =============================================================================
# Production
# =============================================================================

build:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production environment started!"

down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

deploy: build
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans
	@echo "Deployment complete!"
	@make status

restart:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart flyready-app api

# =============================================================================
# Database
# =============================================================================

db-migrate:
	docker-compose exec api alembic upgrade head

db-rollback:
	docker-compose exec api alembic downgrade -1

db-revision:
	docker-compose exec api alembic revision --autogenerate -m "$(msg)"

db-shell:
	docker-compose exec postgres psql -U flyready -d flyready

db-backup:
	docker-compose exec postgres pg_dump -U flyready flyready > backup_$$(date +%Y%m%d_%H%M%S).sql

db-restore:
	docker-compose exec -T postgres psql -U flyready flyready < $(file)

# =============================================================================
# Redis
# =============================================================================

redis-shell:
	docker-compose exec redis redis-cli

redis-flush:
	docker-compose exec redis redis-cli FLUSHALL

# =============================================================================
# Monitoring
# =============================================================================

monitoring-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d prometheus grafana
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000"

# =============================================================================
# Utilities
# =============================================================================

status:
	@echo "Container Status:"
	@docker-compose ps

health:
	@echo "Health Checks:"
	@curl -s http://localhost:8501/_stcore/health || echo "Streamlit: DOWN"
	@curl -s http://localhost:8000/health || echo "API: DOWN"

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

prune:
	docker-compose down -v --remove-orphans
	docker system prune -af --volumes
	@echo "All Docker resources cleaned!"

# SSL certificate generation (for development)
ssl-generate:
	@mkdir -p nginx/ssl
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout nginx/ssl/privkey.pem \
		-out nginx/ssl/fullchain.pem \
		-subj "/CN=localhost"
	@echo "Self-signed SSL certificate generated!"

# Environment setup
env-setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created from .env.example"; \
	else \
		echo ".env file already exists"; \
	fi

# Version info
version:
	@echo "FlyReady Lab"
	@echo "Version: $$(cat VERSION 2>/dev/null || echo '1.0.0')"
	@docker --version
	@docker-compose --version
