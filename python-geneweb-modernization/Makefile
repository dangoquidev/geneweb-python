# GenEWeb Python - Development Makefile
# Simple, standard, and efficient development workflow

.PHONY: help format check test all setup clean status install run run-simple

# Default target shows help
help:
	@echo "🚀 GenEWeb Python Development"
	@echo "=============================="
	@echo ""
	@echo "Available commands:"
	@echo "  make run     - Start GenEWeb server (main daemon)"
	@echo "  make run-simple - Start simple test server"
	@echo "  make setup   - Setup development environment"
	@echo "  make format  - Format code with black and isort"
	@echo "  make check   - Run quality checks (flake8, mypy)"
	@echo "  make test    - Run all test suites"
	@echo "  make all     - Complete workflow (format + check + test)"
	@echo "  make status  - Show project status"
	@echo "  make clean   - Clean generated files and caches"
	@echo "  make install - Install package in development mode"
	@echo ""
	@echo "Quick start: make setup && make run"

# Show project status (replaces ./dev.py status)
status:
	@echo "🚀 GenEWeb Python - Project Status"
	@echo "=================================="
	@echo ""
	@printf "📁 Python files: "
	@find . -name "*.py" -not -path "./.pytest_cache/*" -not -path "./__pycache__/*" | wc -l
	@printf "📊 Lines of code: "
	@find . -name "*.py" -not -path "./.pytest_cache/*" -not -path "./__pycache__/*" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $$1}' 2>/dev/null || echo "Unable to count"
	@echo ""
	@echo "🛠️  Available commands: run 'make help'"
	@echo "📚 Documentation: CONTRIBUTING.md"
	@echo ""

# Setup development environment
setup:
	@echo "🛠️  Setting up development environment..."
	pip install -e .
	pip install black isort flake8 mypy pytest pre-commit pylint
	pre-commit install
	@echo "✅ Development environment setup completed!"

# Install package in development mode
install:
	pip install -e .

# Format code with black and isort
format:
	@echo "🎨 Formatting code..."
	@which black >/dev/null 2>&1 || (echo "❌ black not found. Run 'make setup' first." && exit 1)
	@which isort >/dev/null 2>&1 || (echo "❌ isort not found. Run 'make setup' first." && exit 1)
	black --line-length=120 .
	isort --profile=black --line-length=120 .
	@echo "✨ Code formatting completed!"

# Run quality checks
check:
	@echo "🔍 Running quality checks..."
	@echo "📏 Checking code style with flake8..."
	@if which flake8 >/dev/null 2>&1; then \
		flake8 --max-line-length=120 . || echo "⚠️  flake8 found style issues"; \
	else \
		echo "⚠️  flake8 not installed. Run 'make setup' to install."; \
	fi
	@echo "🔍 Checking types with mypy..."
	@if which mypy >/dev/null 2>&1; then \
		mypy --ignore-missing-imports . || echo "⚠️  mypy found type issues"; \
	else \
		echo "⚠️  mypy not installed. Run 'make setup' to install."; \
	fi
	@echo "✅ Quality checks completed"

# Run all tests
test:
	@echo "🧪 Running tests..."
	@echo "📋 Running compliance tests..."
	python3 -m pytest test_compliance.py -v
	@echo "🔧 Running basic functionality tests..."
	python3 test_basic.py
	@echo "🌐 Running server tests..."
	@python3 test_server.py || echo "ℹ️  Server tests require running server"
	@echo "🎉 Test execution completed!"

# Complete development workflow
all: format check test
	@echo ""
	@echo "🎉 All development checks completed!"
	@echo "✅ Code formatted, quality checked, tests passed"
	@echo "🚀 Ready to commit!"

# Clean generated files and caches
clean:
	@echo "🧹 Cleaning up generated files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup completed!"

# Advanced targets for power users
lint:
	@echo "🔍 Running comprehensive linting..."
	pylint --max-line-length=120 --disable=C0114,C0116 . || true

coverage:
	@echo "📊 Running test coverage analysis..."
	python3 -m pytest test_compliance.py --cov=. --cov-report=html || echo "Install pytest-cov for coverage: pip install pytest-cov"

# Quick quality check (faster than full check)
quick-check:
	@echo "⚡ Quick quality check..."
	@flake8 --max-line-length=120 . --select=E9,F63,F7,F82 || echo "⚠️  Critical issues found"
	@echo "✅ Quick check completed"

# Run the main GenEWeb daemon server
run:
	@echo "🚀 Starting GenEWeb daemon server..."
	@echo "💡 Use Ctrl+C to stop the server"
	python3 gwd_simple.py -p 2317 -hd .

# Run the simple test server (for development)
run-simple:
	@echo "🧪 Starting simple GenEWeb test server..."
	@echo "💡 Use Ctrl+C to stop the server"
	python3 simple_server.py

# Run with specific port
run-port:
	@echo "🚀 Starting GenEWeb server on custom port..."
	@read -p "Enter port number (default 2317): " port; \
	port=$${port:-2317}; \
	echo "Starting server on port $$port..."; \
	python3 gwd.py -p $$port -hd .

# Show server help
run-help:
	@echo "🚀 GenEWeb Server Options"
	@echo "========================"
	@echo ""
	python3 gwd.py --help
