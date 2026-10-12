---
name: understand-service
description: Explains the infrastructure sub-service to someone new — the shared buckets and their zones, the Athena workgroup, the notifications topic, the Studio VPC and Studio, the SSM contract with MLOps projects, and what it does NOT own. Use when onboarding or before a first change in infrastructure.
---

# Understand infrastructure

Answer in the language the person writes in. Point at real files.

1. **What it is**: the shared platform of this repository — pure IaC, no code. Two stacks:
   `serverless/common` (buckets, workgroup, topic, SSM) and `serverless/studio` (team UI), plus the vendored VPC
   library stack Studio runs in (why Studio needs a VPC: architecture.md → Resource roles). Details:
   `.claude/rules/architecture.md` → Stacks.
2. **Why it exists**: every MLOps project needs the same data lake, artifact store, query engine and alert channel.
   Centralizing them keeps one data lake with per-project prefixes and one place to receive notifications.
3. **How projects use it**: they read SSM parameters at deploy time and write under their own prefixes at run time.
   Walk through the table in `.claude/rules/integrations.md` and show one consumer, e.g.
   `../customer-churn/serverless/data/serverless.yml` → `custom.s3`.
4. **Data lake zones**: `raw/` → `curated/` → `predictions/`, and why the bucket emits EventBridge events
   (architecture.md → Resource roles). Show `../customer-churn/serverless/data/events.yml` as the subscriber.
5. **Per stage**: `.claude/rules/environments.md`.
6. **What it does NOT own**: Glue databases/tables/jobs, SageMaker pipelines, models, endpoints, ECR repositories,
   project-specific workgroups, EventBridge rules — all belong to each project (e.g. `customer-churn`). It also never
   deploys anything by itself: deploy steps are in `README.md` → Deployment.
7. **First change checklist**: read `.claude/rules/deployment.md` → Blast radius before editing anything in
   `serverless/common/`.
