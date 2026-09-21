.PHONY: help install install-dev run lint format test clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime dependencies
	pip install -r requirements.txt

install-dev: ## Install runtime and development dependencies
	pip install -r requirements-dev.txt

run: ## Run the Streamlit app
	streamlit run app.py

lint: ## Lint the codebase with Ruff
	ruff check .

format: ## Auto-format the codebase with Ruff
	ruff format .
	ruff check --fix .

test: ## Run the test suite
	pytest

clean: ## Remove caches and build artifacts
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
