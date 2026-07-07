# =============================================================================
# DocQuery AI — Developer Commands
# =============================================================================
# Usage: make <target>
#
# These are shortcuts for common development tasks.
# =============================================================================

.PHONY: install dev run test lint format clean reset

# --- Setup ---
install:                     ## Install production dependencies
	pip install -e .

dev:                         ## Install all dependencies (prod + dev + frontend)
	pip install -e ".[dev,frontend]"

# --- Run ---
run:                         ## Start the FastAPI server
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:                ## Start the Streamlit frontend
	streamlit run frontend/app.py

# --- Quality ---
test:                        ## Run test suite
	pytest tests/ -v --tb=short

test-cov:                    ## Run tests with coverage report
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

lint:                        ## Lint code with ruff
	ruff check app/ tests/ main.py

format:                      ## Auto-format code with ruff
	ruff format app/ tests/ main.py
	ruff check --fix app/ tests/ main.py

typecheck:                   ## Run mypy type checking
	mypy app/ main.py

# --- Data Management ---
reset:                       ## Reset all databases (ChromaDB + SQLite)
	rm -rf data/chroma_db data/sqlite
	mkdir -p data/chroma_db data/sqlite data/uploads
	@echo "✅ Databases reset"

seed:                        ## Load sample documents
	python scripts/seed_data.py

# --- Docker ---
docker-build:                ## Build Docker image
	docker compose build

docker-up:                   ## Start all services via Docker Compose
	docker compose up -d

docker-down:                 ## Stop all services
	docker compose down

docker-logs:                 ## View service logs
	docker compose logs -f

# --- Cleanup ---
clean:                       ## Remove build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ dist/ build/
	@echo "✅ Cleaned"

help:                        ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
