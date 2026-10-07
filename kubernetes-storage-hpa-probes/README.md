# Kubernetes Storage, HPA and Probes

Three topics that only make sense together: where data lives when Pods are disposable, how
the replica count changes on its own, and how Kubernetes decides whether a container is
working.

**Environment:** Minikube v1.39.0 with the Docker driver on macOS (Apple silicon),
Kubernetes v1.37.0, containerd 2.3.4. Single node with 15 allocatable CPUs and 8 GiB.
`metrics-server` enabled via `minikube addons enable metrics-server` — without it there is
no `kubectl top` and no HPA.

```bash
minikube addons enable metrics-server
kubectl top node
```

```
NAME       CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)
minikube   672m         4%       1981Mi          24%
```

---

## Contents

| Folder | What it covers |
|---|---|
| [`01-kubernetes-volumes/`](01-kubernetes-volumes/) | `emptyDir`, `hostPath`, static PV/PVC, StorageClass and dynamic provisioning — each one broken on purpose to show what it does not survive |
| [`02-hpa/`](02-hpa/) | One Deployment taken 1 → 8 → 1 by CPU load alone, with the autoscaler's own reasoning read out of `describe` |
| [`03-probes/`](03-probes/) | `readinessProbe`, `livenessProbe` and `startupProbe`, each made to fail, plus the restart loop you get without a startup probe |
| [`04-mini-project/`](04-mini-project/) | All of the above in one Deployment: a PVC that survives a rollout while the replica count goes 2 → 6 → 2 |

---

## The one idea underneath all three

Kubernetes treats a Pod as disposable. Every topic here is a consequence of that.

- **Storage** exists because the Pod is disposable and some data is not. The whole
  `emptyDir` → `hostPath` → PVC progression is just increasing independence from the Pod's
  lifecycle.
- **The HPA** exists because Pods are disposable *enough* to create and destroy on a metric.
  That only works if they are stateless, or if their state is on a volume that outlives
  them.
- **Probes** exist because Kubernetes has to decide when to dispose of one, and when a Pod
  that is merely slow should be left alone.

The mini project is where the three meet: six replicas created and destroyed by an
autoscaler, probes deciding which of them received traffic, and one file on a
PersistentVolume that none of it touched.

---

## Results

| Exercise | Outcome |
|---|---|
| `emptyDir` shared by two containers | writer and reader saw the same file with no network |
| `emptyDir` across a container restart | `restartCount=2`, every line retained |
| `emptyDir` across a Pod delete | 7 lines → fresh empty volume |
| `hostPath` | same file read from the Pod and from the node over `minikube ssh` |
| Static PV + PVC | `Available` → `Bound`; data survived a Pod delete and recreate |
| Dynamic provisioning | a PV named `pvc-89b60b43-…` that nobody wrote |
| HPA under load | 1 → 2 → 4 → 8 in 45s, then 8 → 4 → 2 → 1 once load stopped |
| `readinessProbe` | `0/1 Running` with empty Endpoints, then routable |
| `livenessProbe` | probe 404 → `Killing` → `restartCount=2` |
| `startupProbe` vs none | Ready at 60s with 0 restarts, versus a permanent restart loop |
| Mini project | 2 → 6 → 2 replicas, `receipt-2001` intact throughout |

---

## Three things that cost time

**An HPA with no `resources.requests.cpu` does nothing, silently.** Target utilisation is a
percentage *of the request*, so with no request there is no denominator and `TARGETS` reads
`<unknown>` forever. There is no error and no event — the HPA simply never acts.

**A serial load generator cannot load anything.** The obvious
`while true; do wget -q -O- http://svc; done` moved the target's CPU to **3%**, because each
iteration is a fork, an exec and a TCP handshake — the loop is bounded by the client, not the
server. Eight loops in parallel per Pod produced 232% utilisation and real scaling.

**Overloading the cluster breaks the autoscaler that is measuring it.** An earlier load
generator (3 Pods × 25 loops) saturated the node, metrics-server was starved of CPU, and the
HPA froze with
`FailedGetResourceMetric: did not receive metrics for targeted pods`. The control loop needs
headroom to function, which is an argument for leaving some and for alerting on the
`ScalingActive` condition going `False`.

---

## Cleanup

```bash
kubectl delete namespace yatri-receipts
kubectl delete -f 01-kubernetes-volumes/ -f 02-hpa/ -f 03-probes/ --ignore-not-found
kubectl delete pv yatri-static-pv --ignore-not-found
```

The `standard` StorageClass has `reclaimPolicy: Delete`, so dynamically provisioned volumes
go with their claims. `yatri-static-pv` uses `Retain` and has to be removed by hand — which
is the behaviour difference that matters most in production.
