# Security & GDPR Guide

_Last updated: 2025-10-31_

This document summarizes the security practices that apply to the modernized GenEWeb backend and highlights the main GDPR requirements. It complements the deployment recommendations (`docs/DEPLOYMENT.md`) and the test plan (`docs/TEST_PLAN.md`).

## 1. Objectives

- Protect genealogical data (potentially sensitive) from leaks or tampering.
- Ensure compliance with GDPR principles: lawfulness, transparency, data minimization, storage limitation, security.
- Provide a best-practice framework for contributors and deployments.

## 2. Current technical baseline

| Area | Current state |
|------|---------------|
| **Framework** | FastAPI + Uvicorn (ASGI) with custom error handlers. |
| **Validation** | Pydantic schemas and dedicated exceptions (`ValidationError`, `DatabaseError`, etc.). |
| **CORS** | Permissive policy in debug, restricted to local origins in production. |
| **Data** | Pickle/GeneWeb/GEDCOM files stored locally (`data/`). |
| **CI/CD** | GitHub Actions: lint, mypy, tests, Docker build to prevent regressions. |
| **Logs** | Minimal logs (no sensitive data), rotation handled via Docker (see `docs/DEPLOYMENT.md`). |

## 3. Application-level best practices

### 3.1 Authentication & Authorization
- Keep public APIs separate from administrative operations.
- Plan for an identity provider integration (OIDC, JWT) for multi-user deployments.
- Enforce HTTPS and secure session handling on the frontend (`HttpOnly` cookies, anti-CSRF).

### 3.2 Input validation & handling
- Always use Pydantic models for serialization/deserialization.
- Stay alert to common attacks: injection, limit overruns (pagination, file upload sizes).
- Return actionable yet concise error messages (avoid exposing stack traces in production).

### 3.3 Error handling & logging
- `register_error_handlers` ensures standardized JSON responses.
- Do not log personal data or secrets.
- Use appropriate log levels: DEBUG locally, INFO/ERROR in production.

### 3.4 Dependencies & code
- Check dependencies with `pip-audit` or `pipenv check` before releases.
- Keep `requirements.txt` versions up to date (CI tests act as guardrails).
- Review scripts in `scripts/` regularly to avoid leaking secrets.

### 3.5 File security
- Restrict permissions on the `data/` directory (chmod 750) and backups.
- Provide at-rest encryption (encrypted filesystem or tar.gz + GPG) for backups containing personal data.
- Monitor the size and structure of imported files to prevent malicious payloads.

## 4. Infrastructure best practices

- **HTTPS is mandatory** behind a reverse proxy (nginx, Traefik) with up-to-date certificates.
- **Firewall / Security Groups**: expose only required public ports (80/443) and restrict 8080.
- **Isolation**: run the application in a dedicated container with a non-root user.
- **Backups**: automated and encrypted, with rotation (see the script example in `docs/DEPLOYMENT.md`).
- **Monitoring**: healthcheck `/api/health`, alerts for prolonged downtime.
- **Updates**: apply OS, Python, and dependency patches regularly.

## 5. GDPR: key obligations

| Principle | Recommended actions |
|-----------|---------------------|
| **Lawfulness & transparency** | Document the purpose of data collection (family genealogy), obtain consent when necessary. |
| **Data minimization** | Store only the necessary attributes (limit free-form notes, anonymize when possible). |
| **Accuracy** | Provide workflows to correct/delete inaccurate data upon request. |
| **Storage limitation** | Define an archiving/deletion policy after periods of inactivity. |
| **Security** | Implement the measures listed above (auth, encryption, secure backups). |
| **Traceability** | Keep a log of critical operations (import/export, deletion) without storing sensitive information. |
| **Data subject rights** | Offer mechanisms to handle access, rectification, objection, and erasure requests. |

### Records & documentation
- Maintain a processing register describing controllers, legal bases, and data flows (including third-party sharing).
- Appoint a DPO (Data Protection Officer) when required by the project size/scope.
- Document subcontractors (hosting, third-party tools) in the Terms of Service.

### Incident procedures
- Implement a breach notification process within 72 hours.
- Run disaster recovery simulations at least once a year.

## 6. Recommended controls

| Frequency | Control |
|-----------|---------|
| **Each PR** | `make check`, `make test`, security-focused code review, verify new dependencies. |
| **Monthly** | Vulnerability scans (`pip-audit`, `npm audit` for the frontend), log review, secret rotation. |
| **Quarterly** | Access review (system accounts, API keys), backup restoration tests, update the GDPR register. |
| **Annually** | Full audit (light pentest, infrastructure configuration review), update security policy and legal notices. |

## 7. Improvement ideas

- Add a modern authentication module (JWT/OAuth2) with granular roles and permissions.
- Integrate automated scans (SAST/DAST) into CI (Bandit, Trivy, OWASP ZAP headless).
- Provide an automated encryption script for GEDCOM exports.
- Deploy centralized logging (ELK, Loki + Grafana) with alerts on critical events.
- Implement secure E2E tests (security headers, Content Security Policy, etc.).

---
_For security questions or incidents: open a GitHub issue (label `security`) and notify the project maintainers._
