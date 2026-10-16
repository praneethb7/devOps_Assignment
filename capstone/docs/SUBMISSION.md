# Submission packet

Deadline supplied by the course: **16 October 2026, 11:59 PM IST**.

- Repository: https://github.com/praneethb7/devOps_Assignment
- Capstone entry: https://github.com/praneethb7/devOps_Assignment/tree/main/capstone
- Successful complete pipeline: https://github.com/praneethb7/devOps_Assignment/actions/runs/38868966201
- Workflow: https://github.com/praneethb7/devOps_Assignment/blob/main/.github/workflows/campuscrate.yml
- Evidence: https://github.com/praneethb7/devOps_Assignment/tree/main/capstone/evidence
- Submission form: https://forms.gle/XWAP1vAumDJgAPM1A

## Suggested project description

CampusCrate is a campus equipment lending application built with React, FastAPI and PostgreSQL. It supports inventory management, borrowing, returns, overdue tracking and transactional stock protection. Its delivery workflow runs isolated automated tests, builds non-root containers, gates publication with Trivy, publishes SHA-tagged images to GHCR and deploys to Kubernetes with Helm. A persistent Minikube demonstration includes Ingress, CPU autoscaling, Prometheus scraping and Grafana dashboards. Terraform defines the AWS VPC/EKS architecture and passes validation and mocked-provider planning tests; real AWS resources were not provisioned.

## Rubric mapping

| Module | Implementation and evidence | Remaining gap |
|---|---|---|
| M1 Application / 10 | `backend/app`, Alembic migration, React UI, browser/Ingress screenshots, database capture | None in implemented application scope |
| M2 Tests / 10 | 15 tests, isolated database, pytest capture, CI PostgreSQL test job | Local terminal screenshot can supplement text capture |
| M3 Git / 5 | Public repository, meaningful capstone commits, ignore rules, commit-history capture | None in source implementation |
| M4 Docker / 10 | Two non-root images, multi-stage frontend, healthy Compose capture and browser screenshot | Local terminal screenshot can supplement Compose capture |
| M5 CI/CD / 15 | Successful linked run: tests, frontend build, both images, GHCR SHA tags, Kubernetes smoke deployment | GHCR package-page screenshot can supplement published-image job logs |
| M6 DevSecOps / 5 | Both scans passed; raw reports and written explanation in `docs/SECURITY.md` | None in implemented pipeline |
| M7 Terraform / 15 | Valid HCL, init, committed lock file, tfvars example, mocked-plan assertions | **Real AWS plan, VPC/EKS creation, AWS Console evidence and destroy were not performed** |
| M8 Kubernetes / 15 | Helm, namespace, 2+ frontend/backend replicas, ClusterIP, Ingress, running-pod captures and browser screenshot | Local terminal screenshot can supplement command captures |
| M9 Observability / 10 | Metrics capture, ServiceMonitor UP screenshot, Grafana populated-panel screenshot | None in demonstrated local stack |
| M10 Presentation / 5 | README, architecture and walkthrough; CI deploy job demonstrates source-to-cluster delivery | Student must present live or provide the required recording |

No score is guaranteed. The instructor evaluates evidence; code-only AWS work cannot satisfy real-provisioning criteria. Text command captures are included as raw evidence and are not described as screenshots of a terminal window.

## Final manual steps

1. Open the repository and capstone link while signed out to confirm accessibility.
2. Review the current complete green run and evidence. If a newer successful run exists, use that run URL.
3. Sign in to the Google Form using the **official SST email ID**; do not assume the Git commit email is the required student email.
4. Enter the verified links and project information; check every field before the single allowed submission.
5. Submit once and retain the confirmation. The form has **not** been submitted by this project setup.

The announced `student-guide.md` was not present in the linked instructor repository when inspected. The README and GRADING.md were available and used for the implementation checklist.
