# Phase 2 â€” Core AWS Services (Week 3â€“6)

## Purpose
This phase converts cloud theory into real implementation. You will deploy workloads, design network layers, expose applications securely, and monitor operations.

---

## Week 3 â€” Compute + Storage Core

## 1) EC2 Fundamentals

### Learn
- EC2 instance lifecycle
- AMI, instance types
- Security groups
- Key pairs
- EBS basics

### Practical outcomes
- Launch Linux EC2
- Connect using SSH
- Install web server (Nginx/Apache)
- Host a simple web page

### Production awareness
- Use minimal open ports
- Keep OS updated
- Use IAM role for instance access

---

## 2) S3 Fundamentals

### Learn
- Buckets and objects
- Storage classes
- Bucket policies and ACL (prefer policy-based)
- Versioning and lifecycle
- Static website hosting

### Practical outcomes
- Create secure bucket
- Upload static assets
- Enable versioning
- Configure lifecycle to transition/archive objects

---

## 3) IAM + EC2 + S3 integration

### Goal
Allow EC2 to access S3 without hardcoded keys using IAM instance roles.

---

## Week 3 Labs

1. Launch EC2 and host static app
2. Attach IAM role to EC2 for S3 read access
3. Create S3 lifecycle rule
4. Create private + public bucket comparison (security view)

---

## Week 4 â€” Networking + High Availability

## 1) VPC Core Concepts

### Learn
- VPC CIDR design
- Public subnet vs private subnet
- Route tables
- Internet gateway
- NAT gateway (outbound internet for private subnet)
- NACL vs Security Groups

### Practical outcomes
- Create custom VPC
- Build 2 public + 2 private subnets across AZs
- Route internet traffic correctly

---

## 2) Load Balancing + Auto Scaling

### Elastic Load Balancer (ALB)
Distributes incoming traffic across multiple EC2 instances.

### Auto Scaling Group (ASG)
Automatically adds/removes EC2 instances based on metrics.

### Practical outcomes
- Deploy web app on ASG
- Front it with ALB
- Configure health checks
- Validate automatic scale behavior

---

## 3) Route 53 Basics

### Learn
- Hosted zones
- Record types (A, CNAME, Alias)
- Routing policies (simple, weighted, failover)

### Practical outcomes
- Point domain/subdomain to ALB

---

## Week 4 Labs

1. Build custom VPC architecture
2. Deploy ALB + ASG web tier
3. Configure Route 53 DNS mapping
4. Simulate traffic and verify scaling

---

## Week 5 â€” Serverless + APIs + Messaging

## 1) AWS Lambda

### Learn
- Event-driven execution
- Stateless functions
- Timeout/memory tuning
- IAM execution role

### Practical outcomes
- Create Lambda function (Python/Node)
- Trigger via API Gateway and S3 events

---

## 2) API Gateway

### Learn
- REST endpoint creation
- Integrating API with Lambda
- CORS setup
- Basic auth/throttling concepts

### Practical outcomes
- Build simple CRUD API with Lambda + API Gateway

---

## 3) Messaging and Async Patterns

### SQS
Queue-based decoupling.

### SNS
Pub/sub notifications.

### EventBridge (intro)
Event routing bus for AWS services/app events.

### Practical outcomes
- Push events to SQS
- Publish notification through SNS
- Trigger Lambda from queue/event

---

## Week 5 Labs

1. Build serverless endpoint with API Gateway + Lambda
2. Add SQS in async flow
3. Add SNS email notification
4. Use DLQ (dead-letter queue) concept for failed processing

---

## Week 6 â€” Monitoring, Logging, and Deployment Automation

## 1) CloudWatch Deepen

### Learn
- Metrics dashboards
- Log groups
- Alarms
- Custom metrics

### Practical outcomes
- Create dashboard for EC2/Lambda
- Configure alarms (CPU, error rate, latency)

---

## 2) CloudTrail + Audit posture

### Learn
- Account-wide logging
- Security auditing use cases
- Investigating suspicious actions

---

## 3) CI/CD Intro on AWS

### Services
- CodeCommit (optional)
- CodeBuild
- CodeDeploy
- CodePipeline

### Practical outcomes
- Build basic pipeline for app deployment

Alternative path:
Use GitHub Actions + AWS deployment target.

---

## 4) Secrets and Configuration

### Learn
- AWS Secrets Manager
- SSM Parameter Store
- Avoid credentials in code

---

## Week 6 Labs

1. Build CloudWatch dashboard and alarms
2. Store DB password in Secrets Manager
3. Create simple deployment pipeline
4. Validate rollback behavior in failed deploy

---

## End of Phase 2 Outcomes

By end of Week 6, you should be able to:
- Deploy EC2-based and serverless workloads
- Design VPC with public/private segmentation
- Build scalable architecture with ALB + ASG
- Expose APIs securely via API Gateway
- Use SQS/SNS for decoupled systems
- Monitor and alert using CloudWatch
- Apply basic CI/CD and secrets management

---

## Reference Architecture You Should Build

A two-tier production-like setup:
- Route 53 -> ALB
- ALB -> Auto Scaling EC2 app tier
- App tier -> RDS/Cache (Phase 3 expansion)
- Static media -> S3 + CloudFront
- Logs/metrics -> CloudWatch

---

## Quick Self-Assessment

1. Difference between security group and NACL?
2. Why private subnet for backend resources?
3. When to use Lambda over EC2?
4. Why queue-based architecture improves reliability?
5. How to avoid hardcoded AWS keys in app code?

---

## Common Mistakes to Avoid

- Deploying DB in public subnet
- Single AZ architecture for production
- No health checks on ALB targets
- No alarms for critical metrics
- No retry strategy in async systems
- Over-permissioned IAM roles

---

## Recommended Practice Time

- Week 3: 12â€“15 hours
- Week 4: 12â€“15 hours
- Week 5: 10â€“12 hours
- Week 6: 10â€“12 hours

Total suggested for Phase 2: 44â€“54 hours

---

## Certification Alignment

This phase maps heavily to:
- AWS Solutions Architect Associate
- AWS Developer Associate
- AWS SysOps Administrator Associate

---

## Final Note for Phase 2

Focus on building and rebuilding architecture manually at least twice. Repetition here creates real cloud confidence.
