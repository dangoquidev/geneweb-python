# Documentation Index

This file is the central index for the project's documentation. It lists the key
reference documents, their purpose, and where to find them. All docs in this
repository should be in English; legacy files in `legacy/` are preserved as an
archive and may contain French.

## How to use this index

- Read the "Getting started" section first to run the project locally.
- Follow the coding and documentation standards when contributing.
- See the Accessibility and Deployment guides before releasing to production.

## Key documents (quick links)

- [README.md](../README.md) — Project overview and quick start (top-level). Useful
  for new users and contributors.
- [CONTRIBUTING.md](../CONTRIBUTING.md) — Contributor guide and developer workflow
  (top-level). How to set up, run, test, and contribute.
- [docs/CODING_CONVENTIONS.md](./CODING_CONVENTIONS.md) — Code style and typing
  conventions (PEP 8, type hints, docstring standards, linting rules).
- [docs/DOCUMENTATION_STANDARDS.md](./DOCUMENTATION_STANDARDS.md) — Standards and
  templates for writing and updating documentation (docstring style, doc pages,
  examples).
- [docs/DEPLOYMENT.md](./DEPLOYMENT.md) — Deployment guidance and server
  configuration examples.
- [docs/DOCKER.md](./DOCKER.md) — Docker build and runtime instructions (image,
  compose, commands and troubleshooting).
- [docs/ACCESSIBILITY.md](./ACCESSIBILITY.md) — Accessibility (A11y) requirements,
  manual checks and suggested automated checks.
- [docs/LEGACY_POLICIES.md](./LEGACY_POLICIES.md) — Policies regarding legacy files
  and translations.

## Additional / developer documents

- [config/mypy.ini](../config/mypy.ini) — MyPy configuration for type checking.
- [Makefile](../Makefile) — Build/test/format/check helper targets used by
  contributors.
- [pyproject.toml](../pyproject.toml) / [requirements.txt](../requirements.txt)
  — Project packaging and dependencies.
- [tests/](../tests/) — Tests and fixtures; run with `make test`.

## Files left intentionally in other languages

- [legacy/ocaml-old-project/](../legacy/ocaml-old-project/) is a historical
  archive of the prior OCaml-based project. It contains original files and
  translations (often in French). These files are preserved in their original
  form for reference only and should **not** be modified as part of the modern
  Python project work unless explicitly requested.

## Recommended reading order for new contributors

1. `README.md` (top-level) — high-level overview and quickstart
2. `CONTRIBUTING.md` — development workflow and tests
3. `docs/CODING_CONVENTIONS.md` and `docs/DOCUMENTATION_STANDARDS.md` — rules to
   follow when editing code and docs
4. `docs/DOCKER.md` and `docs/DEPLOYMENT.md` — how to run locally and deploy
5. `docs/ACCESSIBILITY.md` — accessibility requirements to validate before
   releases

## Translation & i18n notes

- All new documentation and user-facing strings must be in English.
- For this repository we prefer a single-language English source. If you add
  localized UI text, keep translations under a dedicated `i18n/` folder and add
  a short README describing the format.

## How to contribute documentation changes

1. Follow `docs/DOCUMENTATION_STANDARDS.md` for structure and docstring format.
2. Run `make format` and `make check` locally (or `make setup` first to install
   developer tooling).
3. Add or update the doc file, and include tests or checks where relevant.
4. Open a PR describing the change and link to the doc pages affected.

## CI / local check suggestions

Recommended local sequence for doc changes:

```bash
make setup        # install dev deps (one-time)
make format       # apply formatting
make check        # lint and type-check
make test         # run tests
```

CI jobs should run the same sequence (format -> check -> test) and include a11y
validation for pages that affect the public UI.

## Contact & reporting

- Report docs issues via GitHub issues and use the label `docs`.
- For accessibility regressions, open an issue with the label `a11y` and include
  reproduction steps and a screenshot or recording.

---

_Last updated: 2025-10-26_
