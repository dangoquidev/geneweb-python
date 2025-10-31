# Backend Test Plan & QA Guide

_Last updated: 2025-10-31_

This document explains how we test the GenEWeb backend: scope, tooling, commands, fixtures, CI automation, and expectations for contributors. It complements `QUICKSTART.md` (how to run the app) and `DOCUMENTATION_STANDARDS.md` (how to write docs).

## Table of Contents

1. [Objectives](#objectives)
2. [Scope](#scope)
3. [Environments](#environments)
4. [Test Types & Suites](#test-types--suites)
5. [Test Data & Fixtures](#test-data--fixtures)
6. [Tooling & Commands](#tooling--commands)
7. [Continuous Integration](#continuous-integration)
8. [Contributor Workflow](#contributor-workflow)
9. [Adding or Updating Tests](#adding-or-updating-tests)
10. [Coverage & Quality Goals](#coverage--quality-goals)
11. [Open Improvements](#open-improvements)

## Objectives

- Guarantee core genealogy features (persons, families, search, import-export) work as expected.
- Catch regressions early through fast, automated feedback (`make check`, `make test`).
- Provide a repeatable process for contributors: how to run, where to add, what to expect.
- Document responsibilities shared between local development and CI.

## Scope

In scope for this plan:

- Python backend (FastAPI) inside `src/backend/`
- Domain models (`src/backend/core/`) and utilities (`src/backend/utils/`)
- Database adapters, repositories, and import/export flows
- Interaction between API layer and persistence using the provided sample bases

Out of scope (tracked separately):

- React frontend testing (handled in the `src/frontend/` workspace)
- Legacy OCaml project under `legacy/`
- End-to-end tests in production-like deployments

## Environments

| Environment | Purpose | Command / Location |
|-------------|---------|--------------------|
| **Local dev** | Fast feedback while coding | `make check`, `make test`, targeted `pytest ...` |
| **CI (GitHub Actions)** | Gatekeeper for PRs (`python-versions: 3.11`) | `.github/workflows/ci.yml` |
| **Docker build** | Smoke validation of packaged backend | `docker build -f Dockerfile --tag geneweb-python:ci .` (run in CI) |

Python 3.12 is the default locally; CI enforces 3.11 to match deployment constraints. Keep compatibility with both.

## Test Types & Suites

All backend tests live in `tests/backend_tests/`.

| Suite / Module | Description |
|----------------|-------------|
| `core/` | Pure domain unit tests (e.g., `test_models.py`, date calculations, events). |
| `database/` | Repository and driver tests (pickle driver, migrations, metadata). |
| `api/` | FastAPI integration tests using `TestClient`/`httpx` with realistic routes and auth checks. |
| `parsers/` | GEDCOM/GeneWeb parsing logic, line/token handling. |
| `services/` | Business services (person, family, search, database lifecycle). |
| `utils/` | Helpers such as string normalization and date utilities. |
| `test_api_database.py`, `test_gedcom_import_integration.py` | Higher-level workflows combining services and IO. |

### Categorisation

- **Unit tests**: fast, isolated, pure Python (core, utils).
- **Integration tests**: exercise multiple layers (API, services, database repositories).
- **Regression scenarios**: complex import/export flows using reference data (`test_gedcom_import_integration`).
- **Edge cases**: validation, error handling, unusual characters/dates.

## Test Data & Fixtures

| Resource | Location | Purpose |
|----------|----------|---------|
| Pytest configuration | `tests/conftest.py` | Adds `src/` to `PYTHONPATH` so tests can import backend modules without installing the package. |
| Sample genealogical datasets | `data/*.pickle`, `data/*.gw`, `data/*.ged` | Realistic fixtures reused across import/export and repository tests. |
| Lightweight GEDCOM fixtures | `tests/fixtures/test_family.ged`, `tests/fixtures/simple_family.gw` | Targeted scenarios for parser tests. |

When adding new fixtures, keep them small (<200 KB) and document usage near the test file.

## Tooling & Commands

### One-shot commands

| Command | Description |
|---------|-------------|
| `make test` | Runs the full backend test suite (`pytest tests/backend_tests/`). |
| `make test-api` | Focuses on API integration tests (`pytest tests/backend_tests/api`). |
| `make check` | Formatting (`black`, `isort`, `autoflake`), lint (`flake8`), typing (`mypy`). |
| `make all` | Runs formatters, linters, and tests sequentially. |
| `pytest tests/backend_tests/services -k duplicates` | Example targeted run (service tests with `duplicates` keyword). |

### Optional extras

- Run with coverage: `pytest --cov=src/backend --cov-report=term-missing`
- Re-run failed tests quickly: `pytest --last-failed`
- Drop into debugger: `pytest -k test_case --pdb`

All commands assume dependencies installed via `make setup` (which calls `pip install -r requirements.txt`).

## Continuous Integration

GitHub Actions workflow: `.github/workflows/ci.yml`

1. **Lint & Type Check**
   - `pip install -r requirements.txt`
   - `make check`
2. **Tests**
   - `pip install -r requirements.txt`
   - `make test`
3. **Docker Build**
   - Build backend image to detect packaging regressions

Every push and pull request to `main` runs the pipeline. Squash commits should be green before merging.

## Contributor Workflow

1. **Set up environment**
   ```bash
   make setup
   ```
2. **Run checks before committing**
   ```bash
   make check
   make test
   ```
3. **Targeted development loop**
   - Run the specific pytest target relevant to your change.
   - Use `-vv` for verbose output when debugging failures.
4. **Before pushing**
   - Ensure both linting and tests pass locally.
   - Update documentation or fixtures if behaviour changes.
5. **During code review**
   - Reference failing tests in PR description if applicable.
   - Share reproduction commands when reporting regressions.

## Adding or Updating Tests

- Place new unit tests beside the module focus (`tests/backend_tests/<area>/`).
- Prefer descriptive test names (`test_create_family_with_invalid_children`).
- Use existing helper factories where possible; avoid duplicated setup code.
- Keep each test self-contained; rely on sample data rather than global state.
- For new API endpoints:
  1. Add schema tests (Pydantic model validation).
  2. Add route tests in `api/` using `TestClient` with realistic payloads.
  3. Cover error paths (4xx/5xx) and success paths.
- When fixtures grow complex, document them inline and in this file if they become shared.

## Coverage & Quality Goals

- **Functional coverage**: All domain objects (person, family, events) must have unit tests for happy path and validation errors.
- **Regression coverage**: Import/export tests must continue to run against real sample datasets.
- **Edge cases**: Non-ASCII characters, unusual date formats, duplicate detection are mandatory scenarios.
- **Performance**: API pagination and search tests prevent O(n²) regressions by asserting response sizes and timings (when applicable).
- **Acceptance gate**: CI must stay green; no skipped tests without justification.

Future target: maintain at least 80% module coverage (tracked manually for now). Consider enabling `pytest-cov` in CI once stable.

## Open Improvements

- [ ] Add automatic coverage reporting (`pytest --cov`) in CI.
- [ ] Introduce contract tests for external export formats on larger datasets.
- [ ] Add negative-path smoke tests for authentication-protected routes when auth is available.
- [ ] Document frontend testing strategy (separate effort).

Contributions welcome—update this plan whenever the testing approach evolves.
