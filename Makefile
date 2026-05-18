.PHONY: help setup run clean test

PYTHON = python3
SRC_DIR = src
MAIN = $(SRC_DIR)/main.py
KB = $(SRC_DIR)/knowledge_base.json

help:
	@echo "========================================================================"
	@echo "            Forward Chaining Chemical Inference Engine — Makefile       "
	@echo "========================================================================"
	@echo "Available commands:"
	@echo "  make setup        : Validate environment requirements"
	@echo "  make run          : Run default synthesis task (Na + H2O -> NaOH)"
	@echo "  make test         : Run multi-step chain synthesis task (Na + H2O + HCl -> NaCl)"
	@echo "  make clean        : Remove legacy root-level Python scripts and cached files"
	@echo "  make run-custom   : Run custom execution. Example: make run-custom FACTS='Na H2O' GOAL='NaOH'"
	@echo "========================================================================"

setup:
	@echo "[AIE SETUP] Checking Python installation..."
	@$(PYTHON) --version
	@echo "[AIE SETUP] Verification complete. Ready to run."

run:
	@$(PYTHON) $(MAIN) --kb $(KB) --facts Na H2O --goal NaOH

test:
	@$(PYTHON) $(MAIN) --kb $(KB) --facts Na H2O HCl --goal NaCl

run-custom:
	@if [ -z "$(FACTS)" ]; then \
		echo "[ERROR] Please specify FACTS. Example: make run-custom FACTS='Na H2O' GOAL='NaOH'"; \
		exit 1; \
	fi
	@if [ -z "$(GOAL)" ]; then \
		$(PYTHON) $(MAIN) --kb $(KB) --facts $(FACTS); \
	else \
		$(PYTHON) $(MAIN) --kb $(KB) --facts $(FACTS) --goal $(GOAL); \
	fi

clean:
	@echo "[AIE CLEAN] Cleaning up legacy workspace files..."
	@rm -rf __pycache__ $(SRC_DIR)/__pycache__
	@rm -f engine.py main.py knowledge_base.json
	@echo "[AIE CLEAN] Cleanup complete."
