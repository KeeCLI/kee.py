.PHONY: test test-verbose test-coverage install-dev clean lint format type-check

# Python command (try python3 first, fallback to python)
PYTHON := $(shell command -v python3 2> /dev/null || echo python)

# Install development dependencies
install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

# Run tests (fallback to unittest if pytest not available)
test:
	@if $(PYTHON) -c "import pytest" 2>/dev/null; then \
		$(PYTHON) -m pytest; \
	else \
		echo "pytest not found, using unittest instead..."; \
		$(PYTHON) -m unittest test_kee -v; \
	fi

# Run tests with verbose output
test-verbose:
	$(PYTHON) -m pytest -v

# Run tests with coverage
test-coverage:
	$(PYTHON) -m pytest --cov=kee --cov-report=html --cov-report=term

# Run specific test
test-unit:
	$(PYTHON) -m pytest -m unit

# Run unittest instead of pytest (fallback)
test-unittest:
	$(PYTHON) -m unittest test_kee -v

# Run linting
lint:
	$(PYTHON) -m flake8 kee.py test_kee.py --max-line-length=100 --ignore=E501,W503

# Format code
format:
	$(PYTHON) -m black kee.py test_kee.py

# Type checking
type-check:
	$(PYTHON) -m mypy kee.py --ignore-missing-imports

# Clean up
clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage *.egg-info build dist

# Run all checks
check: lint type-check test-unittest

# Help
help:
	@echo "Available targets:"
	@echo "  install-dev       - Install development dependencies"
	@echo "  test             - Run tests with pytest"
	@echo "  test-unittest    - Run tests with unittest (no extra deps)"
	@echo "  test-verbose     - Run tests with verbose output"
	@echo "  test-coverage    - Run tests with coverage report"
	@echo "  lint             - Run linting"
	@echo "  format           - Format code"
	@echo "  type-check       - Run type checking"
	@echo "  clean            - Clean up generated files"
	@echo "  check            - Run all checks (lint, type-check, test)"
	@echo ""
	@echo "Python command being used: $(PYTHON)"
