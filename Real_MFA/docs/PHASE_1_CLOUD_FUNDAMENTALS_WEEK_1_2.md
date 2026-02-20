# Phase 1 â€” Cloud Fundamentals (Week 1â€“2)

## Purpose
This phase builds the base required for every AWS role: cloud concepts, core architecture thinking, basic security mindset, and account-level setup.

If this phase is strong, every next AWS topic becomes easier.

---

## Week 1 â€” Cloud Thinking + AWS Foundation

## 1) Cloud Computing Basics

### What is cloud computing?
Cloud computing means using on-demand computing resources over the internet instead of owning physical hardware.

### Why cloud?
- Faster setup
- Lower upfront cost
- Elastic scaling
- Better reliability
- Global delivery

### Main cloud service models
- IaaS (Infrastructure as a Service): You manage OS and app, provider manages hardware
- PaaS (Platform as a Service): You deploy app, provider manages platform/runtime
- SaaS (Software as a Service): Ready-to-use software

### Deployment models
- Public cloud
- Private cloud
- Hybrid cloud
- Multi-cloud

### Shared Responsibility Model
AWS handles security of the cloud, customer handles security in the cloud.

---

## 2) Core AWS Global Infrastructure

### Regions
Independent geographic areas (for latency, compliance, and disaster planning).

### Availability Zones (AZs)
Isolated data centers inside a region.

### Edge Locations
Used by CDN services like CloudFront for low latency content delivery.

### Important design idea
Use multiple AZs for high availability.

---

## 3) AWS Account Setup Essentials

### Create an AWS account with best practices
- Secure root account
- Enable MFA on root user
- Avoid daily work from root account
- Configure billing alerts

### IAM basics for day 1
- User
- Group
- Role
- Policy

### First recommended setup
- Create admin IAM user
- Enable MFA for admin user
- Set strong password policy
- Turn on CloudTrail
- Turn on billing alarm in CloudWatch

---

## 4) Basic Networking Concepts (High-level)

Before VPC deep dive, understand:
- IP address
- CIDR
- Public vs private network
- DNS basics
- Firewall concept

---

## 5) Cloud Economics Intro

### OPEX vs CAPEX
- CAPEX: Buy physical infrastructure upfront
- OPEX: Pay monthly based on usage

### AWS pricing mindset
- Pay-as-you-go
- Reserved/Savings plans for predictable usage
- Spot for interruptible workloads

### Cost awareness early
- Tag resources
- Delete unused resources
- Set budgets

---

## Week 1 Hands-on Labs

1. Create AWS account and secure it
2. Enable MFA for root + IAM admin
3. Create IAM users and groups
4. Attach least-privilege policies
5. Enable billing alerts
6. Explore AWS console and service categories

---

## Week 2 â€” Security Foundation + Service Familiarization

## 1) IAM Deep Basics

### IAM identities
- Users: person identities
- Roles: temporary permissions
- Groups: permission grouping

### IAM policies
JSON-based allow/deny rules for actions on resources.

### Least privilege principle
Give only required permissions, nothing extra.

### Access management checks
- Rotate credentials
- Use role-based access
- Avoid hardcoded keys

---

## 2) Basic Governance Services

### CloudTrail
Audit log of API calls and account activity.

### CloudWatch
Metrics, logs, alarms.

### AWS Config (intro)
Track configuration changes and compliance checks.

### Trusted Advisor (intro)
Cost, performance, fault tolerance, security recommendations.

---

## 3) AWS Core Service Orientation (No deep implementation yet)

Understand what each does:
- EC2: virtual servers
- S3: object storage
- RDS: managed relational DB
- Lambda: serverless compute
- VPC: virtual network
- Route 53: DNS
- ELB: traffic distribution

Goal: know when to use what.

---

## 4) Architecture Principles (Foundation)

From AWS Well-Architected pillars (intro level):
- Operational Excellence
- Security
- Reliability
- Performance Efficiency
- Cost Optimization
- Sustainability

---

## 5) Cloud Career Mapping (Optional but useful)

Roles aligned with this phase:
- Cloud Support Associate
- Junior Cloud Engineer
- DevOps trainee
- Backend developer entering cloud

---

## Week 2 Hands-on Labs

1. Write and attach custom IAM policy (read-only S3)
2. Use role assumption between two IAM users (basic test)
3. Create CloudWatch alarm for billing metric
4. Enable CloudTrail and verify activity logs
5. Create AWS budget and notification threshold

---

## End of Phase 1 Outcomes

By end of Week 2, you should be able to:
- Explain cloud models and shared responsibility clearly
- Secure AWS account correctly
- Build IAM users/roles/policies safely
- Understand regions/AZ/edge architecture
- Read AWS console and identify right service category
- Apply basic cost and monitoring guardrails

---

## Quick Self-Assessment

If you can answer these without notes, Phase 1 is complete:

1. Difference between IAM user and role?
2. Why multi-AZ deployment matters?
3. What does CloudTrail record?
4. What is least privilege and why critical?
5. How do you prevent surprise AWS billing?

---

## Mini Revision Sheet

- Cloud = on-demand IT resources
- AWS region = geographic zone
- AZ = isolated DC in a region
- IAM = identity and access control
- CloudTrail = account/API audit logs
- CloudWatch = metrics/logs/alarms
- Shared responsibility = AWS + customer split

---

## Recommended Practice Time

- Theory: 10â€“12 hours total
- Hands-on: 8â€“10 hours total
- Review and quiz: 2â€“3 hours

Total suggested for Phase 1: 20â€“25 hours

---

## Optional Certification Alignment

This phase aligns strongly with:
- AWS Certified Cloud Practitioner (CLF-C02) foundation topics
- Early prep for Solutions Architect Associate

---

## Common Mistakes to Avoid

- Using root account for daily work
- Ignoring MFA
- Attaching AdministratorAccess everywhere
- Skipping billing alarms
- Ignoring region placement and latency

---

## Final Note for Phase 1

Do not rush. A strong cloud foundation reduces confusion in networking, compute scaling, and production architecture later.
