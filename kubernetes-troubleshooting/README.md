# Kubernetes Troubleshooting

The diagnostic commands, nine broken-and-fixed failure scenarios, and a mini project with
three faults planted in one manifest. Everything here was applied to a live cluster, broken
on purpose, diagnosed, fixed and verified.

**Environment:** Minikube v1.39.0 with the Docker driver on macOS (Apple silicon),
Kubernetes v1.37.0, containerd 2.3.4, metrics-server enabled.

| Folder | Contents |
|---|---|
| [`01-commands/`](01-commands/) | `get`, `describe`, `logs`, `exec`, `events`, `explain`, `top`, `-o wide` against a healthy workload |
| [`02-scenarios/`](02-scenarios/) | nine `-broken.yaml` / `-fixed.yaml` pairs, one per failure mode |
| [`03-mini-project/`](03-mini-project/) | three independent faults in one Deployment and Service |

---

## The nine scenarios

| # | Symptom | Root cause | Found with |
|---|---|---|---|
| 1 | `CrashLoopBackOff` | command exits 1 | `describe` → `Exit Code` |
| 2 | `ImagePullBackOff` | tag not in registry | event → `code = NotFound` |
| 3 | `ErrImagePull` | no pull authorisation | event → `403 Forbidden` |
| 4 | `Pending` | request exceeds node capacity | event → `Insufficient cpu` |
| 5 | `ContainerCreating` | referenced Secret missing | event → `FailedMount` |
| 6 | Service answers nothing | selector ≠ Pod labels | `get endpoints` → `<none>` |
| 7 | name does not resolve | wrong Service name | `nslookup` → `NXDOMAIN` |
| 8 | connection refused | `targetPort` ≠ `containerPort` | `get endpoints` → wrong port |
| 9 | `CreateContainerConfigError` | ConfigMap key missing | event names the key |

---

## What the exercise actually taught

**The status column classifies the problem before you investigate anything.** Each status
corresponds to a specific phase having failed, and that tells you which tool will help:

| Status | What got as far as | `logs` useful? |
|---|---|---|
| `Pending` | not scheduled | no — no container exists |
| `ContainerCreating` | scheduled, volumes failing | no |
| `CreateContainerConfigError` | scheduled, config failing | no |
| `ErrImagePull` / `ImagePullBackOff` | scheduled, image failing | no |
| `CrashLoopBackOff` / `Error` | ran and exited | **yes** |
| `Running` but unreachable | fine — the problem is a Service | no |

Four of those six states make `kubectl logs` useless, which is why reaching for logs first
is usually a wasted step.

**`kubectl describe` names the root cause in eight of nine scenarios.** Not a hint — the
exact missing key, the exact tag, the exact Secret name. The reflex worth building is
`get` then `describe`, and reading the `Events` block before forming a theory.

**The ninth is the dangerous class.** Scenarios 6 and 8 produce **no event and no log**,
because two objects that are each individually valid simply disagree. Nothing in Kubernetes
validates that a Service selector matches any Pod, or that a `targetPort` matches a
`containerPort`. These are found only by comparing declared values:

```bash
kubectl get svc X -o jsonpath='{.spec.selector}'          # against
kubectl get deploy X -o jsonpath='{.spec.template.metadata.labels}'
```

And the distinction between them is one line of output:

- **`ENDPOINTS <none>`** → the selector is wrong (scenario 6)
- **`ENDPOINTS 10.244.0.98:8080`** → the selector is right and the **port** is wrong
  (scenario 8)

Populated endpoints are necessary but not sufficient. Only a request through the Service
tests both.

**Two error messages that look similar and mean opposite things:**

- `Connection refused` — the packet arrived and nothing was listening. Wrong port, or the
  process is down.
- Timeout — the packet went nowhere. Wrong address, a NetworkPolicy, or routing.

**`NXDOMAIN` does not always mean failure.** Scenario 7's *successful* lookup printed four
`NXDOMAIN` lines before resolving, because the resolver walks the three-suffix `search` path
in `/etc/resolv.conf`. `nslookup` also exits non-zero whenever any query in that sequence
fails, so its exit code cannot be used as a health check. The `Name:` and `Address:` lines
are the answer; read to the end.

---

## Things the runs exposed that the manifests did not plan for

- **`kubectl logs --previous` failed in scenario 1** — `unable to retrieve container logs`.
  The previous container had already been garbage collected after three restarts. The
  `Last State` and `Exit Code` fields in `describe` survive that, because they live in the
  Pod status rather than in container storage.
- **Fixing scenario 5 is not instant.** The kubelet retries a failed mount on a backoff
  (`FailedMount ... x7 over 35s`), so creating the missing Secret left the Pod
  `ContainerCreating` for another half minute. The first capture recorded it still stuck at
  60 seconds, which looked like the fix had not worked. It had; it needed waiting for.
- **`kubectl top pods` returned `metrics not available yet`** on Pods 25 seconds old, while
  `top node` worked in the same breath. Same scrape-cycle lag that makes a new HPA read
  `<unknown>`.
- **`v1 Endpoints is deprecated in v1.33+`** appears on every `get endpoints` call.
  `kubectl get endpointslices` is the current form; `endpoints` still works and is still
  what most documentation and most muscle memory use.

---

## Cleanup

```bash
kubectl delete namespace triage yatri-triage
```
