# GenEWeb Python - Development Makefile
# Simple, standard, and efficient development workflow

# Detect Python command (prefer python3, fallback to python)
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null || echo "python")

# Check if Python is available
ifeq ($(shell command -v $(PYTHON) 2> /dev/null),)
$(error Python is not installed or not in PATH. Please install Python 3.6+ and try again)
endif

.PHONY: help format check test all setup clean status install run run-dev run-api run-legacy run-simple run-admin run-both run-admin-help run-fullstack run-fullstack-tmux stop-fullstack

# Default target shows help
help:
	@echo "🚀 GenEWeb Python Development"
	@echo "=============================="
	@echo ""
	@echo "Available commands:"
	@echo "  make run             - Start REST API server (port 8000)"
	@echo "  make run-dev         - Start REST API with auto-reload"
	@echo "  make run-fullstack   - Start API + Frontend (manual)"
	@echo "  make run-fullstack-tmux - Start API + Frontend (tmux)"
	@echo "  make stop-fullstack  - Stop all tmux sessions"
	@echo "  make run-api         - Start REST API with custom port/database"
	@echo "  make run-legacy      - Start legacy daemon server (port 2317)"
	@echo "  make run-admin       - Start GenEWeb admin panel (port 2316)"
	@echo "  make run-both        - Start both server and admin panel"
	@echo "  make run-simple      - Start simple test server (databases in data/)"
	@echo "  make setup           - Setup development environment"
	@echo "  make setup-frontend  - Install frontend dependencies"
	@echo "  make create-frontend - Create new React frontend project"
	@echo "  make format          - Format code with black and isort + auto-fixes"
	@echo "  make autofix         - Auto-fix common style issues only"
	@echo "  make check           - Run quality checks (flake8, mypy)"
	@echo "  make mypy-help       - Get assistance with MyPy errors"
	@echo "  make mypy-safe       - Auto-fix SAFE MyPy errors only"
	@echo "  make test            - Run all test suites"
	@echo "  make all             - Complete workflow (format + check + test)"
	@echo "  make status          - Show project status"
	@echo "  make list-db         - List available databases"
	@echo "  make run-help        - Show server options"
	@echo "  make run-admin-help  - Show admin panel options"
	@echo "  make clean           - Clean generated files and caches"
	@echo "  make install         - Install package in development mode"
	@echo ""
	@echo "🆕 Modern REST API:"
	@echo "  make run             → API only: http://127.0.0.1:8000/api/docs"
	@echo "  make run-fullstack   → API + Frontend React (2 terminals needed)"
	@echo "  make run-fullstack-tmux → API + Frontend (automatic with tmux)"
	@echo ""
	@echo "Quick start: make setup && make run"
	@echo "Full-stack: make run-fullstack-tmux (requires tmux)"

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

# Run all tests
test:
	@echo "🧪 Running tests..."
	@echo "📋 Running backend tests..."
	PYTHONPATH=src $(PYTHON) -m pytest tests/backend_tests/ -v
	@echo "🎉 Test execution completed!"

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

# Run the main GenEWeb daemon server (legacy)
run-legacy:
	@echo "🚀 Starting GenEWeb daemon server (legacy)..."
	@echo "💡 Use Ctrl+C to stop the server"
	cd src && $(PYTHON) -m backend.servers.gwd_simple --frontend-dev --frontend-dir ./frontend -p 2317 -hd ../data

# Run the modern REST API server (recommended)
run:
	@echo "🚀 Starting GenEWeb..."
	@echo ""
	$(PYTHON) run_api.py --port 8000 --db data/showcase.pickle --debug

# Run the REST API with auto-reload (development)
run-dev:
	@echo "🚀 Starting GenEWeb with auto-reload..."
	@echo ""
	$(PYTHON) run_api.py --port 8000 --db data/showcase.pickle --debug --reload

# Run API + Frontend React (full-stack)
run-fullstack:
	@echo "🚀 Starting GenEWeb Full-Stack (API + Frontend)..."
	@echo ""
	@echo "⚠️  This requires two terminals:"
	@echo "   Terminal 1: API Server (starting now...)"
	@echo "   Terminal 2: Frontend Dev Server"
	@echo ""
	@echo "To start frontend manually, run in another terminal:"
	@echo "   cd src/frontend && pnpm dev"
	@echo ""
	@echo "Or use tmux/screen to run both:"
	@echo "   make run-fullstack-tmux"
	@echo ""
	@$(PYTHON) run_api.py --port 8000 --db data/showcase.pickle --debug

# Run full-stack with tmux (API + Frontend)
run-fullstack-tmux:
	@echo "� Starting GenEWeb Full-Stack with tmux..."
	@command -v tmux >/dev/null 2>&1 || { echo "❌ tmux not installed. Install with: sudo apt install tmux"; exit 1; }
	@tmux new-session -d -s geneweb-api "cd $(PWD) && $(PYTHON) run_api.py --port 8000 --db data/showcase.pickle --debug"
	@if [ -d "src/frontend" ] && [ -f "src/frontend/package.json" ]; then \
		tmux new-session -d -s geneweb-frontend "cd $(PWD)/src/frontend && pnpm dev"; \
		echo "✅ Started API (port 8000) and Frontend in tmux sessions"; \
		echo ""; \
		echo "� Commands:"; \
		echo "   tmux attach -t geneweb-api      # View API logs"; \
		echo "   tmux attach -t geneweb-frontend # View Frontend logs"; \
		echo "   tmux kill-session -t geneweb-api"; \
		echo "   tmux kill-session -t geneweb-frontend"; \
		echo ""; \
		echo "🌐 Access:"; \
		echo "   API: http://127.0.0.1:8000/api/docs"; \
		echo "   Frontend: http://localhost:5173 (or 3000)"; \
	else \
		echo "⚠️  Frontend not found in src/frontend"; \
		echo "   API started at http://127.0.0.1:8000/api/docs"; \
	fi

# Stop all tmux sessions
stop-fullstack:
	@echo "🛑 Stopping GenEWeb sessions..."
	@tmux kill-session -t geneweb-api 2>/dev/null || true
	@tmux kill-session -t geneweb-frontend 2>/dev/null || true
	@echo "✅ All sessions stopped"

# Run the REST API on custom port and database
run-api:
	@read -p "Enter port number (default 8000): " port; \
	read -p "Enter database path (default data/showcase.pickle): " db; \
	port=$${port:-8000}; \
	db=$${db:-data/showcase.pickle}; \
	echo "🚀 Starting API on port $$port with database $$db..."; \
	$(PYTHON) run_api.py --port $$port --db $$db --debug

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

# Run the GenEWeb admin panel
run-admin:
	@echo "⚙️  Starting GenEWeb Admin Panel..."
	@echo "💡 Use Ctrl+C to stop the admin server"
	@echo "🌐 Admin panel will be available at: http://localhost:2316/"
	$(PYTHON) -m src.backend.servers.admin.admin_main -p 2316 -gwd_p 2317 -bd data

# Run both server and admin panel (requires terminal multiplexer or separate terminals)
run-both:
	@echo "🚀 Starting both GenEWeb server and admin panel..."
	@echo ""
	@echo "⚠️  This requires two separate terminals:"
	@echo "   Terminal 1: make run"
	@echo "   Terminal 2: make run-admin"
	@echo ""
	@echo "Or use a terminal multiplexer like tmux:"
	@echo "   tmux new-session -d -s geneweb-server 'make run'"
	@echo "   tmux new-session -d -s geneweb-admin 'make run-admin'"
	@echo ""
	@echo "Starting server first (you'll need to open another terminal for admin)..."
	@$(MAKE) run

# Show admin panel help
run-admin-help:
	@echo "⚙️  GenEWeb Admin Panel Options"
	@echo "==============================="
	@echo ""
	$(PYTHON) -m src.backend.servers.admin.admin_main --help

# Run admin panel with custom port
run-admin-port:
	@echo "⚙️  Starting GenEWeb admin panel on custom port..."
	@read -p "Enter admin port number (default 2316): " port; \
	@read -p "Enter main server port number (default 2317): " gwd_port; \
	port=$${port:-2316}; \
	gwd_port=$${gwd_port:-2317}; \
	echo "Starting admin panel on port $$port (main server: $$gwd_port)..."; \
	$(PYTHON) -m src.backend.servers.admin.admin_main -p $$port -gwd_p $$gwd_port -bd data

.PHONY: run-prod build-frontend run-admin-port

build-frontend:
	cd src/frontend && pnpm build || npm run build

run-prod: build-frontend
	@echo "🚀 Starting GenEWeb in production mode (serving React build)..."
	cd src && $(PYTHON) -m backend.servers.gwd_simple --frontend-dist ../src/frontend/dist -p 2317 -hd ../data
