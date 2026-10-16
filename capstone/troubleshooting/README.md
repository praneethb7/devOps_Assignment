# Troubleshooting and recovery

All exercise objects have separate names; the working application remains available.

## ImagePullBackOff

```bash
kubectl apply -f troubleshooting/broken-image.yaml
kubectl -n campuscrate get pods -l app=broken-image
kubectl -n campuscrate describe pod -l app=broken-image
kubectl -n campuscrate get events --sort-by=.lastTimestamp
```

The `campuscrate-missing-tag` image tag does not exist. `describe` shows `ErrImagePull` and `ImagePullBackOff`; the registry error identifies the unresolved tag. Recover by changing the image to the known published frontend SHA, or remove the isolated lab:

```bash
kubectl -n campuscrate delete deployment broken-image
```

## Service selector mismatch

```bash
kubectl apply -f troubleshooting/broken-service.yaml
kubectl -n campuscrate get service broken-service -o yaml
kubectl -n campuscrate get endpointslice -l kubernetes.io/service-name=broken-service
kubectl -n campuscrate get pods --show-labels
```

The selector ends in `backend-typo`, which matches no pod. A running pod alone does not prove its Service can reach it. Fix the selector and confirm populated endpoints:

```bash
kubectl -n campuscrate patch service broken-service -p '{"spec":{"selector":{"app":"campuscrate-backend"}}}'
kubectl -n campuscrate get endpointslice -l kubernetes.io/service-name=broken-service -o wide
kubectl -n campuscrate delete service broken-service
```

## Operational checks

| Symptom | Investigation | Recovery |
|---|---|---|
| `/ready` returns 503 | Backend logs, PostgreSQL readiness, migration Job, Secret reference | Restore DB access or run missing migration; liveness stays independent |
| Browser API error | Ingress host and paths, Services, EndpointSlices, backend logs | Match browser hostname and check `/api` routes to backend |
| HPA `<unknown>` | `kubectl top pods`, Metrics Server logs, requests and pod readiness | Wait for fresh metrics or repair Metrics Server; do not infer scaling from configuration alone |
| Migration retries on first install | Job logs and DB readiness | Job retries while DB starts; persistent failure needs schema or credential repair |
| Grafana restarts | `lastState` for OOMKilled, previous logs | Increase realistic memory limit; re-establish port-forward |
| Prometheus target missing | ServiceMonitor release label, namespace selector, named port | Align all selectors and check `/metrics` |
| Trivy fails | Actions report for specific package/CVE | Upgrade or replace vulnerable dependencies/base; retain the gate |
| Docker public pulls hang | Credential-helper process, registry reachability | Repair credential helper or use temporary public-image config; preserve user configuration |

For a failed rollout use `helm history`, `kubectl describe`, `kubectl logs --previous` and `helm rollback`. Collect events before removing failed objects. Database state is not reverted by Helm rollback.
