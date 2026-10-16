# Walkthrough and presentation notes

## Eight-minute walkthrough

1. **Application (1 minute).** Open CampusCrate through `http://campuscrate.localhost:8088`. Show availability, search and category filters. Create equipment; lend one unit; show the count decrease; return it and show the count recover. Point out the overdue sample and preserved loan ledger.
2. **API and persistence (1 minute).** Open Swagger at `http://127.0.0.1:8001/docs`. Show GET, POST, PUT and DELETE. Explain that a 409 protects loan history or prevents overbooking. Show `kubectl -n campuscrate exec postgres-0 -- psql -U campuscrate -d campuscrate -c '\dt'` and `alembic_version`.
3. **Git and CI (2 minutes).** Show the capstone commit history and successful Actions run. Make a small visible text change, commit and push using your account, then show the new run. Tests and migration checks gate builds; Trivy gates publication; image tags equal the source SHA. The final job deploys the exact scanned images to kind and exercises lending before removing its cluster.
4. **Docker and Kubernetes (1 minute).** Show the two Dockerfiles: Node build stage then unprivileged Nginx; Python build/runtime separation and UID 10001. Show `docker compose ps`, `kubectl -n campuscrate get pods,svc,ingress,hpa`, and `helm list -n campuscrate`.
5. **Infrastructure (45 seconds).** Open Terraform files. Explain public/private subnets, NAT, EKS workers, restricted API access, OIDC and EBS CSI storage. Show validation and mock-plan tests. State plainly that AWS provisioning was intentionally not performed; no real cloud creation/destroy evidence is available.
6. **Autoscaling and monitoring (1 minute).** Show the recorded 2→5 HPA event, then the live HPA. Explain the 20m demo request versus the default 100m request and the 60% target. Show Prometheus UP targets and Grafana request rate, latency, error-rate and per-route panels.
7. **Troubleshooting (45 seconds).** Apply the isolated broken Service, observe empty EndpointSlices, compare pod labels, patch its selector, observe endpoints and delete the exercise object. Explain the missing-image exercise using captured events.

## Live local rollout after a commit

CI's deploy job uses a temporary cluster; it does not update the laptop cluster automatically. To demonstrate a persistent local rollout after changing application code:

```bash
docker compose build
minikube image load campuscrate-backend:local campuscrate-frontend:local
helm upgrade campuscrate helm/campuscrate -n campuscrate \
  -f helm/campuscrate/values-local.yaml --set monitoring.enabled=true \
  --wait --wait-for-jobs
kubectl -n campuscrate rollout restart deployment/frontend deployment/backend
kubectl -n campuscrate rollout status deployment/frontend
kubectl -n campuscrate rollout status deployment/backend
```

For immutable published images on an amd64 cluster, set `backend.tag` and `frontend.tag` to the successful run's full source SHA. The current CI images are linux/amd64; the local Apple-silicon demo uses locally built arm64 images. Private GHCR packages require a pull Secret through `imagePullSecrets`.

## Questions to be ready for

| Question | Explanation |
|---|---|
| Why separate readiness and liveness? | A DB outage removes the pod from service but should not continuously restart a healthy process. |
| Why lock the equipment row? | Concurrent borrowers must serialize the availability check and insertion to prevent allocating the last unit twice. |
| Why Alembic? | Schema changes become versioned, repeatable operations rather than manual SQL. |
| Why migrations as a Job? | Multiple API replicas must not race to change the schema at startup. |
| Why SHA tags? | An image can be traced to an exact source revision; mutable `latest` cannot provide that guarantee. |
| Why can a Service fail with healthy pods? | Its selector or target port can be wrong. EndpointSlices reveal whether pods were selected. |
| Why is HPA showing unknown? | Missing/old CPU samples, unready pods, absent resource requests or a broken Metrics Server. |
| Why Prometheus plus Metrics Server? | Prometheus stores application time series; HPA's default resource metrics API is supplied by Metrics Server. |
| Why not PostgreSQL replicas here? | Multiple independent PostgreSQL pods sharing a PVC do not create replication. Production needs managed PostgreSQL or a replication operator plus backups. |
| What does Helm rollback restore? | Kubernetes manifests; it does not restore database contents or undo migrations. |
| Why Terraform destroy? | Cloud resources continue charging after the demo; code-only validation incurred no resource charges here. |
