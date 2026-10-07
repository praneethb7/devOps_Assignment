# Terraform and Infrastructure as Code

An S3 bucket built and destroyed through the complete Terraform workflow, plus notes on the
five AWS services the rest of the course depends on.

**Environment:** Terraform v1.16.4 on macOS (Apple silicon), `hashicorp/aws` provider
v6.67.0, AWS CLI v2.36.14, LocalStack 3.8.1 in Docker.

---

## Contents

| Folder | What it is |
|---|---|
| [`terraform-s3-demo/`](terraform-s3-demo/) | A working Terraform project: `init`, `fmt`, `validate`, `plan`, `apply`, `show`, `output`, `destroy`, every step captured |
| [`aws-services/01-iam/`](aws-services/01-iam/) | Users, groups, roles, policies, the evaluation order, least privilege |
| [`aws-services/02-ec2/`](aws-services/02-ec2/) | AMIs, instance types, key pairs, security groups, EBS, public vs private IP, the lifecycle |
| [`aws-services/03-s3/`](aws-services/03-s3/) | Buckets, objects, storage classes, versioning, lifecycle policies, encryption, access control |
| [`aws-services/04-vpc/`](aws-services/04-vpc/) | CIDR, subnets, route tables, internet and NAT gateways, security groups vs NACLs |
| [`aws-services/05-dynamodb-rds/`](aws-services/05-dynamodb-rds/) | Partition and sort keys; engines, Multi-AZ, read replicas, backups |

Session 19's end-to-end build — VPC, subnets, routing, security groups, EC2 and S3 as one
`apply` — is in [`../cloud-terraform-in-action/`](../cloud-terraform-in-action/).

---

## Why this runs against LocalStack

There is no AWS account behind this work, so the Terraform runs target **LocalStack** — an
AWS-compatible API served from a container on `localhost:4566`.

```bash
docker run -d --name localstack -p 4566:4566 \
  -e SERVICES=s3,ec2,iam,sts localstack/localstack:3.8.1
```

That choice is worth being clear about:

- The **API calls are real**. Terraform speaks the S3 and EC2 protocols and the provider
  cannot tell the difference, which is the entire point of the exercise.
- The **service answering them is local**. No account, no bill, no credentials to leak.
- The only AWS-specific code is a `provider` block with an `endpoints` override and three
  `skip_*` flags. Deleting that block targets real AWS, and nothing in `main.tf` changes.

Two practical notes:

- `localstack/localstack:latest` now requires a Pro licence and exits immediately with
  `License activation failed! 🔑❌`. The pinned community release `3.8.1` needs no token.
- LocalStack is not a complete AWS. One resource here — an S3 lifecycle configuration —
  cannot be applied against it, because the provider's read-after-write consistency check
  never succeeds. That failure, and why the resource is left in the code behind a flag, is
  written up in [`terraform-s3-demo/README.md`](terraform-s3-demo/README.md).

---

## What the workflow actually showed

| Command | What it proved |
|---|---|
| `init` | resolved `~> 6.0` to v6.67.0 and pinned it with checksums in the lock file |
| `fmt -check` | no output and exit 0 when formatting is clean — which is what makes it a CI gate |
| `validate` | types, required arguments and references, with no API calls |
| `plan` | `5 to add`; `(known after apply)` distinguishes provider values from config values |
| `apply` | the bucket created first and alone, then four dependents in parallel — the dependency graph, inferred from references |
| `show` | state holds attributes never written in the config: `hosted_zone_id`, `bucket_domain_name` |
| `output` | the curated subset, and `-raw` for piping one value onward |
| `destroy` | **the same graph in reverse** — dependents first, the bucket last |

Everything was then re-verified with the AWS CLI, which has never read the Terraform state:
versioning `Enabled`, `AES256` encryption, all four public-access flags `true`, and the
object's bytes read back.

---

## The idea the exercise is really about

A failed `apply` is **partial, not atomic**. When the lifecycle resource timed out, the
other five resources already existed and `terraform state list` showed exactly those five.
Nothing rolled back.

That is what state is for. Terraform does not inspect the world and diff it on every run —
it compares the configuration against its record of what it previously created. Which
explains both its strengths and its sharpest edges: a resource changed by hand in the
console causes drift, and a lost or corrupted state file means Terraform no longer knows it
owns anything. It is also why real projects keep state in a versioned, encrypted S3 bucket
with locking, rather than the local file used here.
