# CampusCrate — Campus equipment lending

CampusCrate tracks shared equipment, student loans, due dates and returns. A React dashboard talks to a FastAPI service backed by PostgreSQL and Alembic migrations.

The capstone covers container delivery, automated testing, security scans, Terraform AWS networking and EKS, Helm deployments, autoscaling and Prometheus/Grafana monitoring.

## Architecture

```mermaid
flowchart LR
  Browser --> Ingress
  Ingress --> Frontend[React / Nginx]
  Ingress --> API[FastAPI replicas]
  API --> DB[(PostgreSQL / PVC)]
  Prometheus --> API
  Grafana --> Prometheus
  GitHub --> Actions[Tests / Build / Trivy]
  Actions --> GHCR
  GHCR --> API
  Terraform --> EKS[AWS VPC / EKS]
```

Implementation and verified run instructions are added with each completed component.
