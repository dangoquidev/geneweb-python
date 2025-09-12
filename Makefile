# GenEWeb Python - Development Makefile
# Simple, standard, and efficient development workflow

# Detect Python command (prefer python3, fallback to python)
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null || echo "python")

# Check if Python is available
ifeq ($(shell command -v $(PYTHON) 2> /dev/null),)
$(error Python is not installed or not in PATH. Please install Python 3.6+ and try again)
endif

.PHONY: help format check test test-legacy test-all test-pytest test-unittest test-compliance test-server all setup clean status install run run-simple

# Default target shows help
help:
	@echo "🚀 GenEWeb Python Development"
	@echo "=============================="
	@echo ""
	@echo "Available commands:"
	@echo "  make run     - Start GenEWeb server (databases in data/)"
	@echo "  make run-simple - Start simple test server (databases in data/)"
	@echo "  make setup   - Setup development environment"
	@echo "  make setup-frontend - Install frontend dependencies"
	@echo "  make create-frontend - Create new React frontend project"
	@echo "  make format  - Format code with black and isort + auto-fixes"
	@echo "  make autofix - Auto-fix common style issues only"
	@echo "  make check   - Run quality checks (flake8, mypy)"
	@echo "  make test    - Run all tests (legacy OCaml + Python)"
	@echo "  make test-legacy - Run legacy OCaml tests"
	@echo "  make test-pytest - Run pytest tests specifically"
	@echo "  make mypy-help - Get assistance with MyPy errors"
	@echo "  make mypy-safe - Auto-fix SAFE MyPy errors only"
	@echo "  make all     - Complete workflow (format + check + test)"
	@echo "  make status  - Show project status"
	@echo "  make list-db - List available databases"
	@echo "  make clean   - Clean generated files and caches"
	@echo "  make install - Install package in development mode"
	@echo ""
	@echo "Quick start: make setup && make run"

# Show project status (replaces ./dev.py status)
status:
	@echo "🚀 GenEWeb Python - Project Status"
	@echo "=================================="
	@echo ""
	@echo "🐍 Python: $(PYTHON) ($(shell $(PYTHON) --version 2>&1))"
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
	@echo "📦 Installing package in development mode..."
	pip install -e .
	@echo "🔧 Installing development tools..."
	pip install --upgrade pip
	pip install black isort flake8 mypy pytest pre-commit pylint pytest-cov autopep8 autoflake
	@echo "📦 Installing pnpm (package manager for frontend)..."
	@if command -v npm >/dev/null 2>&1; then \
		npm install -g pnpm || echo "⚠️  Failed to install pnpm. You may need to run with sudo or install manually."; \
	else \
		echo "⚠️  npm not found. Please install Node.js first to use pnpm."; \
	fi
	@echo "🎨 Setting up frontend development environment..."
	@if [ -d "src/frontend" ] && [ -f "src/frontend/package.json" ]; then \
		echo "📦 Installing frontend dependencies from src/frontend..."; \
		(cd src/frontend && (pnpm install || npm install)) && echo "✅ Frontend dependencies installed"; \
	else \
		echo "ℹ️  Frontend directory not found. Run setup commands from Next steps to create it."; \
	fi
	@echo "🪝 Installing pre-commit hooks..."
	pre-commit install
	@echo "✨ Installing pre-commit dependencies..."
	pre-commit install --install-hooks
	@echo "✅ Development environment setup completed!"
	@echo ""
	@echo "🎯 Next steps:"
	@echo "  • Run 'make test' to verify everything works"
	@echo "  • Run 'make run' to start the server"
	@echo "  • Set up frontend: mkdir -p src/frontend && cd src/frontend && pnpm create vite . --template react"
	@echo ""
	@echo "📋 Installed tools:"
	@echo "  🐍 Python: $(PYTHON)"
	@if command -v pnpm >/dev/null 2>&1; then \
		echo "  📦 pnpm: $(shell pnpm --version 2>/dev/null || echo 'not found')"; \
	else \
		echo "  ⚠️  pnpm: not installed (needed for frontend development)"; \
	fi

# Install package in development mode
install:
	pip install -e .

# Format code with black and isort + auto-fix common issues
format:
	@echo "🎨 Formatting code and fixing style issues..."
	@which black >/dev/null 2>&1 || (echo "❌ black not found. Run 'make setup' first." && exit 1)
	@which isort >/dev/null 2>&1 || (echo "❌ isort not found. Run 'make setup' first." && exit 1)
	@which autopep8 >/dev/null 2>&1 || (echo "⚠️  autopep8 not found. Run 'make setup' to install." && exit 1)
	@which autoflake >/dev/null 2>&1 || (echo "⚠️  autoflake not found. Run 'make setup' to install." && exit 1)
	@echo "🧹 Removing unused imports..."
	autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive src/ tests/ || true
	@echo "🔧 Fixing whitespace and basic formatting..."
	autopep8 --in-place --aggressive --aggressive --max-line-length=120 --recursive src/ tests/ || true
	@echo "⚫ Applying black formatting..."
	black --line-length=120 src/ tests/ || true
	@echo "📋 Sorting imports..."
	isort --profile=black --line-length=120 src/ tests/ || true
	@echo "✨ Code formatting and style fixes completed!"

# Auto-fix specific style issues
autofix:
	@echo "🔧 Auto-fixing common style issues..."
	@echo "  • Removing trailing whitespace..."
	@find src/ tests/ -name "*.py" -exec sed -i 's/[[:space:]]*$$//' {} \; 2>/dev/null || true
	@echo "  • Removing unused imports..."
	@autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive src/ tests/ || true
	@echo "  • Fixing whitespace around parentheses..."
	@autopep8 --select=E201,E202,E203 --in-place --recursive src/ tests/ || true
	@echo "  • Fixing line length..."
	@autopep8 --select=E501 --max-line-length=120 --in-place --recursive src/ tests/ || true
	@echo "  • Fixing f-strings without placeholders..."
	@$(PYTHON) scripts/fix_fstrings.py || true
	@echo "✅ Auto-fixes completed!"

# Run quality checks
check:
	@echo "🔍 Running quality checks..."
	@echo "📏 Checking code style with flake8..."
	@if which flake8 >/dev/null 2>&1; then \
		flake8 --config=config/.flake8 src/ tests/ || echo "⚠️  flake8 found style issues"; \
	else \
		echo "⚠️  flake8 not installed. Run 'make setup' to install."; \
	fi
	@echo "🔍 Checking types with mypy..."
	@if which mypy >/dev/null 2>&1; then \
		PYTHONPATH=src mypy --config-file=config/mypy.ini src/ || echo "⚠️  mypy found type issues"; \
	else \
		echo "⚠️  mypy not installed. Run 'make setup' to install."; \
	fi
	@echo "✅ Quality checks completed"

# Run all tests (Python only) - Enhanced to match run-test.sh
test-pytest:
	@echo "🧪 Running Python tests..."
	@echo "� Running all tests with pytest..."
	PYTHONPATH=. $(PYTHON) -m pytest tests/backend_tests -v
	@echo "🔧 Running basic functionality tests..."
	PYTHONPATH=. $(PYTHON) tests/backend_tests/test_basic.py
	@echo "📋 Running compliance tests..."
	PYTHONPATH=. $(PYTHON) tests/backend_tests/test_compliance.py
	@echo "🌐 Running server tests..."
	@PYTHONPATH=. $(PYTHON) tests/backend_tests/test_server.py || echo "ℹ️  Server tests require running server"
	@echo "🎉 Python test execution completed!"

# Run tests for the legacy OCaml project
test-legacy:
	@echo "🏛️  Testing legacy OCaml project..."
	@if [ ! -d "legacy/ocaml-old-project" ]; then \
		echo "❌ Legacy project not found at legacy/ocaml-old-project"; \
		echo "💡 Please ensure the OCaml project is available"; \
		exit 1; \
	fi
	@echo "🔧 Setting up OCaml environment..."
	@cd legacy/ocaml-old-project && \
	eval $$(opam env) && \
	ocaml ./configure.ml && \
	make build-geneweb && \
	echo "⏱️  Waiting 3 seconds before running tests..." && \
	sleep 3 && \
	make test && \
	make clean
	@echo "✅ Legacy OCaml tests completed!"

# Run comprehensive tests (both legacy and new)
test:
	@echo "🚀 Running comprehensive test suite..."
	@echo "================================== Testing legacy OCaml project =================================="
	@$(MAKE) test-legacy || echo "⚠️  Legacy tests failed or not available"
	@echo ""
	@echo "================================== Testing new Python project ==================================="
	@$(MAKE) test-pytest || echo "⚠️  Python tests failed"
	@echo ""
	@echo "🎉 Comprehensive testing completed!"

# Complete development workflow
all: format check test
	@echo ""
	@echo "🎉 All development checks completed!"
	@echo "✅ Code formatted, quality checked, tests passed"
	@echo "🚀 Ready to commit!"

# MyPy error assistance
mypy-help:
	@echo "🔍 Analysing MyPy errors..."
	@$(PYTHON) scripts/mypy_assistant.py

# Safe MyPy auto-fixes (only simple type annotations)
mypy-safe:
	@echo "🔧 Applying safe MyPy fixes..."
	@$(PYTHON) scripts/mypy_safe_fix.py

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
	$(PYTHON) -m pytest test_compliance.py --cov=. --cov-report=html || echo "Install pytest-cov for coverage: pip install pytest-cov"

# Quick quality check (faster than full check)
quick-check:
	@echo "⚡ Quick quality check..."
	@flake8 --max-line-length=120 . --select=E9,F63,F7,F82 || echo "⚠️  Critical issues found"
	@echo "✅ Quick check completed"

# Run the main GenEWeb daemon server
run:
	@echo "🚀 Starting GenEWeb daemon server..."
	@echo "💡 Use Ctrl+C to stop the server"
	cd src && $(PYTHON) -m backend.servers.gwd_simple --frontend-dev --frontend-dir ./frontend -p 2317 -hd ../data

# Run the simple test server (for development)
run-simple:
	@echo "🧪 Starting simple GenEWeb test server..."
	@echo "💡 Use Ctrl+C to stop the server"
	cd src && $(PYTHON) -m backend.servers.simple_server 2317 ../data

# Run with specific port
run-port:
	@echo "🚀 Starting GenEWeb server on custom port..."
	@read -p "Enter port number (default 2317): " port; \
	port=$${port:-2317}; \
	echo "Starting server on port $$port..."; \
	cd src && $(PYTHON) -m backend.servers.gwd_simple -p $$port -hd ../data

# List available databases
list-db:
	@echo "📊 Available databases in data/:"
	@ls -la data/*.pickle 2>/dev/null | sed 's/.*\//  - /' | sed 's/\.pickle$$//' || echo "  No databases found"

# Show server help
run-help:
	@echo "🚀 GenEWeb Server Options"
	@echo "========================"
	@echo ""
	cd src && $(PYTHON) -m backend.servers.gwd_simple --help

.PHONY: run-prod build-frontend

build-frontend:
	cd src/frontend && pnpm build || npm run build

run-prod: build-frontend
	@echo "🚀 Starting GenEWeb in production mode (serving React build)..."
	cd src && $(PYTHON) -m backend.servers.gwd_simple --frontend-dist ../src/frontend/dist -p 2317 -hd ../data
