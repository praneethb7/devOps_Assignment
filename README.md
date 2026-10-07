# DevOps Coursework

Hands-on work for the SST DevOps & Cloud module, one folder per session. Each folder has its
own README with the commands that were run, the output they produced, and screenshots from
the run.

| Session | Folder | Topic |
|---|---|---|
| 01–02 | [`linux/`](linux/) | Soft and hard links, `adduser` vs `useradd`, `journalctl`, command cheat sheet |
| 03 | [`shell-scripting/`](shell-scripting/) | `sysinfo.sh` — variables, `read -p`, `mkdir`/`touch`, output redirection |
| 04 | [`networking/`](networking/) | `ip`, `ss`, `ping`, `traceroute`, `dig`, `curl`, and IP addressing notes |
| 05 | [`git-github/`](git-github/) | `git commit -a -m` vs `-m`, and `git cherry-pick` |
| 06 | [`docker-fundamentals/`](docker-fundamentals/) | Six Hello World containers: Node.js, Python, Java, Apache, React, Nginx |
| 07 | [`docker-multi-stage/`](docker-multi-stage/) | Multi-stage builds, and deploying three application types |
| 08 | [`docker-networking/`](docker-networking/) | Multi-network containers, host networking, bind mounts, overlay networks |
| 09 | [`kubernetes-fundamentals/`](kubernetes-fundamentals/) | Minikube setup, cluster architecture, core objects |
| 10 | [`kubernetes-core-objects/`](kubernetes-core-objects/) | Rolling, blue-green, canary and recreate strategies; the Pod lifecycle |
| 11 | [`kubernetes-services/`](kubernetes-services/) | The five Service types, object comparisons, FQDN and CoreDNS |
| 12 | [`kubernetes-ingress-config/`](kubernetes-ingress-config/) | ConfigMap and Secret injection, path and host Ingress routing, TLS |
| 13 | [`kubernetes-storage-hpa-probes/`](kubernetes-storage-hpa-probes/) | Volumes from `emptyDir` to dynamic provisioning; an HPA driven 1→8→1; all three probes |
| 14 | [`kubernetes-troubleshooting/`](kubernetes-troubleshooting/) | The diagnostic commands, nine broken-and-fixed scenarios, a three-fault mini project |
| 15 | [`helm/`](helm/) | Command surface, a full install→upgrade→rollback cycle, one chart as two environments |
| 16 | [`cicd-github-actions/`](cicd-github-actions/) | Lint, a three-version test matrix, publish to GHCR, smoke test of the published image |
| 17 | [`devsecops-pipeline/`](devsecops-pipeline/) | SAST, SCA, secret and image scanning into a gate, then deploy to a kind cluster |
| 18 | [`terraform-infrastructure-as-code/`](terraform-infrastructure-as-code/) | An S3 bucket through the full Terraform workflow, plus IAM, EC2, S3, VPC, DynamoDB and RDS notes |
| 19 | [`cloud-terraform-in-action/`](cloud-terraform-in-action/) | VPC, subnets, routing, gateway, security groups, EC2 and S3 — fifteen resources in one apply |
| 20 | [`monitoring-observability-gitops/`](monitoring-observability-gitops/) | Prometheus and Grafana with alerts that fired, the three signals, Argo CD self-healing |
| 21 | [`final-project-session21/`](final-project-session21/) | Running the TaskBoard three-tier stack and exercising its APIs |

---

## Environment

Everything was run on macOS (Apple silicon) with Docker Desktop 29.6.2. Linux-only commands
were run inside Ubuntu containers.

| | Version |
|---|---|
| Kubernetes | Minikube v1.39.0, Kubernetes v1.37.0, containerd 2.3.4 |
| Helm | v4.3.0 |
| Terraform | v1.16.4, `hashicorp/aws` v6.67.0 |
| Monitoring | Prometheus v3.1.0, Grafana 11.5.1 |
| GitOps | Argo CD, upstream `stable` manifests |

**AWS** — Sessions 18 and 19 run against **LocalStack 3.8.1** in Docker, an AWS-compatible
API on `localhost:4566`. The Terraform and the API calls are real; the service answering
them is local, so there is no account and no bill. The only AWS-specific code is a
`provider` block with an `endpoints` override, and deleting it targets real AWS unchanged.

**Pipelines** — Sessions 16 and 17 run on GitHub Actions; their workflow files are in
[`.github/workflows/`](.github/workflows/), because GitHub only reads workflows from the
repository root. Both publish images to GHCR.

**Screenshots** are terminal renderings of the captured stdout of each command, produced
from the real output of the run they document.

---

## A few things that cost real time

Collected here because they were the parts that did not work first try.

**An HPA with no `resources.requests.cpu` does nothing, silently.** Utilisation is a
percentage *of the request*, so with no request there is no denominator — `TARGETS` reads
`<unknown>` forever, with no error and no event.

**A serial load generator cannot generate load.** `while true; do wget -q -O- http://svc;
done` moved the target's CPU to **3%**: the loop is bounded by process startup on the
client, not by the server. Eight loops in parallel per Pod produced 232% and real scaling.

**Overloading a cluster breaks the autoscaler measuring it.** A heavier load generator
starved metrics-server of CPU, and the HPA froze with
`FailedGetResourceMetric: did not receive metrics for targeted pods`.

**`kubectl describe` names the root cause in eight of nine failure scenarios** — the exact
missing key, tag or Secret. The two that produce no event at all are a Service selector that
matches no Pod, and a `targetPort` that is not the container's port; both are found only by
comparing two objects that are each individually valid.

**A failed `terraform apply` is partial, not atomic.** When one resource timed out against
LocalStack, the other five existed and the state file recorded exactly those five.

**A hand-written Prometheus histogram is easy to break without failing.** `+Inf` read 3916
against a `_count` of 822; `histogram_quantile()` returns plausible nonsense from bad
buckets rather than erroring. `+Inf` must equal `_count`.

**A security gate that blocks on HIGH blocks every build.** 25 fixable HIGH CVEs in a
distroless Debian base, none of them fixable by this application. The gate now blocks on
CRITICAL and reports HIGH, which is a policy that survives contact with a real base image.

**A GitHub Actions job with no `checkout` cannot run a shell step**, if the workflow sets
`defaults.run.working-directory`. It bit the smoke job in Session 16 and the gate job in
Session 17.
