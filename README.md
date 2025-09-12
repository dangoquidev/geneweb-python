# GenEWeb (Python modernization) – Awkward_legacy

Modernized Python implementation of the historical GenEWeb server with a React + TypeScript frontend.

- Backend: Python 3, file-based pickle database driver, HTTP endpoints for search and statistics
- Frontend: React + Vite + Tailwind + shadcn/ui, minimal routing, statistics visualizations

## Project structure

```
src/
  backend/        # Python GenEWeb server and DB driver
  frontend/       # React frontend (Vite)
data/             # Example pickle databases (*.pickle)
scripts/          # Data conversion tools (GED ⇄ JSON ⇄ pickle)
```

## Prerequisites

- Python 3.11+
- Node.js 18+ with pnpm or npm (for frontend build)

## Quick start (development)

Use the Makefile targets. From the project root:

```
make setup       # one-time: install backend deps and dev tools
make run         # start backend server with frontend served from src/frontend (dev mode)
```

The server runs on port 2317 by default. Place your databases under `data/` (e.g., `data/showcase.pickle`).

Open:
- Backend+Frontend: http://localhost:2317/

## Makefile targets

- make run: Start the main GenEWeb server (serves the frontend in dev mode)
- make run-simple: Start a simple test server (backend only)
- make run-prod: Build the frontend and serve its static dist from the Python server
- make build-frontend: Build the frontend only (uses pnpm or npm)
- make list-db: List available databases under data/
- make setup: Install backend in editable mode plus dev tools
- make format, make check, make test, make all: Standard quality workflow
- make clean: Remove caches and build artifacts

## Data preparation

The backend uses a simple pickle-based database with persons and families.

Convert a GEDCOM to JSON:
```
python3 scripts/ged_to_json.py --input your.ged --output data/ged.json
```

Convert JSON to pickle (includes persons and families):
```
python3 scripts/json_to_geneweb_pickle.py --input data/ged.json --output data/ged.pickle
```

Then run:
```
make list-db
make run
```

## Frontend overview

- Search view: free-text search of persons
- Statistics view: latest births/deaths/marriages, oldest people/couples, longest-lived, population pyramid
- Results rendering adapts automatically to person-based vs couple-based data

Development (optional):
```
cd src/frontend
pnpm install
pnpm dev
```
(In dev mode, the Python server can proxy or you can use the built frontend served by `make run`.)

## Backend endpoints (high-level)

- GET /api/{base}/search?q=... → persons list
- GET /api/{base}/statistics/{type} → data for the given statistic type
  - Types include: latest-births, latest-deaths, latest-marriages, oldest-couples, oldest-people, longest-lived, population-pyramid

## Testing

```
make test
```

Includes compliance and basic server tests. Some server tests require the server to be running.

## License and attribution

This project modernizes components of GenEWeb (c) 1998-2007 INRIA. See repository metadata for details.
