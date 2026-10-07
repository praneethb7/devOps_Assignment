# Monitoring, Observability and GitOps

Three topics that together answer: *is it working, why is it not, and how did it get into
this state.*

**Environment:** Docker Compose and Minikube v1.39.0 on macOS (Apple silicon),
Kubernetes v1.37.0, Prometheus v3.1.0, Grafana 11.5.1, Argo CD from upstream `stable`.

| Folder | Contents |
|---|---|
| [`01-monitoring/`](01-monitoring/) | a metrics-emitting service, Prometheus scraping it, three alert rules — two of which fired — and Grafana provisioned from files |
| [`02-observability/`](02-observability/) | metrics, logs and traces on Kubernetes, and why the third one is a code change |
| [`03-gitops/`](03-gitops/) | Argo CD reconciling a repo path, reverting a manual scale and recreating a deleted Service |

---

## Results

| Exercise | Outcome |
|---|---|
| `/metrics` endpoint | counter, gauge and histogram, hand-written in the exposition format |
| Prometheus targets | both jobs `up`, 5s scrape interval |
| PromQL | rate by outcome, failure ratio `0.0876`, p50/p95/p99 from buckets |
| `HighBookingFailureRate` | **fired** — 8.76% against a 5% threshold |
| `BookingServiceDown` | **fired** on `docker compose stop`, cleared on restart |
| Grafana | datasource and 6-panel dashboard provisioned; query proxied through it |
| Three signals | `top` showed 1m CPU; logs showed `reason: payment_declined` |
| Argo CD first sync | `Synced` / `Healthy` at commit `6357e408` |
| Self-heal | manual scale to 5 reverted to 2; deleted Service recreated |

---

## The thread through all three

**Monitoring is a closed question set.** `01-monitoring/` alerts on a failure ratio, a
latency percentile and target liveness. That covers failures already understood.

**Observability is the ability to ask a new question.** `02-observability/` is about why the
three signals are not interchangeable: a metric found that something was wrong, and only the
log record said `payment_declined`. Metrics cannot hold that — high-cardinality labels
multiply time series — and logs cannot aggregate cheaply. Hence both, with alerting on the
metric and investigation in the logs.

**GitOps is how the state became what it is.** `03-gitops/` makes the cluster's
configuration a function of a git commit, which turns "why is production like this" from
archaeology into `git log`.

---

## Three things worth keeping

**`up` is the most important metric, and it is synthetic.** Prometheus writes it per target
per scrape, so it distinguishes "the service is broken" from "we cannot see the service".
When the application was stopped, the failure-rate alert went *quiet* — no samples, no ratio
— and only `up == 0` caught it. **Silence is the dangerous alert state.**

**A hand-rolled histogram is easy to get wrong in a way that does not fail.** The first
`/metrics` output had `+Inf` at 3916 against a `_count` of 822; the buckets were being
incremented in the application and accumulated again in the handler.
`histogram_quantile()` happily returns plausible numbers from broken buckets rather than
erroring, so **`+Inf` must equal `_count`** is the check to run.

**Self-heal makes `kubectl edit` stop working, on purpose.** A manual scale to five replicas
survived about thirty seconds. That is the point rather than a limitation: the emergency fix
has to be a commit, so there is no such thing as an undocumented production change. It is
also the thing to understand before switching it on.

---

## Cleanup

```bash
cd 01-monitoring && docker compose down -v && cd ..
kubectl delete -f 03-gitops/argocd/application.yaml
kubectl delete namespace observability-demo yatri-gitops argocd
```
