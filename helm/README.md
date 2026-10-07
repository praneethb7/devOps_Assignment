# Helm

The command surface, a complete install → upgrade → rollback cycle with the served content
proving which revision is live, and one chart deployed twice as two environments.

**Environment:** Minikube v1.39.0 with the Docker driver on macOS (Apple silicon),
Kubernetes v1.37.0, **Helm v4.3.0**. Namespace `helm-demo`.

| Folder | Contents |
|---|---|
| [`01-commands/`](01-commands/) | `create`, `lint`, `template`, `install`, `list`, `status`, `get`, `repo`, `search`, `uninstall` |
| [`02-rollback/`](02-rollback/) | install → upgrade → upgrade → rollback, with `helm history` at each step |
| [`03-mini-project/`](03-mini-project/) | `notes-chart`: one chart, `values.yaml` and `values-prod.yaml` |

---

## What Helm actually is

A template engine plus a record of what it rendered. `helm get manifest` shows the second
half — the exact YAML sent to the API server:

```
$ helm get manifest yatri-notes -n helm-demo | grep -E '^kind:|^  name:|replicas:'
kind: ConfigMap
  name: yatri-notes-notes-chart
kind: Service
  name: yatri-notes-notes-chart
kind: Deployment
  name: yatri-notes-notes-chart
  replicas: 1
```

That record lives in a Secret in the release namespace, which is what makes `rollback`
possible at all — Helm is not re-rendering an old chart, it is re-applying a stored
manifest.

Note `APPLY_METHOD: server-side apply` in `helm get metadata`. This is Helm **4**, which
applies server-side by default, so field ownership is tracked by the API server rather than
by Helm's old client-side three-way merge. The practical difference is that a conflict with
another controller that manages the same field now surfaces as an apply conflict instead of
being silently overwritten.

---

## The rollback cycle

The chart renders its `message` value into the served page, so each revision is visually
distinct and the rollback can be proven from outside rather than from Helm's own report.

```
install  --set message='revision one'     -> revision one (revision 1)
upgrade  --set message='revision two'     -> revision two (revision 2)
upgrade  --set message='BROKEN RELEASE'   -> BROKEN RELEASE (revision 3)
helm rollback yatri-echo 2                -> revision two (revision 2)
```

```
$ helm history yatri-echo -n helm-demo
REVISION  UPDATED                   STATUS      CHART             DESCRIPTION
1         Wed Oct  7 21:18:17 2026  superseded  echo-chart-0.1.0  Install complete
2         Wed Oct  7 21:18:42 2026  superseded  echo-chart-0.1.0  Upgrade complete
3         Wed Oct  7 21:19:06 2026  superseded  echo-chart-0.1.0  Upgrade complete
4         Wed Oct  7 21:19:30 2026  deployed    echo-chart-0.1.0  Rollback to 2
```

**A rollback rolls forward.** Rolling back to revision 2 created **revision 4**, described
as `Rollback to 2`. Nothing is rewritten and nothing is deleted — the history is
append-only, so the broken revision 3 is still there and still inspectable. Rolling back a
rollback is just another rollback.

Full detail in [`02-rollback/`](02-rollback/).

---

## One chart, two environments

[`03-mini-project/notes-chart/`](03-mini-project/notes-chart/) ships `values.yaml` as dev
defaults and `values-prod.yaml` as an overlay containing **only the differences**:

```bash
helm install yatri-notes ./notes-chart -n helm-demo
helm upgrade yatri-notes ./notes-chart -n helm-demo -f notes-chart/values-prod.yaml
```

```
### the production release, read from inside the cluster
<h1>yatri notes - PRODUCTION</h1>
<p>release: yatri-notes</p>
<p>chart: notes-chart-0.1.0</p>
<p>revision: 2</p>
<p>environment: production</p>

limits={"cpu":"500m","memory":"256Mi"}
```

Three replicas instead of one, `logLevel: warn` instead of `debug`, and larger limits — from
a 12-line overlay rather than a second copy of the manifests. That is the entire argument
for Helm over plain YAML.

---

## Two template details that matter

**The ConfigMap checksum annotation.** From
[`03-mini-project/notes-chart/templates/deployment.yaml`](03-mini-project/notes-chart/templates/deployment.yaml):

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

Without this, a config-only `helm upgrade` updates the ConfigMap and the running Pods keep
the old values — the same trap as Session 12, where environment variables are a snapshot
taken at container creation. Hashing the rendered ConfigMap into a Pod annotation changes
the Pod template whenever the config changes, which forces a rollout.

**Selector labels must exclude the version.** `_helpers.tpl` defines two label sets
deliberately:

```
notes-chart.labels          -> name, instance, version, managed-by, chart
notes-chart.selectorLabels  -> name, instance only
```

A Deployment's `spec.selector` is **immutable**. Putting `app.kubernetes.io/version` in it
means the first chart version bump produces
`field is immutable` and the release cannot be upgraded without deleting it.

---

## Commands, grouped by what they are for

| Inspect without a cluster | Act on a cluster | Inspect a release |
|---|---|---|
| `helm create` | `helm install` | `helm list` |
| `helm lint` | `helm upgrade` | `helm status` |
| `helm template` | `helm rollback` | `helm history` |
| `helm repo add/update` | `helm uninstall` | `helm get values/manifest/metadata` |
| `helm search repo/hub` | | |

The left column is where most debugging should start — `helm template` renders locally and
shows exactly what would be applied, with no release created and nothing to clean up.

## Cleanup

```bash
helm uninstall yatri-notes yatri-echo -n helm-demo
kubectl delete namespace helm-demo
```

`helm uninstall` removes the release's objects but **not** PersistentVolumeClaims created by
a StatefulSet volumeClaimTemplate, and not CRDs. Deleting the namespace is the reliable
finish.
