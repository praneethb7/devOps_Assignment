# Security scan record

[Successful delivery run](https://github.com/praneethb7/devOps_Assignment/actions/runs/38868966201) · commit `82ec393528fe2e5d30861af71c05fa104e8929f0`.

Trivy scanned both container images, including their operating-system packages and Python dependencies, and the workflow fails on any HIGH or CRITICAL finding. The final Alpine-based images passed that gate with zero findings at those severities; the raw reports are in [backend](../evidence/security-backend/trivy-backend.txt) and [frontend](../evidence/security-frontend/trivy-frontend.txt). A clean report describes the scanner database and packages at that run; it does not guarantee that future vulnerabilities or application logic flaws do not exist.

## Finding and remediation

The earlier Debian 13.7 backend image was blocked with 44 HIGH/CRITICAL OS-package findings; the Python package section was clean. One reported finding was `CVE-2025-69720` in `ncurses-base`/`ncurses-bin`, described by the scanner as a buffer-overflow vulnerability. Several util-linux findings had no fixed package version in that report, so merely reinstalling application dependencies would not fix the base-image exposure.

The backend was rebuilt on `python:3.12-alpine`, retaining a non-root UID, the migration tooling and the same application tests. The gate remained configured with `exit-code: 1`, `severity: HIGH,CRITICAL` and `ignore-unfixed: false`; no CVE allowlist or scan bypass was added. The subsequent run passed both image scans and the deployed application smoke test.

## Controls and boundaries

- Application runtimes use non-root users. Kubernetes disables privilege escalation and drops capabilities.
- Secrets are generated locally and referenced through Kubernetes Secrets. The local `.env` and Terraform state/variable files are ignored.
- Database is internal to Compose/Kubernetes; the browser calls same-origin `/api` paths.
- Input validation bounds quantities and text, validates enum values and requires timezone-aware future due dates.
- PostgreSQL row locking serializes stock allocation; conflict responses preserve stock and loan history.
- CI uses read-only repository access except for the image-publishing jobs, which need `packages: write`.

This is a classroom administrator application without authentication, authorization, public TLS, rate limiting or production backups. Keep the demo on loopback/trusted networks. Public use would require those controls and a managed secret/backup policy. Kubernetes Secrets are base64 encoded and require cluster RBAC/encryption controls for a production installation.
