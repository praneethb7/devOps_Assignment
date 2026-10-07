# VPC — Virtual Private Cloud

A VPC is a private, logically isolated network inside AWS that you control: the address
range, the subnets, the routing and the firewalls. Every EC2 instance, RDS database and load
balancer lands inside one.

It is the service where mistakes are least visible and most expensive — a database in a
public subnet looks identical to one in a private subnet until someone scans the address.

---

## What is a VPC

A VPC spans **one region** and covers every Availability Zone in it. Nothing inside it is
reachable from the internet until you add the components that make it so.

Every account comes with a **default VPC** per region: `172.31.0.0/16`, one public subnet
per AZ, an internet gateway already attached, and `map_public_ip_on_launch` on. It is
convenient and it is why an instance launched with all defaults is immediately on the public
internet. For anything real, build your own.

---

## CIDR

A CIDR block is an address range written as `network/prefix`. The prefix is how many leading
bits are fixed; the rest address hosts.

| CIDR | Addresses | Usable | Typical role |
|---|---|---|---|
| `/16` | 65,536 | 65,531 | a whole VPC |
| `/20` | 4,096 | 4,091 | a large subnet |
| `/24` | 256 | 251 | a normal subnet |
| `/28` | 16 | 11 | the smallest AWS allows |

AWS **reserves five addresses in every subnet**, which is why usable is always five fewer:

| Address in `10.0.1.0/24` | Reserved for |
|---|---|
| `10.0.1.0` | network address |
| `10.0.1.1` | VPC router |
| `10.0.1.2` | DNS (the VPC `.2` resolver) |
| `10.0.1.3` | future use |
| `10.0.1.255` | broadcast (reserved; AWS does not support broadcast) |

Rules that bite later:

- VPC CIDR must be between `/16` and `/28`
- **The VPC CIDR cannot be changed after creation** — you can add secondary blocks, but the
  primary is fixed. Size generously.
- Use the private ranges: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- **Do not overlap** with any network you might ever peer with or connect by VPN. Overlapping
  CIDRs cannot be peered, and this is the reason large organisations end up rebuilding VPCs.

A sane starting layout for `10.0.0.0/16` across two AZs:

```
10.0.1.0/24   public  ap-south-1a
10.0.2.0/24   public  ap-south-1b
10.0.11.0/24  private ap-south-1a
10.0.12.0/24  private ap-south-1b
```

---

## Subnets

A subnet is a slice of the VPC CIDR that lives in **exactly one Availability Zone**. That
is its defining property — a subnet cannot span AZs, which is why high availability always
means at least one subnet per AZ.

A subnet is **public or private purely because of its route table**. There is no flag called
"public". If the route table has a route to an internet gateway, it is public. That is the
whole distinction.

---

## Route tables

A set of rules matched by destination, **longest prefix wins**. Every route table has an
unremovable `local` route covering the VPC CIDR, which is what lets subnets talk to each
other with no configuration at all.

Public subnet:

| Destination | Target |
|---|---|
| `10.0.0.0/16` | `local` |
| `0.0.0.0/0` | `igw-xxxx` |

Private subnet:

| Destination | Target |
|---|---|
| `10.0.0.0/16` | `local` |
| `0.0.0.0/0` | `nat-xxxx` |

Each subnet associates with exactly one route table; one route table can serve many
subnets. Unassociated subnets fall back to the VPC's **main** route table — an easy way to
make a subnet accidentally public, so associate explicitly.

---

## Internet Gateway

A horizontally scaled, highly available component attached to the VPC that allows traffic
to and from the internet. It also performs the one-to-one NAT between an instance's private
address and its public address.

Three things must **all** be true for an instance to be reachable from the internet:

1. an internet gateway is attached to the VPC
2. the subnet's route table has `0.0.0.0/0 -> igw`
3. the instance has a public IP or Elastic IP

Plus security group and NACL rules allowing the traffic. Missing any one produces a timeout,
and the usual culprit is #3 — `map_public_ip_on_launch` is off by default on custom
subnets.

An **egress-only internet gateway** is the IPv6 equivalent of a NAT gateway: outbound only.

---

## NAT Gateway

Lets instances in **private** subnets reach the internet — for package updates, API calls,
pulling container images — while remaining unreachable from it. Outbound connections are
translated to the NAT gateway's Elastic IP; inbound connections cannot be initiated.

A NAT gateway is placed **in a public subnet** and is **AZ-scoped**. One per AZ is the
production pattern: a single NAT gateway makes the other AZs depend on the one it sits in,
which quietly converts a one-AZ outage into a multi-AZ one.

It is also, for small environments, often the largest line on the bill — an hourly charge
per gateway plus a per-GB data processing charge. Two mitigations:

- **VPC endpoints** for S3 and DynamoDB (gateway endpoints, no hourly charge) keep that
  traffic off the NAT entirely
- a **NAT instance** — a self-managed EC2 instance — is cheaper but is a single point of
  failure you now maintain

| | NAT Gateway | NAT Instance |
|---|---|---|
| Managed | yes | no |
| HA | within one AZ | you build it |
| Bandwidth | up to 100 Gbps | instance-dependent |
| Security groups | not applicable | yes |

---

## Security Groups

Covered in [`../02-ec2/`](../02-ec2/). The short version, for contrast with NACLs:
instance-level, **stateful**, allow-rules only, evaluated as the union of all attached
groups.

---

## Network ACLs

A **stateless** firewall at the **subnet** boundary. The second layer of defence, and the
one that behaves unlike anything else in AWS.

- Rules are numbered and evaluated **in order, lowest first**; the first match wins and
  evaluation stops
- Both `ALLOW` and `DENY` are available — this is the only place you can express "deny"
- There is an implicit `DENY *` at the end
- **Stateless**: a response is not automatically permitted. Allowing inbound 443 is useless
  unless outbound ephemeral ports (1024–65535) are also allowed.
- The default NACL allows all traffic in both directions; a custom one denies everything
  until you write rules

That stateless/ephemeral-port detail is the classic VPC debugging story: security groups
look right, routes look right, and traffic still fails because a custom NACL allows inbound
443 but not the outbound reply.

| | Security Group | Network ACL |
|---|---|---|
| Level | instance / ENI | subnet |
| State | stateful | stateless |
| Rules | allow only | allow and deny |
| Evaluation | all rules, union | in number order, first match |
| Default | deny in, allow out | default NACL allows all |

Use security groups as the primary control. Reach for NACLs to block a specific CIDR or to
enforce a coarse subnet-wide boundary.

---

## Public vs private subnet

| | Public | Private |
|---|---|---|
| Route for `0.0.0.0/0` | internet gateway | NAT gateway, or none |
| Inbound from internet | possible | not possible |
| Outbound to internet | direct | via NAT |
| Belongs there | load balancers, bastions, NAT gateways | application servers, databases, caches |

The standard three-tier layout:

```
Internet
   |
[ IGW ]
   |
Public subnets   ->  Application Load Balancer, NAT gateway
   |
Private subnets  ->  application servers  (no public IP)
   |
Private subnets  ->  RDS, ElastiCache     (no NAT route either)
```

The database tier gets no internet route in either direction. It does not need one, and
removing it removes a class of exfiltration risk.

---

## Other components worth knowing

- **VPC endpoints** — reach AWS services without traversing the internet. *Gateway*
  endpoints (S3, DynamoDB) are free and route-table based; *Interface* endpoints (PrivateLink)
  put an ENI in your subnet and charge hourly.
- **VPC peering** — one-to-one connection between two VPCs. **Not transitive**: A↔B and B↔C
  does not give A↔C.
- **Transit Gateway** — a hub for many VPCs and on-premises connections; what peering
  becomes once there are more than a handful.
- **VPC Flow Logs** — records of accepted and rejected traffic, to CloudWatch or S3. The
  first thing to enable when connectivity is mysteriously failing.

---

## Common use cases

| Need | Shape |
|---|---|
| Public web app | ALB in public subnets, app in private, RDS in isolated private |
| Internal-only service | private subnets, internal ALB, no IGW |
| Hybrid connectivity | Site-to-Site VPN or Direct Connect, non-overlapping CIDRs |
| Strict compliance | private subnets + interface endpoints, no NAT at all |
| Multi-account | Transit Gateway, or shared subnets via RAM |

---

## How this connects to the rest of the course

Session 19 builds exactly this with Terraform: a VPC, an internet gateway, a public subnet
with `map_public_ip_on_launch`, a route table associating `0.0.0.0/0` with the gateway, a
security group, and an EC2 instance inside it. Reading that `main.tf` alongside this page is
the fastest way to see which component does which job — and `terraform destroy` shows the
dependency order in reverse, since the gateway cannot be deleted until the instance using
it is gone.
