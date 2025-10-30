# Legacy (OCaml) Policy and Prioritization

This document describes the project's policy and priorities regarding the
legacy OCaml codebase stored under `legacy/ocaml-old-project/`. It explains why
those files are preserved, how contributors should treat them, and the approved
paths for migration, bug fixes, or reference usage.

Status summary

- The `legacy/ocaml-old-project/` directory is an archival snapshot. It is:
  - Read-only reference material for historical behaviour and algorithms.
  - Not part of the active Python runtime or packaging.
  - Not to be modified as part of normal Python development work.

Purpose and guiding principles

1. Preserve the historical oracle. The OCaml project is the behavioural
   reference (oracle) for the Python reimplementation. Tests and specifications
   may rely on the legacy project to verify parity, but we do not re-import any
   OCaml code into the Python project.

2. Minimise risk to ongoing development. The modern project (Python, FastAPI,
   frontend) is the active codebase. Direct edits to legacy files risk
   accidental regression of historical artifacts or legal/licensing context.

3. Keep the archive discoverable. The legacy tree should remain searchable and
   documented so contributors can consult the original logic, examples and
   textual artifacts when implementing or testing behaviour.

Technology decisions: OCaml → Python, raw HTML → React

This project intentionally moves the active implementation from the historical
OCaml codebase to a modern Python stack (FastAPI) and replaces raw HTML
templates with a React-based frontend in selected areas. The reasons below are
meant to explain and justify that strategic choice and to provide guidance for
contributors who need to make design or migration decisions.

Why Python (instead of continuing in OCaml)

- Ecosystem and maintainability: Python has a large, active ecosystem for web
  development (FastAPI, testing, async tooling) and a wider pool of
  contributors and maintainers familiar with the language. This reduces
  bus-factor risk and improves onboarding speed.
- Interoperability: Python integrates well with modern deployment and testing
  tools (Docker, CI, typed checks with MyPy) and with data tooling used by
  the project (serialization formats, ORM/database drivers where applicable).
- Developer productivity: For many contributors, Python offers faster
  iteration, more available libraries, and simpler packaging compared to the
  constraints of the legacy OCaml toolchain.
- Testability and parity: Writing language-agnostic specification tests in
  Python makes it straightforward to assert parity with legacy behaviour while
  keeping the implementation idiomatic for Python.

Why React (instead of raw HTML templates)

- Developer experience: React provides componentization, better state
  management and a testable UI model. This makes it easier to implement
  complex interactions (search, client routing, progressive enhancement) that
  are harder to manage with scattered raw HTML templates.
- Maintainability: Components and typed props (via TypeScript) encourage
  predictable interfaces and smaller, reusable UI units. This reduces UI
  duplication and makes accessibility improvements easier to apply
  consistently.
- Tooling and testing: React ecosystems (Jest, Playwright, RTL) offer strong
  tools for unit and end-to-end testing of UI behaviour. This helps ensure
  parity with legacy features while enabling incremental refactors.

Trade-offs and mitigations

- Performance: OCaml can have performance and footprint advantages for some
  workloads. We mitigate this by benchmarking critical paths (profile the
  Python app and add caching, worker processes, or native extensions only
  where required).
- Semantic parity risk: Re-implementations can introduce subtle behaviour
  drift. Mitigation: specification-first development, acceptance tests that
  use legacy outputs as an oracle, and a test matrix that includes canonical
  legacy fixtures.
- Developer skill variance: Not all contributors know React/TypeScript. Mitigate
  by documenting component patterns, providing small examples, and preferring
  simple components where possible.

Compatibility notes (UI & API)

- Backwards compatibility: The Python API should keep stable endpoints for a
  reasonable deprecation window. Where endpoint shapes change, provide clear
  migration notes in `docs/DEPLOYMENT.md` and the OpenAPI spec (`/api/docs`).
- Frontend transitions: Replace the UI incrementally. Keep server-side HTML
  fallbacks or provide graceful degradation for pages that have not yet been
  migrated to React. Feature flags can help toggle new UI components safely.

Testing, parity and validation

- Use legacy outputs as an oracle: add canonical input fixtures and expected
  outputs into `tests/fixtures/legacy/` so CI can assert parity without running
  legacy toolchains.
- Add integration tests that exercise the full stack: backend → API →
  frontend (using headless browsers) to avoid regressions during UI migration.
- Maintain a small suite of golden tests that compare current outputs to
  recorded legacy outputs; keep the golden files under `tests/legacy_golden/`.

Migration pattern and recommended steps

1. Specification: write a concise specification or acceptance test describing
   the feature's expected behaviour (edge cases included).
2. Fixture capture: add canonical input(s) and expected output(s) from the
   legacy code into `tests/fixtures/legacy/`.
3. Implement a minimal Python API that satisfies the spec and tests.
4. Incrementally replace UI: create a small React component and a wrapper page
   that mirrors legacy behaviour, add UI tests, then replace progressively.
5. Deprecation: once a page or endpoint is fully covered by tests and the new
   stack, mark legacy behaviour as deprecated and schedule archive-only
   clean-up in the long-term roadmap.

Accessibility & UX improvements

- Migration is an opportunity to improve accessibility. Adopt the project's
  `docs/ACCESSIBILITY.md` checklist for new components (focus management,
  ARIA roles, keyboard navigation, color contrast).
- Use automated a11y checks (Playwright + axe) in CI for pages that change.

Operational & deployment considerations

- Packaging: prefer container-first deployment (Docker) and document runtime
  parameters in `docs/DOCKER.md` so the operations team can tune resources.
- Monitoring: add health endpoints, metrics, and traces for the Python app so
  that performance regressions can be detected early.

When to consider reverting or embedding OCaml

- Reintroduction of OCaml code is discouraged. If an absolute performance or
  feature case demands OCaml, prefer isolating it behind a well-documented
  service boundary (separate process or microservice) and keep the main
  product in Python. Any such plan must go through maintainer and legal
  review.

Scope — what this policy covers

- Files and locations: everything under `legacy/ocaml-old-project/`.
- Exceptions: small metadata edits that improve clarity without changing code
  semantics (for example: adding a README note clarifying the archive is
  historical) MAY be made after approval from project maintainers.

What is NOT allowed (default rule)

- Do not translate, refactor or port files inside `legacy/ocaml-old-project/`
  as part of day-to-day Python project work.
- Do not run a build, packaging or tests that modify the legacy tree as part of
  CI for the Python project.
- Do not treat the legacy code as a library dependency; the Python rewrite must
  be independent and well-tested.

Permitted interactions and workflows

1. Read-only reference
   - Developers may consult legacy code as an oracle when:
     - Writing tests asserting parity with historical behaviour.
     - Implementing an algorithm that is not yet specified elsewhere.
   - When using legacy code as reference, record the source location in the
     test or code comment (file path + line range + short explanation).

2. Documentation or metadata clarifications (low-risk)
   - Minor README or doc updates inside `legacy/` that make the archive easier
     to navigate (for example: index files, metadata about the archive locale)
     can be applied. These are limited to non-executable text and require a
     maintainer review.

3. Critical security fixes (rare)
   - If the legacy project contains an actionable security vulnerability that
     affects the maintained Python project (for example, a packaged binary or
     published asset), escalate to maintainers. Any fix in `legacy/` requires
     explicit approval and a clear changelog entry. The preferred approach is:
     - Fix the vulnerability in the Python project (if applicable) and note the
       historical artifact in `legacy/` rather than editing legacy sources.

Priority matrix for changes

- Priority A — Blocker / Security: Fix or mitigation required. May trigger a
  sanctioned change in `legacy/` only after team approval.
- Priority B — Behavioural parity tests: Add tests in the Python repo with
  references to legacy files as the oracle. No legacy edits required.
- Priority C — Documentation / metadata clarity: Small updates allowed with
  maintainer review (for example an index file or an explicit "archive"
  notice). These are low risk.
- Priority D — Feature changes or refactors: Not permitted in `legacy/`.

Migration paths and recommended approach

We keep the legacy project as historical reference. Preferred migration paths are
as follows:

1. Specification-first: Extract behaviour from legacy tests or examples and
   write small, language-agnostic specification (examples + acceptance tests)
   in the Python repo. Use unit/integration tests that refer to those
   specifications.

2. Test-driven parity: For any feature that must match historical behaviour,
   write tests that assert behaviour against the legacy oracle (compare outputs
   for canonical inputs). Keep the tests and the sample inputs in `tests/` and
   point to the legacy source file in the test comments.

3. Re-implementation: Implement the functionality in Python, guided by the
   tests and spec. Ensure tests pass and add new tests that cover edge cases.

4. Documentation: Update the docs in `docs/` to explain known behavioural
   differences, compatibility notes, and migration guidance.

Translation & localization (legacy content)

- The legacy archive contains French text and localization artifacts. We do NOT
  translate archive files as part of normal Python project work.
- If a specific legacy text must be translated for documentation or tests,
  copy the short snippet into `docs/` or `tests/fixtures/` and provide an
  English translation there; do not change the original file in `legacy/`.

CI, testing and the legacy oracle

- Tests that assert parity with legacy behaviour should live in `tests/` and
  be automated under `make test`.
- Tests may refer to legacy files as an oracle, but they must copy any input
  fixtures needed into `tests/fixtures/` so CI runs reproducibly without
  depending on `legacy/` tooling.

Legal, licensing and attribution

- The legacy tree may include original licensing and attribution files. Do not
  remove or alter licensing information in `legacy/` without legal approval.
- When reusing algorithms or documented behaviour, ensure attribution stays in
  the relevant Python module or tests if required by the license.

Exception process (how to request changes to legacy)

1. Open an issue describing the change, motivation, and impact.
2. Provide an implementation plan and a minimal patch if possible.
3. Tag the issue `legacy` and `maintainer-review`.
4. A maintainer will review and either:
   - Approve a documentation-only change, or
   - Escalate for legal/technical review for code changes.

Maintenance checklist for reviewers

- Is the proposed change documentation-only (non-executable)? If yes, prefer
  adding a small README in `legacy/` rather than changing historic files.
- Does the change alter executable code in `legacy/`? If yes, require a strong
  rationale and maintainer sign-off.
- Is there an accompanying test or specification in the Python repo that
  validates parity? If not, ask the contributor to add one.

Risks and mitigations

- Risk: accidental drift of legacy tree into active development.
  - Mitigation: default read-only policy and required exception process.
- Risk: contributors rely on untranslated legacy content.
  - Mitigation: encourage copying small, relevant excerpts into `docs/` or
    `tests/fixtures/` with English translations.
- Risk: hidden licensing concerns.
  - Mitigation: require legal/maintainer review before changing legacy files.

Open questions & recommended next steps

- Option: add a small `legacy/README.md` index that lists high-value files and
  their purpose (non-intrusive). This is low-risk and helps navigation.
- Option: create `docs/LEGACY_EXTRACTS.md` that provides English summaries of
  commonly referenced legacy algorithms and pointers to tests that exercise
  them.

Decision record (short)

- Keep `legacy/ocaml-old-project/` as a read-only historical archive.
- Use legacy sources only as an oracle and copy small excerpts into the Python
  repo (docs/tests) when necessary, with English translations.
- Only allow edits to `legacy/` after a formal issue and maintainer
  approval; avoid reintroducing OCaml code into the active Python codebase.

Contact

- For legacy-related proposals: open an issue and tag `legacy`.

_Last updated: 2025-10-31_
