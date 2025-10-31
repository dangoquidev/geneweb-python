# Contributing to GenEWeb (Python)

Welcome — thank you for contributing! This document explains how to get started, which
conventions to follow, and where the project's canonical documentation is located.

## Quick facts

- Modern server (recommended): `run_api.py` (FastAPI) — use `make run`.
- The `legacy/ocaml-old-project` folder is a historical archive (read-only).
- Primary documentation lives in the `docs/` directory (see the docs index).

## Quick start

```bash
git clone <repository-url>
cd Awkward_legacy
make setup
make run        # starts the modern server (FastAPI)
make all        # format -> check -> test
```

## Essential documentation

- `docs/CODING_CONVENTIONS.md` — code conventions (PEP 8, typing, docstrings)
- `docs/DOCUMENTATION_STANDARDS.md` — documentation standards and templates
- `README.md` — project overview and quickstart

## Development workflow

- Format: `make format`
- Checks (type/style): `make check`
- Tests: `make test`
- All-in-one: `make all`

## Testing and best practices

- Tests should follow the arrange / act / assert pattern.
- Test locations: `tests/`, `tests/backend_tests/`.
- Add Google-style docstrings and type annotations for all public APIs.

## Errors and exceptions

- Use dedicated exception classes (for example `DatabaseError`, `GenEWebError`) to
	provide clear, actionable error messages without leaking sensitive data.

## Notes about legacy references

Older documentation may mention legacy modules (for example `gwd_simple.py` or
`template_engine.py`). Those references are historical; rely on the modern API
and update any documentation that still points to removed modules.

---

Thank you for your contribution!
