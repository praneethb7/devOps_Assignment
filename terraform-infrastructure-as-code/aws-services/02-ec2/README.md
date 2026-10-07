# EC2 — Elastic Compute Cloud

EC2 is rented virtual machines. You choose an operating system image, a hardware size and a
network position, and AWS starts a server you have root on and pay for by the second.

It is the service that makes the cloud's cost model concrete: the machine exists only while
it is running, and so does the bill.

---

## What is EC2

An **instance** is one virtual machine running on AWS hypervisors in a specific
Availability Zone. You get full operating system control; AWS manages the hardware,
hypervisor, physical network and power.

What AWS does *not* manage is everything inside the instance — patching, the application,
the web server, log rotation. That division is the whole reason managed services like RDS
exist: the same database on EC2 is yours to back up and upgrade.

---

## AMI — Amazon Machine Image

The template an instance boots from. It contains the root volume snapshot, the operating
system, pre-installed software and the block device mapping.

AMIs are **region-specific** — an AMI ID in `ap-south-1` is meaningless in `us-east-1`, and
hardcoding one is the most common reason a working Terraform module fails when someone
changes region. Look it up instead:

```hcl
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}
```

Sources: AWS-published (Amazon Linux, Ubuntu, Windows), Marketplace, community, or your
own. Building your own — a "golden image" with the agent and dependencies baked in — is the
standard way to cut boot time and guarantee that every instance is identical.

---

## Instance types

A family letter, a generation number and a size: `t3.micro`, `m6i.large`, `c7g.xlarge`.

| Family | Optimised for | Typical use |
|---|---|---|
| **T** | burstable, cheap | dev boxes, low-traffic sites |
| **M** | balanced | general application servers |
| **C** | compute | batch processing, game servers, CI runners |
| **R / X** | memory | caches, in-memory databases |
| **I / D** | storage, local NVMe | data warehouses |
| **P / G / Inf** | GPU / accelerators | training and inference |

A `g` in the name (`c7g`) means **Graviton**, AWS's ARM processors — materially cheaper per
unit of work, but the AMI and every binary must be ARM builds.

**The T-family catch:** burstable instances earn CPU credits while idle and spend them when
busy. Run out and the instance is throttled to its baseline — a `t3.micro` baseline is 10%
of a vCPU. A production service that looks fine for a week and then collapses under sustained
load is usually a T instance that has exhausted its credits. For steady load, use M or C.

---

## Key pairs

An SSH public/private key pair. AWS stores the public key and injects it into the instance's
`~/.ssh/authorized_keys` at first boot; you keep the private key.

**AWS never stores the private key.** Lose the `.pem` and there is no recovery — you detach
the root volume, attach it to another instance, edit `authorized_keys`, and reattach.

```bash
chmod 400 yatri-key.pem                        # SSH refuses a world-readable key
ssh -i yatri-key.pem ec2-user@<public-ip>      # Amazon Linux
ssh -i yatri-key.pem ubuntu@<public-ip>        # Ubuntu
```

The modern alternative is **Session Manager**: connect through the SSM agent and IAM, with
no key pair, no open port 22, and no public IP at all. Every session is logged to
CloudTrail. For anything new, prefer it.

---

## Security Groups

A stateful virtual firewall attached to an instance's network interface.

- Rules are **allow only** — there is no deny rule
- **Stateful**: allow traffic in and the response goes out automatically, whatever the
  outbound rules say
- Default inbound is deny-all; default outbound is allow-all
- Multiple groups can attach to one instance; rules are the union
- A rule's source can be a CIDR **or another security group**

That last point is the one worth using. Rather than hardcoding the web tier's IP range on
the database:

```
db-sg   inbound  3306  source: web-sg
```

The database accepts MySQL from anything in `web-sg` and nothing else, and it keeps working
as web instances come and go — no CIDR maintenance, no accidental widening.

The deployment rule of thumb: `0.0.0.0/0` is acceptable on 80 and 443 for a public load
balancer. On 22, 3389 or any database port it is an incident waiting to happen.

Security groups are instance-level. **Network ACLs** are subnet-level, stateless and *do*
support deny — see [`../04-vpc/`](../04-vpc/).

---

## EBS — Elastic Block Store

Network-attached block storage that appears to the instance as a disk. Unlike the instance,
an EBS volume is durable: it survives a stop/start and can be detached and attached to
another instance in the same AZ.

| Type | Character | Use |
|---|---|---|
| **gp3** | general SSD, IOPS set independently of size | the sane default |
| **gp2** | general SSD, IOPS tied to size | legacy; gp3 is cheaper and faster |
| **io2 / io2 Block Express** | provisioned IOPS, highest durability | production databases |
| **st1** | throughput HDD | big sequential reads, logs |
| **sc1** | cold HDD | archives you rarely touch |

Three properties that catch people out:

- **An EBS volume lives in one Availability Zone.** It cannot cross AZs. To move it, take a
  snapshot — snapshots are regional — and create a volume from it in the other AZ.
- **`DeleteOnTermination` defaults to true for the root volume.** Terminate the instance and
  the root disk is destroyed. Attached data volumes default to false.
- **Snapshots are incremental** but each one is independently restorable; deleting an old
  snapshot never breaks a newer one.

**Instance store** is the other kind of disk: physically attached NVMe, very fast, and
**ephemeral**. Stop the instance and the data is gone. It is for scratch and caches only.

---

## Public vs private IP

Every instance gets a **private IPv4** from its subnet's CIDR. It is stable for the
instance's life and is how things inside the VPC reach each other.

A **public IPv4** is optional. It is not configured inside the operating system —
`ip addr` on the instance only ever shows the private address. The internet gateway performs
one-to-one NAT between them.

| | Private | Public | Elastic IP |
|---|---|---|---|
| Always assigned | yes | no | no |
| Survives stop/start | yes | **no** | yes |
| Reachable from internet | no | yes | yes |
| Costs money | no | small hourly charge | charged when unattached |

**The public IP changes on every stop/start.** That is what an **Elastic IP** fixes: a
static public address you own and attach. Note the inverted billing — an Elastic IP costs
you *while it is not attached to a running instance*, which is AWS discouraging hoarding.

For anything real, do not rely on instance IPs at all. Put a load balancer in front and
point DNS at that.

---

## Instance lifecycle

```
          launch
            |
        [pending]
            |
        [running] <-------- start -------- [stopped]
         |   |  \                              ^
         |   |   `------- stop ----------------'
         |   |
         |   `--- reboot ---> [running]
         |
      terminate
            |
     [shutting-down]
            |
      [terminated]
```

What each transition actually does:

- **Stop** — the VM is shut down, EBS volumes are kept, billing for compute stops. The
  public IP is released, instance store data is lost, and the instance will very likely boot
  on different physical hardware.
- **Reboot** — an OS-level restart. Same host, same IP, no state lost.
- **Terminate** — irreversible. Root volume is deleted by default.
- **Hibernate** — RAM is written to the root EBS volume and restored on start. Needs to be
  enabled at launch.

You still pay for EBS volumes and Elastic IPs while an instance is stopped. "Stopped" is not
"free".

### Purchase options

| Option | Discount | Trade-off |
|---|---|---|
| **On-Demand** | none | no commitment |
| **Savings Plans / Reserved** | up to ~72% | 1 or 3 year commitment |
| **Spot** | up to ~90% | can be reclaimed with a 2-minute warning |
| **Dedicated Host** | — | physical isolation, licence compliance |

Spot is excellent for CI runners, batch jobs and stateless workers behind a queue, and wrong
for anything that cannot be interrupted.

---

## Common use cases

| Need | Shape |
|---|---|
| Web application | Auto Scaling group across AZs behind an ALB |
| CI/CD runners | Spot instances in a private subnet |
| Legacy software that cannot be containerised | single instance, golden AMI |
| Batch/ML training | C or P family, Spot, scaled to zero when idle |
| Bastion access | Session Manager instead of a bastion host |
| Self-managed database | R family + io2 — but ask why not RDS first |

---

## How this connects to the rest of the course

Session 19 provisions an EC2 instance with Terraform inside a custom VPC — public subnet,
internet gateway, security group — which is this page and
[`../04-vpc/`](../04-vpc/) assembled into one `terraform apply`. The security group there
allows 22 and 80 and nothing else, and the instance gets a public IP only because it sits
in a subnet with `map_public_ip_on_launch` enabled.
