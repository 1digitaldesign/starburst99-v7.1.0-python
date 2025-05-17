###############################################################################
# Makefile for the Starburst99 Population Synthesis Code - Python Version
# - Full Python implementation
###############################################################################

#==============================================================================
# Project configuration
#==============================================================================
# Version information
VERSION = 7.1.0
# Python executable
PYTHON = python3
# Directory structure
SRC_DIR = src/python
BIN_DIR = bin
SCRIPTS_DIR = scripts
TOOLS_DIR = tools
DATA_DIR = data
OUTPUT_DIR = output
DOCS_DIR = docs
TESTS_DIR = $(SRC_DIR)/tests

#==============================================================================
# Python-specific settings
#==============================================================================
# Virtual environment
VENV = venv
VENV_BIN = $(VENV)/bin
VENV_PYTHON = $(VENV_BIN)/python
VENV_PIP = $(VENV_BIN)/pip

# Testing
PYTEST = $(VENV_BIN)/pytest
COVERAGE = $(VENV_BIN)/coverage

# Linting and formatting
BLACK = $(VENV_BIN)/black
FLAKE8 = $(VENV_BIN)/flake8
MYPY = $(VENV_BIN)/mypy
ISORT = $(VENV_BIN)/isort

#==============================================================================
# Build rules
#==============================================================================
# Default target - set up development environment
all: setup test

# Set up Python virtual environment
venv:
	@echo "Creating Python virtual environment..."
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	@echo "Virtual environment created."

# Install package in development mode
develop: venv
	@echo "Installing package in development mode..."
	$(VENV_PIP) install -e .
	@echo "Development installation complete."

# Setup directory structure and links
setup: venv develop
	@echo "Setting up runtime environment..."
	mkdir -p $(BIN_DIR) $(OUTPUT_DIR)
	ln -sf ../$(SCRIPTS_DIR)/go_galaxy $(OUTPUT_DIR)/go_galaxy
	@echo "Creating convenience script..."
	@echo '#!/bin/bash' > $(BIN_DIR)/starburst99
	@echo 'cd "$$(dirname "$$0")/.." && $(VENV_PYTHON) $(SRC_DIR)/starburst_main.py "$$@"' >> $(BIN_DIR)/starburst99
	chmod +x $(BIN_DIR)/starburst99
	@echo "Setup complete."

#==============================================================================
# Testing targets
#==============================================================================
# Run all tests
test: venv
	@echo "Running Python tests..."
	$(PYTEST) $(TESTS_DIR) -v
	@echo "Tests complete."

# Run tests with coverage
test-coverage: venv
	@echo "Running tests with coverage..."
	$(COVERAGE) run -m pytest $(TESTS_DIR) -v
	$(COVERAGE) report
	$(COVERAGE) html
	@echo "Coverage report generated in htmlcov/"

# Run specific test file
test-single: venv
	@echo "Running single test..."
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-single FILE=test_file.py"; \
		exit 1; \
	fi
	$(PYTEST) $(TESTS_DIR)/$(FILE) -v

#==============================================================================
# Code quality targets
#==============================================================================
# Format code with black
format: venv
	@echo "Formatting code with black..."
	$(BLACK) $(SRC_DIR)
	@echo "Code formatting complete."

# Sort imports
sort-imports: venv
	@echo "Sorting imports..."
	$(ISORT) $(SRC_DIR)
	@echo "Import sorting complete."

# Lint code with flake8
lint: venv
	@echo "Linting code with flake8..."
	$(FLAKE8) $(SRC_DIR)
	@echo "Linting complete."

# Type check with mypy
typecheck: venv
	@echo "Type checking with mypy..."
	$(MYPY) $(SRC_DIR)
	@echo "Type checking complete."

# Run all code quality checks
quality: format sort-imports lint typecheck
	@echo "All code quality checks complete."

#==============================================================================
# Running the application
#==============================================================================
# Run the Starburst99 Python version
run: setup
	@echo "Running Starburst99..."
	cd $(OUTPUT_DIR) && $(VENV_PYTHON) ../$(SRC_DIR)/starburst_main.py
	@echo "Execution complete."

# Run with specific input file
run-with-input: setup
	@echo "Running Starburst99 with input file..."
	@if [ -z "$(INPUT)" ]; then \
		echo "Usage: make run-with-input INPUT=filename"; \
		exit 1; \
	fi
	cd $(OUTPUT_DIR) && $(VENV_PYTHON) ../$(SRC_DIR)/starburst_main.py $(INPUT)
	@echo "Execution complete."

#==============================================================================
# Documentation
#==============================================================================
# Generate documentation
docs: venv
	@echo "Generating documentation..."
	$(VENV_BIN)/sphinx-build -b html docs docs/_build
	@echo "Documentation generated in docs/_build/"

#==============================================================================
# Utility targets
#==============================================================================
# Clean up Python artifacts
clean:
	@echo "Cleaning Python artifacts..."
	find $(SRC_DIR) -type f -name "*.pyc" -delete
	find $(SRC_DIR) -type d -name "__pycache__" -delete
	find $(SRC_DIR) -type f -name ".coverage" -delete
	rm -rf $(SRC_DIR)/htmlcov
	rm -rf $(SRC_DIR)/.mypy_cache
	rm -rf $(SRC_DIR)/.pytest_cache
	rm -rf *.egg-info
	rm -rf build dist
	@echo "Clean complete."

# Clean everything including virtual environment
clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	rm -f $(BIN_DIR)/starburst99
	@echo "Full clean complete."

# Convert data files to JSON format (Python converter)
convert-json:
	@echo "Converting data files to JSON format..."
	$(VENV_PYTHON) $(TOOLS_DIR)/converters/convert_data_to_json.py
	@echo "Conversion complete."

# Install the package system-wide
install: venv
	@echo "Installing Starburst99 Python version..."
	$(VENV_PIP) install .
	@echo "Installation complete."

# Create source distribution
dist: venv
	@echo "Creating source distribution..."
	$(VENV_PYTHON) setup.py sdist bdist_wheel
	@echo "Distribution created in dist/"

#==============================================================================
# Help
#==============================================================================
help:
	@echo "Starburst99 Python Makefile Help"
	@echo "================================"
	@echo "Available targets:"
	@echo "  all              - Set up environment and run tests (default)"
	@echo "  setup            - Set up development environment"
	@echo "  test             - Run all tests"
	@echo "  test-coverage    - Run tests with coverage report"
	@echo "  test-single      - Run a single test file (use FILE=...)"
	@echo "  format           - Format code with black"
	@echo "  lint             - Lint code with flake8"
	@echo "  typecheck        - Type check with mypy"
	@echo "  quality          - Run all code quality checks"
	@echo "  run              - Run Starburst99"
	@echo "  run-with-input   - Run with specific input (use INPUT=...)"
	@echo "  docs             - Generate documentation"
	@echo "  clean            - Clean Python artifacts"
	@echo "  clean-all        - Clean everything including venv"
	@echo "  convert-json     - Convert data files to JSON"
	@echo "  install          - Install package system-wide"
	@echo "  dist             - Create source distribution"
	@echo "  help             - Display this help message"

# Mark targets that don't produce files
.PHONY: all setup venv develop test test-coverage test-single format sort-imports lint typecheck quality run run-with-input docs clean clean-all convert-json install dist help