# DynamoDB and RDS — Database Services

Two managed database services that solve different problems. The decision between them is
not "NoSQL versus SQL" so much as **"do I know my access patterns in advance?"**

- **RDS** — managed relational databases. You still think in tables, joins and SQL; AWS
  handles the server, patching, backups and failover.
- **DynamoDB** — a managed NoSQL key-value and document store. No servers at all, scales to
  any throughput, but only answers the queries its keys were designed for.

---

# DynamoDB

## NoSQL

DynamoDB is key-value with document support. There are no joins, no `GROUP BY`, and no
schema beyond the key attributes.

What you get for giving those up:

- Single-digit millisecond latency at effectively any scale
- No instance to size, patch or fail over — it is genuinely serverless
- Throughput that scales horizontally without a rewrite

What it costs you:

- **Queries must be designed up front.** The data model follows the access patterns, not
  the entities. A question nobody anticipated usually means a new index or a full table
  scan.
- No joins — related data is denormalised or fetched in separate calls
- No transactions across arbitrary rows at arbitrary scale, though `TransactWriteItems`
  covers up to 100 items

## Tables, items and attributes

```
Table: yatri-bookings
  Item: { "booking_id": "B-1001",      <- partition key
          "created_at": "2026-10-07",  <- sort key
          "passenger":  "A. Sharma",
          "route":      { "from": "BOM", "to": "DEL" },   <- nested document
          "seats":      [ "12A", "12B" ] }
```

- **Table** — a collection of items. Regional, not tied to an AZ.
- **Item** — one record, max **400 KB**. The rough equivalent of a row.
- **Attribute** — a field. Every item must have the key attributes; everything else varies
  item to item. Two items in one table need not resemble each other at all.

Types include scalars (string, number, binary, boolean, null), documents (list, map) and
sets. That 400 KB limit is a hard ceiling — larger payloads go to S3 with the key stored in
the item.

## Partition key

The **partition key** (hash key) determines which physical partition stores the item.
DynamoDB hashes it and distributes accordingly.

Choosing it well is the single most important design decision:

- **High cardinality.** Many distinct values.
- **Even access distribution.** A key like `status` with values `active`/`inactive` creates
  a *hot partition* — most traffic hitting one partition, throttling while the table as a
  whole is far under capacity.
- A key such as `booking_id` or `user_id` spreads naturally.

With no sort key, the partition key alone must be unique.

## Sort key

The optional second half of a composite primary key. Items sharing a partition key are
stored together, **sorted** by the sort key — which is what makes range queries possible:

```
booking_id = "B-1001" AND created_at BETWEEN "2026-01" AND "2026-10"
```

`partition key + sort key` must be unique together. This is also how one-to-many
relationships are modelled: all of a user's orders share the partition key `USER#123` and
are separated by sort keys `ORDER#...`.

**Query vs Scan** is the distinction that matters for cost: `Query` targets one partition
key and is efficient; `Scan` reads the entire table and should be treated as a mistake in
production code.

Two index types widen access:

- **LSI** — alternative sort key, same partition key. Must be created with the table.
- **GSI** — entirely different partition and sort key, effectively a second view of the
  table. Can be added later, has its own capacity, and is eventually consistent.

## Capacity, and other features

- **On-demand** — pay per request, no planning. The right default.
- **Provisioned** — set read/write capacity units, optionally auto-scaled. Cheaper for
  steady, predictable traffic.
- **DynamoDB Streams** — a change log of every write, consumable by Lambda. The basis for
  event-driven architectures and replication.
- **TTL** — a timestamp attribute after which items are deleted free of charge.
- **Global tables** — multi-region, multi-active replication.
- **DAX** — an in-memory cache that cuts reads to microseconds.
- **PITR** — point-in-time recovery to any second in the last 35 days.

## DynamoDB use cases

| Need | Why it fits |
|---|---|
| Session store | key lookup, TTL expiry, massive write rates |
| Shopping cart | one item per user, no joins needed |
| IoT / telemetry ingestion | high write throughput, time-series sort key |
| Leaderboards | partition by game, sort by score |
| User profiles | single-item fetch by `user_id` |
| Event sourcing | append-only writes plus Streams |

Poor fits: ad-hoc reporting, anything needing joins or aggregation across the table, and
relational integrity across entities.

---

# RDS

## Relational database

RDS runs a real relational engine on an EC2 instance that AWS manages for you. The database
itself is unmodified — the application connects with a standard driver and does not know it
is on RDS.

AWS takes over provisioning, OS and engine patching, automated backups, failover and
replication. You keep schema design, query tuning, indexing and connection management.

## Supported engines

| Engine | Notes |
|---|---|
| **PostgreSQL** | the usual default for new work |
| **MySQL** | widest ecosystem compatibility |
| **MariaDB** | MySQL fork |
| **Oracle** | bring your own licence or licence-included |
| **SQL Server** | several editions |
| **Aurora** (MySQL/PostgreSQL compatible) | AWS's own, see below |

**Aurora** is worth separating out: a rewritten storage layer with a distributed, six-way
replicated volume across three AZs, up to 15 low-lag read replicas, and failover in seconds
rather than a minute. **Aurora Serverless v2** scales capacity continuously and is the
natural fit for spiky or unpredictable workloads.

## DB instances

An instance is sized like EC2 — `db.t4g.micro`, `db.m6g.large`, `db.r6g.xlarge` — with the
same family logic: T burstable, M balanced, R memory-optimised. Databases are usually
memory-bound, so R is common in production.

Storage choices: General Purpose SSD (gp3), Provisioned IOPS (io1/io2) for latency-sensitive
work, with **storage autoscaling** available so the volume grows before it fills.

Scaling is mostly **vertical** — a bigger instance class, which involves a restart (brief if
Multi-AZ). Horizontal scaling applies to reads only, via replicas.

## Security

- **Place it in a private subnet.** An RDS instance should not be publicly accessible; the
  `publicly_accessible` flag exists and should stay `false`.
- **Security group** allowing the database port only from the application tier's security
  group — the group-as-source pattern from [`../02-ec2/`](../02-ec2/).
- **DB subnet group** spanning at least two AZs; required for Multi-AZ.
- **Encryption at rest** via KMS. It must be enabled **at creation** — an unencrypted
  instance cannot be encrypted later except by snapshot-restore into a new one.
- **TLS in transit**, using the RDS CA bundle.
- **IAM database authentication** issues short-lived tokens instead of passwords.
- **Secrets Manager** for credentials, with automatic rotation.

## Backups

- **Automated backups** — daily snapshot plus continuous transaction logs, enabling
  point-in-time recovery to any second within the retention window (1–35 days). Retention
  `0` disables backups entirely, which is a setting worth checking.
- **Manual snapshots** — kept until explicitly deleted, and the only ones that survive
  instance deletion.
- Taken from the standby in Multi-AZ, so there is no I/O pause on the primary.
- Restoring **always creates a new instance** — it never restores in place, so the endpoint
  changes and the application must be repointed.

## Multi-AZ

A synchronous standby in a second Availability Zone.

- The standby serves **no read traffic**. It exists purely for availability.
- Failover is automatic, takes roughly 60–120 seconds, and works by repointing the DNS
  endpoint — the application reconnects to the same hostname.
- Roughly doubles cost.
- **Multi-AZ DB cluster** is a newer variant: two readable standbys and faster failover.

This is availability, not scalability, and not a backup. It protects against AZ failure and
instance failure; it replicates a bad `DELETE` to the standby instantly.

## Read replicas

**Asynchronous** copies that serve read traffic.

- Up to 15 (Aurora) or 5 (RDS engines) per primary
- Can live in another region, which doubles as disaster recovery
- Can be **promoted** to a standalone primary
- **Eventually consistent** — replication lag means a read immediately after a write may
  return stale data

| | Multi-AZ | Read replica |
|---|---|---|
| Replication | synchronous | asynchronous |
| Purpose | availability | read scaling |
| Serves reads | no | yes |
| Failover | automatic | manual promotion |
| Cross-region | no | yes |

The application must route deliberately — writes to the cluster endpoint, reads to the
reader endpoint. Nothing does this automatically.

## RDS use cases

| Need | Why it fits |
|---|---|
| Transactional application | ACID, foreign keys, joins |
| Reporting and analytics | ad-hoc SQL, aggregation |
| Lift-and-shift migration | same engine, no code changes |
| Read-heavy workload | read replicas |
| Unpredictable load | Aurora Serverless v2 |

---

## Choosing between them

| | DynamoDB | RDS |
|---|---|---|
| Model | key-value / document | relational |
| Schema | per item | fixed, migrated |
| Query flexibility | by key and index only | arbitrary SQL |
| Joins | no | yes |
| Scaling | automatic, horizontal | vertical + read replicas |
| Servers | none | instances you size |
| Latency | single-digit ms, flat | depends on query and instance |
| Cost model | per request | per instance-hour |

**Choose DynamoDB** when the access patterns are known and stable, scale is large or spiky,
and latency must stay flat. **Choose RDS** when the data is relational, the queries are not
all known in advance, or there is existing SQL to preserve.

The honest default for a new application with uncertain requirements is RDS — a relational
schema tolerates questions nobody thought of, and DynamoDB does not. Using both in one
system is normal: orders in RDS, sessions in DynamoDB.

---

## How this connects to the rest of the course

The Session 21 capstone runs PostgreSQL in a container via Docker Compose and, in
Kubernetes, as a StatefulSet with a PersistentVolumeClaim. RDS is what replaces that in
production — the same engine and the same connection string, with the backup, failover and
patching moved to AWS. The storage argument is the one from Session 13: a database in a Pod
is only as durable as its PVC and the reclaim policy behind it.
