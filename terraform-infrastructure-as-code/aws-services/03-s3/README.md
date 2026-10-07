# S3 — Simple Storage Service

S3 is object storage: you `PUT` a whole file under a key and `GET` it back over HTTP. There
is no filesystem, no partial write, and no server to run. It is the service the Terraform
project in [`../../terraform-s3-demo/`](../../terraform-s3-demo/) builds.

It is also where most public cloud data leaks have happened, which is why half this page is
about access control.

---

## What is S3

Durability is quoted at **eleven nines** (99.999999999%) — AWS replicates every object
across multiple devices in at least three Availability Zones in the region. Availability is
lower and varies by storage class.

What it is not:

- **Not a filesystem.** No append, no partial write, no rename. Changing one byte means
  uploading the object again.
- **Not block storage.** You cannot mount it as a disk and run a database on it. That is
  EBS.
- **Not low-latency.** First-byte latency is tens of milliseconds, not microseconds.

Strong read-after-write consistency has applied to all operations since December 2020. The
old advice about eventually-consistent overwrites is obsolete.

---

## Buckets

The top-level container. A bucket lives in **one region**, and the name is **globally
unique across every AWS account on earth** — which is why real bucket names carry a company
or account suffix, as the Terraform project's `yatri-receipts-archive-24bcs10081` does.

Naming rules worth knowing: 3–63 characters, lowercase, numbers, hyphens and dots only, must
not look like an IP address. Avoid dots entirely — they break TLS certificate matching for
virtual-hosted-style URLs.

There is no limit on the number of objects in a bucket or on total size.

---

## Objects

An object is the data plus its metadata, stored under a **key**.

```
s3://yatri-receipts-archive/receipts/2026/10/booking-1001.pdf
   bucket                   |------------- key --------------|
```

The slashes are **part of the key string**. S3 has no directories; the console renders a
folder tree by splitting on `/` for display. "Listing a folder" is really listing keys with
a given prefix.

- Object size: 0 bytes to 5 TB
- Single `PUT`: up to 5 GB — beyond that, multipart upload (and multipart is worth using
  above ~100 MB anyway, for parallelism and resumability)
- Each object carries system metadata (size, last modified, ETag) and optional user metadata

Key design matters for performance. S3 scales per prefix, so spreading writes across many
prefixes parallelises better than piling everything under one.

---

## Storage classes

| Class | Use | Retrieval |
|---|---|---|
| **Standard** | frequently accessed | immediate |
| **Intelligent-Tiering** | unknown or changing patterns | immediate |
| **Standard-IA** | infrequent, needs to be instant | immediate, per-GB fee |
| **One Zone-IA** | infrequent, reproducible | immediate, single AZ |
| **Glacier Instant Retrieval** | archive, instant access | immediate |
| **Glacier Flexible Retrieval** | archive | minutes to hours |
| **Glacier Deep Archive** | compliance, 7–10 year retention | up to 12 hours |

Storage gets cheaper down the table; retrieval gets slower and per-request costs rise.

Two traps:

- **Minimum billing duration.** IA classes bill a minimum of 30 days, Glacier Deep Archive
  180. Transitioning an object that is deleted a week later costs *more* than leaving it in
  Standard.
- **One Zone-IA is one AZ.** Lose that AZ, lose the data. Only for things you can
  regenerate — thumbnails, derived data.

**Intelligent-Tiering** moves objects between tiers automatically based on access, for a
small monitoring fee per object. For unpredictable access patterns it is usually the right
default, and it is the one class with no retrieval fee.

---

## Versioning

Off by default. Once enabled it can be **suspended but never disabled** — existing versions
stay forever.

With versioning on:

- Overwriting creates a new version; the old one is retained
- Deleting adds a **delete marker** rather than removing data — the object disappears from
  listings but every version is still there, still billed
- Recovery is deleting the delete marker

The Terraform project enables it:

```hcl
resource "aws_s3_bucket_versioning" "receipts" {
  bucket = aws_s3_bucket.receipts.id
  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}
```

Note it is a **separate resource**, not a block inside `aws_s3_bucket`. That changed in AWS
provider v4 and is the single most common reason an older S3 Terraform example fails to
plan.

Versioning is the defence against the two failure modes backups usually miss: a bad deploy
overwriting good objects, and ransomware. Pair it with **MFA Delete** for anything
regulatory.

The cost consequence is real — every version is billed — which is what lifecycle rules are
for.

---

## Lifecycle policies

Rules that transition or expire objects on a schedule, evaluated daily. The Terraform
project expires old versions after 30 days:

```hcl
rule {
  id     = "expire-noncurrent-receipts"
  status = "Enabled"
  filter { prefix = "receipts/" }
  noncurrent_version_expiration { noncurrent_days = 30 }
}
```

A fuller policy usually combines four actions:

1. **Transition current versions** — Standard → Standard-IA at 30 days → Glacier at 90
2. **Transition noncurrent versions** — more aggressively, since they are rarely read
3. **Expire noncurrent versions** — the one above
4. **Abort incomplete multipart uploads** after 7 days

That last rule is the one almost everyone forgets. A failed multipart upload leaves parts
that are **billed but invisible in the console object listing**. Buckets quietly accumulating
cost for years are usually this.

---

## Encryption

**At rest** — every bucket has been encrypted by default since January 2023 (SSE-S3). The
options:

| Mode | Key held by | Use |
|---|---|---|
| **SSE-S3** | AWS, transparent | the default; fine for most things |
| **SSE-KMS** | AWS KMS, your key | audit trail per decrypt, cross-account control |
| **DSSE-KMS** | KMS, two layers | regulatory double encryption |
| **SSE-C** | you, sent per request | you manage keys entirely |

SSE-KMS adds a CloudTrail entry per operation and lets you revoke access by disabling the
key — powerful, but KMS request charges and quotas become real at high throughput.

**In transit** — TLS. Enforce it rather than assume it, with an explicit deny:

```json
{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:*",
  "Resource": ["arn:aws:s3:::yatri-receipts-archive/*"],
  "Condition": { "Bool": { "aws:SecureTransport": "false" } }
}
```

---

## Bucket policies and access control

Four mechanisms, which is three more than most people need:

1. **Block Public Access** — an account- and bucket-level override. On by default for new
   buckets. The Terraform project sets all four flags explicitly, because being explicit
   means a later change cannot quietly open the bucket:

   ```hcl
   block_public_acls       = true
   block_public_policy     = true
   ignore_public_acls      = true
   restrict_public_buckets = true
   ```

2. **Bucket policies** — resource-based JSON on the bucket. The main tool. Required for
   cross-account access.
3. **IAM policies** — identity-based, attached to a user or role. See
   [`../01-iam/`](../01-iam/).
4. **ACLs** — legacy, per-object. Disabled by default on new buckets and should stay that
   way.

Remember from IAM: `s3:ListBucket` takes the **bucket** ARN and `s3:GetObject` takes the
**object** ARN with `/*`. Mixing them up is the usual reason a policy does not work.

For public distribution, do not make the bucket public. Put **CloudFront** in front with an
Origin Access Control, keep the bucket private, and get caching and TLS as well.

For temporary access, use a **presigned URL** — a time-limited signed link that needs no AWS
credentials from the recipient.

---

## Common use cases

| Need | How |
|---|---|
| Static website | S3 + CloudFront + OAC, bucket private |
| Application uploads | presigned `PUT` straight from the browser |
| Data lake | Parquet partitioned by prefix, queried with Athena |
| Backups | versioning + lifecycle to Glacier + Object Lock |
| Terraform remote state | versioned bucket, SSE-KMS, state locking |
| Log aggregation | ALB/CloudTrail/VPC flow logs write natively |
| Event-driven processing | S3 event notification → Lambda or SQS |
| Compliance retention | Object Lock in Governance or Compliance mode |

---

## How this connects to the rest of the course

[`../../terraform-s3-demo/`](../../terraform-s3-demo/) creates a bucket with versioning,
public access blocked, AES256 encryption and a lifecycle rule — five of the sections above,
as six Terraform resources. Running it against LocalStack exercises the same S3 API that
real AWS serves.

Worth noting for Session 18's remote-state discussion: the bucket pattern Terraform itself
uses for state is this page's advice applied to Terraform — versioning on (so a corrupted
state file is recoverable), encryption on, public access blocked, and access limited to the
CI role.
