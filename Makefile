# ==============================================================================
#                 Omni-IPS (Omni-domain Intelligent Problem Solver)
#                        Unified Operational Makefile
# ==============================================================================
# Powered by Astral 'uv' Package Manager & Docker Containerization
# ==============================================================================

.PHONY: help setup test test-rag ingest-chemistry ingest-geometry ingest-chemistry-dry ingest-geometry-dry ingest-chemistry-fast ingest-all ingest-all-fast embed-knowledge docker-up docker-down docker-logs docker-status run-server run-legacy-demo clean

# Shell Configuration
SHELL := /bin/bash
UV := $(shell which uv 2>/dev/null)

# Color Outputs
COLOR_RESET   = \033[0m
COLOR_BOLD    = \033[1m
COLOR_GREEN   = \033[32m
COLOR_BLUE    = \033[34m
COLOR_CYAN    = \033[36m
COLOR_YELLOW  = \033[33m
COLOR_RED     = \033[31m

# Defaults
PORT ?= 8080
HOST ?= 0.0.0.0

help:
	@echo -e "$(COLOR_BOLD)$(COLOR_CYAN)========================================================================$(COLOR_RESET)"
	@echo -e "$(COLOR_BOLD)$(COLOR_GREEN)            Omni-IPS Unified Operation Command Panel (uv-Powered)      $(COLOR_RESET)"
	@echo -e "$(COLOR_BOLD)$(COLOR_CYAN)========================================================================$(COLOR_RESET)"
	@echo -e "$(COLOR_BOLD)Environment Status:$(COLOR_RESET)"
	@if [ -z "$(UV)" ]; then \
		echo -e "  uv Package Manager: $(COLOR_RED)NOT FOUND$(COLOR_RESET) (Please install uv first)"; \
	else \
		echo -e "  uv Package Manager: $(COLOR_GREEN)FOUND$(COLOR_RESET) ($(shell uv --version))"; \
	fi
	@echo -e ""
	@echo -e "$(COLOR_BOLD)1. Setup & Package Management:$(COLOR_RESET)"
	@echo -e "  $(COLOR_CYAN)make setup$(COLOR_RESET)                - Install dependencies & synchronize virtual environment (.venv) using uv"
	@echo -e "  $(COLOR_CYAN)make clean$(COLOR_RESET)                - Remove cached files, pycache, and virtual environment"
	@echo -e ""
	@echo -e "$(COLOR_BOLD)2. Testing & Verification:$(COLOR_RESET)"
	@echo -e "  $(COLOR_CYAN)make test$(COLOR_RESET)                 - Run the multi-domain symbolic engine verification tests"
	@echo -e "  $(COLOR_CYAN)make test-rag$(COLOR_RESET)             - Run the GraphRAG pipeline and explainability agent verification tests"
	@echo -e ""
	@echo -e "$(COLOR_BOLD)3. ETL Pipelines & Ingestion (Neo4j & ChromaDB):$(COLOR_RESET)"
	@echo -e "  $(COLOR_CYAN)make ingest-chemistry$(COLOR_RESET)     - Extract from Wikidata + ingest 20 textbook reactions into Neo4j"
	@echo -e "  $(COLOR_CYAN)make ingest-chemistry-fast$(COLOR_RESET)- Ingest chemistry data immediately, skipping Wikidata SPARQL extraction"
	@echo -e "  $(COLOR_CYAN)make ingest-geometry$(COLOR_RESET)      - Ingest 16 Euclidean axioms and theorems into Neo4j"
	@echo -e "  $(COLOR_CYAN)make ingest-all$(COLOR_RESET)           - Run both chemistry and geometry ETL ingestion pipelines"
	@echo -e "  $(COLOR_CYAN)make ingest-all-fast$(COLOR_RESET)      - Run both chemistry (fast) and geometry ETL ingestion pipelines"
	@echo -e "  $(COLOR_CYAN)make embed-knowledge$(COLOR_RESET)      - Generate local embeddings and populate ChromaDB from Neo4j nodes"
	@echo -e "  $(COLOR_CYAN)make ingest-chemistry-dry$(COLOR_RESET) - Run chemistry ETL in validation (Dry Run) mode without Neo4j"
	@echo -e "  $(COLOR_CYAN)make ingest-geometry-dry$(COLOR_RESET)  - Run geometry ETL in validation (Dry Run) mode without Neo4j"
	@echo -e ""
	@echo -e "$(COLOR_BOLD)4. API Server & Execution:$(COLOR_RESET)"
	@echo -e "  $(COLOR_CYAN)make run-server$(COLOR_RESET)           - Launch FastAPI Gateway locally (Port: $(PORT), Host: $(HOST))"
	@echo -e "  $(COLOR_CYAN)make run-legacy-demo$(COLOR_RESET)      - Run legacy forward-chaining CLI demo (Na + H2O -> NaOH)"
	@echo -e ""
	@echo -e "$(COLOR_BOLD)5. Docker Infrastructure:$(COLOR_RESET)"
	@echo -e "  $(COLOR_CYAN)make docker-up$(COLOR_RESET)            - Build and launch Neo4j, ChromaDB, and Backend containers"
	@echo -e "  $(COLOR_CYAN)make docker-down$(COLOR_RESET)          - Shut down docker compose services and release ports"
	@echo -e "  $(COLOR_CYAN)make docker-status$(COLOR_RESET)        - View status of docker compose services"
	@echo -e "  $(COLOR_CYAN)make docker-logs$(COLOR_RESET)          - Tail live logs from all docker compose containers"
	@echo -e "$(COLOR_BOLD)$(COLOR_CYAN)========================================================================$(COLOR_RESET)"

setup:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Validating and setting up Python environment via uv...$(COLOR_RESET)"
	@if [ -z "$(UV)" ]; then \
		echo -e "$(COLOR_YELLOW)[WARNING] 'uv' is not installed or not in PATH.$(COLOR_RESET)"; \
		echo -e "Installing uv now..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		export PATH="$$HOME/.local/bin:$$PATH"; \
	fi
	@uv sync
	@echo -e "$(COLOR_GREEN)[Omni-IPS] Setup complete. Virtual environment ready in '.venv/'.$(COLOR_RESET)"

test:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Running multi-domain integration & verification tests...$(COLOR_RESET)"
	@uv run python tests/verify_scaffold.py

test-rag:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Running GraphRAG & Explainability pipeline integration tests...$(COLOR_RESET)"
	@uv run python tests/verify_rag.py

ingest-chemistry:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Starting Chemistry ETL pipeline (Wikidata SPARQL + Curated Ingestion)...$(COLOR_RESET)"
	@uv run python data_pipelines/ingest_chemistry.py

ingest-chemistry-dry:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Running Chemistry ETL pipeline in DRY RUN validation mode...$(COLOR_RESET)"
	@uv run python data_pipelines/ingest_chemistry.py --dry-run

ingest-geometry:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Starting Geometry ETL pipeline (Euclidean Axioms Ingestion)...$(COLOR_RESET)"
	@uv run python data_pipelines/ingest_geometry.py

ingest-geometry-dry:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Running Geometry ETL pipeline in DRY RUN validation mode...$(COLOR_RESET)"
	@uv run python data_pipelines/ingest_geometry.py --dry-run

ingest-chemistry-fast:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Starting Chemistry FAST ETL pipeline (skipping SPARQL)...$(COLOR_RESET)"
	@uv run python data_pipelines/ingest_chemistry.py --skip-sparql

ingest-all:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Triggering comprehensive database ingestion (Chemistry + Geometry)...$(COLOR_RESET)"
	@uv run python data_pipelines/ingest_chemistry.py
	@uv run python data_pipelines/ingest_geometry.py
	@echo -e "$(COLOR_GREEN)[Omni-IPS] All ETL pipelines executed successfully. Databases populated.$(COLOR_RESET)"

ingest-all-fast:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Triggering comprehensive FAST database ingestion (Chemistry FAST + Geometry)...$(COLOR_RESET)"
	@uv run python data_pipelines/ingest_chemistry.py --skip-sparql
	@uv run python data_pipelines/ingest_geometry.py
	@echo -e "$(COLOR_GREEN)[Omni-IPS] All fast ETL pipelines executed successfully. Databases populated.$(COLOR_RESET)"

embed-knowledge:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Populating Chroma Vector Database from Neo4j Knowledge Graph...$(COLOR_RESET)"
	@uv run python rag_agent/embed_knowledge.py

run-server:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Launching local FastAPI Gateway server at http://$(HOST):$(PORT)...$(COLOR_RESET)"
	@uv run uvicorn api.main:app --reload --host $(HOST) --port $(PORT)

run-legacy-demo:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Executing legacy forward chaining CLI logic...$(COLOR_RESET)"
	@uv run python src/main.py --kb src/knowledge_base.json --facts Na H2O --goal NaOH

docker-up:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] orchestrating containerized infrastructure (Neo4j + ChromaDB + Backend)...$(COLOR_RESET)"
	docker compose up --build -d
	@echo -e "$(COLOR_GREEN)[Omni-IPS] Infrastructure successfully launched.$(COLOR_RESET)"
	@echo -e "  - Neo4j Browser: http://localhost:7474 (user: neo4j / pass: omni_ips_password)"
	@echo -e "  - FastAPI docs:  http://localhost:8080/docs"
	@echo -e "  - ChromaDB host: http://localhost:8000"

docker-down:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Shutting down docker infrastructure...$(COLOR_RESET)"
	docker compose down
	@echo -e "$(COLOR_GREEN)[Omni-IPS] All containerized services halted.$(COLOR_RESET)"

docker-status:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Retrieving status of containerized services...$(COLOR_RESET)"
	docker compose ps

docker-logs:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Tailing container logs...$(COLOR_RESET)"
	docker compose logs -f

clean:
	@echo -e "$(COLOR_BLUE)[Omni-IPS] Cleaning up workspace artifacts, virtual env, and caches...$(COLOR_RESET)"
	@rm -rf __pycache__ src/__pycache__ core_engine/__pycache__ domains/__pycache__ domains/*/__pycache__ graph_db/__pycache__ tests/__pycache__ data_pipelines/__pycache__ api/__pycache__
	@rm -rf .venv .uv .pytest_cache
	@rm -f engine.py main.py knowledge_base.json
	@echo -e "$(COLOR_GREEN)[Omni-IPS] Cleanup completed.$(COLOR_RESET)"
