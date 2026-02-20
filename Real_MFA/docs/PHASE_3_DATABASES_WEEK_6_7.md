# Phase 3 â€” Databases (Week 6â€“7)

## Purpose
This phase teaches database decisions, managed database operations, backup/recovery thinking, and performance basics on AWS.

You will learn not only how to create a database, but how to choose the right database for each workload.

---

## Week 6 (Database Foundation + Service Selection)

## 1) Database Types in AWS

### Relational Databases (SQL)
Use when strong consistency, joins, transactions, and structured schema are required.

AWS services:
- RDS (MySQL, PostgreSQL, MariaDB, SQL Server, Oracle)
- Aurora (high-performance managed relational)

### NoSQL Databases
Use when high scale, flexible schema, key-value/document access is needed.

AWS services:
- DynamoDB

### In-memory caching
Use for low-latency reads and reduced DB load.

AWS services:
- ElastiCache (Redis/Memcached)

### Data warehouse analytics (intro)
- Redshift for large-scale analytics workloads

---

## 2) RDS Basics

### Learn
- DB instance setup
- Engine selection
- Storage classes
- Multi-AZ deployment
- Backup retention
- Read replicas
- Parameter groups and option groups

### Practical outcomes
- Launch PostgreSQL/MySQL RDS
- Connect app from EC2
- Restrict inbound traffic via security groups

---

## 3) Aurora Basics

### Learn
- Aurora architecture overview
- Why Aurora can outperform standard RDS engines
- Reader endpoint/writer endpoint
- Failover behavior

### Practical outcomes
- Compare RDS vs Aurora use cases

---

## 4) DynamoDB Basics

### Learn
- Tables, items, attributes
- Partition key / sort key
- RCU/WCU concept
- On-demand vs provisioned capacity
- TTL, GSIs, LSIs basics

### Practical outcomes
- Create DynamoDB table
- Build key design for a sample feature (sessions/cart/events)

---

## Week 6 Labs

1. Deploy RDS PostgreSQL in private subnet
2. Connect app securely from EC2
3. Configure backups and snapshot
4. Create DynamoDB table and perform CRUD
5. Compare query patterns SQL vs DynamoDB

---

## Week 7 (Performance, Reliability, Security, Migration)

## 1) Performance Tuning Fundamentals

### RDS/Aurora performance points
- Index strategy
- Query optimization
- Connection pooling
- Read replicas for read-heavy loads
- Monitoring slow query logs

### DynamoDB performance points
- Partition key design to avoid hot partitions
- Right capacity mode selection
- Proper GSI usage

### Caching strategy
Use ElastiCache Redis for:
- Session storage
- Frequently accessed query results
- Rate limiting counters

---

## 2) Backup and Disaster Recovery

### Learn
- Automated backups
- Manual snapshots
- PITR (Point-in-time recovery)
- Cross-region snapshot copy

### Practical outcomes
- Restore a DB from snapshot
- Simulate recovery test

---

## 3) Database Security

### Core controls
- Private subnet placement
- Security group restrictions (only app tier access)
- Encryption at rest (KMS)
- TLS in transit
- Secrets Manager for DB credentials
- IAM authentication where supported

### Audit and compliance
- CloudTrail and DB logs integration
- Access monitoring and anomaly review

---

## 4) Database Migration Concepts

### Learn
- AWS DMS (Database Migration Service)
- Homogeneous vs heterogeneous migration
- Minimal downtime strategy
- Schema conversion considerations

### Practical outcomes
- Understand migration plan steps from on-prem/local DB to AWS managed DB

---

## 5) Data Modeling by Workload

### E-commerce example
Use:
- RDS/Aurora for orders, payments, users (transactional)
- DynamoDB for carts/session-like fast key-value access
- Redis for caching product/session hot data

### Logging/analytics example
Use:
- S3 + Athena/Redshift for analytical queries at scale

---

## Week 7 Labs

1. Enable Multi-AZ on relational DB
2. Create read replica and test read scaling
3. Set CloudWatch alarms for DB metrics (CPU, free storage, connections)
4. Restore from snapshot in test environment
5. Store DB credentials in Secrets Manager and rotate manually (practice)

---

## End of Phase 3 Outcomes

By end of Week 7, you should be able to:
- Choose correct AWS database service for a use case
- Deploy secure relational database on AWS
- Design DynamoDB keys for performance
- Implement backup and restore workflows
- Apply encryption, credentials security, and subnet isolation
- Use caching to reduce database load

---

## Decision Matrix (Quick Guide)

- Need ACID transactions + joins -> RDS/Aurora
- Need huge scale key-value/document -> DynamoDB
- Need ultra-fast cache/session counters -> ElastiCache Redis
- Need analytical warehousing -> Redshift

---

## Interview-Style Questions (Practice)

1. Why place RDS in private subnets?
2. Difference between Multi-AZ and Read Replica?
3. When would you pick DynamoDB over PostgreSQL?
4. How does PITR help in incident recovery?
5. How does Secrets Manager improve DB security?

---

## Common Mistakes to Avoid

- Publicly accessible production DB without strict reason
- No backup/restore testing
- Weak partition key in DynamoDB causing hotspots
- No index strategy in relational DB
- Credentials in `.env` committed to git
- No monitoring on connection saturation

---

## Recommended Practice Time

- Week 6: 12â€“14 hours
- Week 7: 12â€“14 hours

Total suggested for Phase 3: 24â€“28 hours

---

## Final Phase Integration Task (Strongly Recommended)

Build a mini production-like stack:
- App on EC2 or ECS
- RDS PostgreSQL for core transactional data
- DynamoDB for session/events store
- Redis cache for hot lookups
- CloudWatch alarms + dashboards
- Backup policy and recovery test report

This single project proves database architecture readiness.

---

## Final Note for Phase 3

Good cloud engineers do not just create databases. They design for security, reliability, recovery, and cost efficiency from day one.
