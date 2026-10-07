# IAM — Identity and Access Management

IAM is the service that answers one question on every single AWS API call: **is this
principal allowed to perform this action on this resource?** It is global, not regional, and
it is free.

Every other service in this folder depends on it. An EC2 instance that reads S3 does so
through IAM; a Terraform run that creates a bucket does so through IAM.

---

## What IAM evaluates

Every request carries four things, and a policy decision is made from them:

| | Example |
|---|---|
| **Principal** | the user, role or service making the call |
| **Action** | `s3:PutObject` |
| **Resource** | `arn:aws:s3:::yatri-receipts-archive/receipts/*` |
| **Condition** | source IP, MFA present, time of day, tag values |

The default is **deny**. Nothing is permitted until a policy says so.

---

## Users

An IAM user is a long-lived identity for a person or an external system. It can hold:

- a **console password** for browser sign-in
- **access keys** (an access key ID plus a secret) for the CLI and SDKs

A user is permanent credentials, which is exactly what makes it the thing to avoid where
possible. An access key committed to a repository works until someone notices. A role's
credentials expire in an hour.

The one user almost every account still needs is a break-glass admin with MFA, used only
when federation is broken.

**The root user** is separate and special. It is the email address the account was created
with, it cannot be restricted by any policy, and it can close the account and change
billing. The correct treatment: enable MFA on it, delete any access keys it has, and then do
not use it.

---

## Groups

A group is a collection of users that policies attach to. Users inherit every policy on
every group they belong to.

```
developers  ->  ReadOnlyAccess + S3 write on the dev bucket
operators   ->  EC2 and CloudWatch full access
finance     ->  Billing read only
```

A group is **not** an identity. Nothing assumes a group, and a group has no credentials; it
is purely a way to stop editing twenty users by hand. Groups cannot be nested.

---

## Roles

A role is a set of permissions with **no permanent credentials**. A principal *assumes* it
and receives temporary credentials — an access key, a secret and a session token — that
expire, typically in one hour.

Roles are the answer to most access questions:

- **EC2 instance profile.** The instance assumes a role and the SDK picks the credentials up
  from instance metadata automatically. No keys on disk, no keys in environment variables.
- **Cross-account access.** A role in the production account trusts a principal in the
  tooling account.
- **Federation.** Staff sign in through an identity provider and are mapped to a role, so
  AWS holds no passwords.
- **CI/CD via OIDC.** GitHub Actions presents a signed token and assumes a role. This is
  what removes long-lived AWS keys from repository secrets — the pattern used in Sessions
  16 and 17.
- **Service-linked roles.** One AWS service calling another on your behalf.

A role has two policies, and conflating them is the usual source of confusion:

- the **trust policy** — *who may assume this role* (the `Principal`)
- the **permissions policy** — *what the role can do once assumed*

Both must allow the call. A correct permissions policy with a trust policy that does not
name your principal produces `AccessDenied` on `sts:AssumeRole`, before any of the
permissions are ever consulted.

---

## Policies

A policy is a JSON document. This one allows read and write under a single prefix and
nothing else:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListTheBucketOnly",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::yatri-receipts-archive",
      "Condition": {
        "StringLike": { "s3:prefix": "receipts/*" }
      }
    },
    {
      "Sid": "ReadWriteReceiptObjects",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::yatri-receipts-archive/receipts/*"
    }
  ]
}
```

`Version` is a policy-language version, not a date you choose — `2012-10-17` is current.

Note that the bucket and the objects are **two different ARNs**. `s3:ListBucket` is a
bucket-level action and takes the bucket ARN; `s3:GetObject` is an object-level action and
takes the `/*` form. Getting this wrong — one ARN for both — is the most common reason an S3
policy silently does not work.

Policy types:

- **Identity-based** — attached to a user, group or role
- **Resource-based** — attached to the resource itself, like an S3 bucket policy or an SQS
  queue policy. These are the only way to grant cross-account access without a role.
- **Permissions boundaries** — a ceiling on what an identity's policies can grant
- **Service control policies (SCPs)** — organisation-wide ceilings, applied per account or
  organisational unit
- **Session policies** — passed at `AssumeRole` time to further narrow that session

---

## Permissions and how a decision is reached

Evaluation order, which matters:

1. **An explicit `Deny` anywhere wins.** Always. No later `Allow` can override it.
2. Otherwise, if any applicable policy has an `Allow`, the request is allowed.
3. Otherwise it is denied — the implicit default.

So an SCP denying `s3:DeleteBucket` across the organisation cannot be undone by an account
administrator attaching `AdministratorAccess`. The explicit deny holds.

For a cross-account call, **both** accounts must allow it: the caller's identity policy and
the resource policy (or the role's trust policy) in the target account.

---

## Least privilege

Grant the narrowest permission that lets the job succeed, then widen only on evidence.

In practice:

- Start from nothing and add actions as calls fail, rather than starting from `*` and
  trimming — trimming never happens.
- Scope `Resource` to specific ARNs. `"Resource": "*"` with `"Action": "s3:*"` is
  "every bucket in the account", which is rarely what was meant.
- Use **IAM Access Analyzer** to generate a policy from CloudTrail history of what an
  identity actually called.
- Check **Last Accessed** data in the console to find granted-but-unused services.
- Treat `iam:PassRole` as privileged. An identity that can pass a role to a service can
  often use it to acquire that role's permissions.

The action that deserves the most suspicion is `iam:*`. Anyone who can write IAM policies
can grant themselves anything, so `iam:CreatePolicyVersion` or `iam:AttachUserPolicy` is
effectively administrator access however narrow it looks.

---

## IAM best practices

1. **Lock the root user.** MFA on, no access keys, not used day to day.
2. **MFA for every human.** Hardware or authenticator app, not SMS.
3. **Roles instead of access keys.** For EC2, for CI/CD, for anything that can assume one.
4. **Rotate what must be long-lived,** and delete unused keys — 90 days is a common bar.
5. **Group policies, not per-user policies.** Scales, and stays auditable.
6. **One AWS account per environment.** The strongest blast-radius boundary there is;
   nothing in dev can touch prod.
7. **SCPs for guardrails** — block whole regions, block disabling CloudTrail.
8. **Permissions boundaries** so teams can create their own roles without privilege
   escalation.
9. **CloudTrail on, in every region,** to a bucket in a separate account.
10. **Alarm on root sign-in, policy changes and failed `AssumeRole` attempts.**
11. **Tag identities and use condition keys** — `aws:PrincipalTag` enables attribute-based
    access control rather than another bespoke policy.
12. **Never put credentials in code.** Use roles; fall back to Secrets Manager or SSM
    Parameter Store.

---

## Common use cases

| Need | Mechanism |
|---|---|
| App on EC2 reads S3 | instance profile with a role, scoped to one bucket prefix |
| GitHub Actions deploys to EKS | OIDC provider + role, trust policy scoped to one repo and branch |
| Staff log in to the console | federation through an identity provider, mapped to roles |
| Auditor needs read access | `SecurityAudit` / `ViewOnlyAccess` on a group |
| Lambda writes to DynamoDB | execution role with `dynamodb:PutItem` on one table ARN |
| Tooling account manages prod | role in prod whose trust policy names the tooling account |
| Contractor, 30 days, one bucket | role with a session duration limit, or a user with a boundary |
| Stop anyone deleting audit logs | resource-based bucket policy with an explicit `Deny` |

---

## How this connects to the rest of the course

The Terraform project in [`../../terraform-s3-demo/`](../../terraform-s3-demo/) authenticates
as an IAM principal on every API call — against LocalStack it is a dummy one, which is why
`skip_credentials_validation` is set. Pointed at real AWS, that principal would need
`s3:CreateBucket`, `s3:PutBucketVersioning`, `s3:PutBucketPublicAccessBlock`,
`s3:PutEncryptionConfiguration`, `s3:PutLifecycleConfiguration` and `s3:PutObject` — and
nothing more. Writing that policy out is the least-privilege exercise in miniature.
