# Verification record — 16 October 2026

## Completed

- 15 API tests passed locally with **90% overall statement coverage** (99% for the core API modules; optional sample-data script included in the overall figure). The production DB is not used by tests.
- CI tests passed against isolated PostgreSQL, with Ruff checks and Alembic upgrade/check/downgrade/upgrade.
- React production build passed. Browser interactions created equipment, borrowed a unit and returned it with correct availability changes.
- Both Docker images built. Compose PostgreSQL, backend and frontend reported healthy; migration container exited successfully.
- `helm lint` passed; Helm installed and upgraded CampusCrate on Minikube. Frontend ran two replicas; backend ran two initially and scaled to five; PostgreSQL ran as a StatefulSet with PVC.
- Browser reached the application through `campuscrate.localhost:8088`, routed by the NGINX Ingress controller.
- A deployed smoke test exercised inventory creation, borrowing, return, update and aggregate consistency through the frontend proxy and through Ingress.
- Prometheus targets showed backend replicas UP; Grafana showed populated request-rate, latency and per-route panels.
- HPA emitted a `SuccessfulRescale` event from two to five backend replicas. A 180-second demo load recorded 18,952 successful responses and 4 request errors while scaling; this was a functional scaling demonstration, not a zero-error performance benchmark.
- Isolated missing-image and wrong-Service-selector exercises were applied, inspected and removed; the working application was preserved.
- Terraform initialized and validated. Mock-provider plan tests passed; no AWS resources were created.
- Complete GitHub Actions run succeeded: [38868966201](https://github.com/praneethb7/devOps_Assignment/actions/runs/38868966201). Both image security gates passed, both SHA-tagged images were published and Helm deployment plus smoke tests passed on kind.

## Evidence interpretation

Browser images are actual browser screenshots. `.txt` files are command output captures. `pipeline.json` records actual GitHub job metadata. Trivy reports are downloaded from the successful pipeline artifacts. HPA screenshots/captures refer to the explicitly documented lower CPU-request demo values. Sample data is opt-in demonstration data, including one deliberately overdue loan.

## Limitations

Real AWS plan/apply/destroy and AWS Console screenshots are unavailable by owner choice. Terraform provider-mock tests are not a cloud deployment. The local cluster uses arm64 images built on the laptop; CI publishes amd64 images and verifies them on kind. The classroom application has no login system, public TLS or production backup policy. Prometheus/Grafana demo storage is ephemeral. CI's deploy target is temporary kind, so persistent Minikube updates are explicit local rollouts. A live presentation/recording and official-email Google Form submission still require the student.
