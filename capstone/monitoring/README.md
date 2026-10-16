# Prometheus and Grafana

Run from the capstone directory after installing the application chart.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create namespace monitoring
# Generate a random password; store it only in the cluster Secret.
password="$(openssl rand -hex 20)"
kubectl -n monitoring create secret generic grafana-admin \
  --from-literal=admin-user=admin --from-literal=admin-password="$password"
unset password
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version 92.9.0 -n monitoring -f monitoring/values.yaml --wait --timeout 8m
kubectl apply -f monitoring/dashboard-configmap.yaml
helm upgrade campuscrate helm/campuscrate -n campuscrate \
  -f helm/campuscrate/values-local.yaml --set monitoring.enabled=true \
  --wait --wait-for-jobs
```

The ServiceMonitor label `release: monitoring` matches the Prometheus selector. The backend Service label matches its selector, and the named `http` port maps to port 8000. Prometheus scrapes every 15 seconds. The Grafana sidecar imports `dashboard-configmap.yaml`, using Prometheus datasource UID `prometheus`.

Open each port-forward in its own terminal:

```bash
kubectl -n monitoring port-forward svc/monitoring-grafana 3001:80
kubectl -n monitoring port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090
```

Open [Grafana](http://127.0.0.1:3001), sign in as `admin`, select Dashboards and open **CampusCrate · Application health**. Retrieve the password locally:

```bash
kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 --decode
```

Open [Prometheus Targets](http://127.0.0.1:9090/targets). Look for `serviceMonitor/campuscrate/campuscrate/0` and `UP` backend endpoints. Use `sum(rate(campuscrate_http_requests_total[2m]))` in the query interface. Run the bounded load script for at least a minute to populate rate panels.

Dashboard panels: request rate, p95 latency, 5xx error rate, request rate by route, target health and backend CPU. The two PrometheusRules detect unavailable backend targets and a sustained >5% server-error ratio. Alertmanager is disabled for the local demonstration; rules remain visible in Prometheus but no external notifications are configured.

Grafana uses a 512Mi memory limit after a 256Mi limit caused an OOM restart during testing. Its local database and Prometheus history are ephemeral for this demo, while application PostgreSQL uses a PVC. Reapply the ConfigMap to restore the dashboard after reinstallation.
