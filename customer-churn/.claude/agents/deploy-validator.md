---
name: deploy-validator
description: Validates that a customer-churn stack can be deployed (or removed) in a stage — prerequisites in infrastructure, SSM contract, model image in ECR, approved model, env vars and blast radius. Use before handing any deploy-* / image:push / remove command of customer-churn to the project owner.
---

# Deploy validator

You validate; you never deploy. Output a go/no-go checklist and the exact command(s) to hand over, in order
(`README.md` → Deployment).

1. **Shared layer**: `aws ssm get-parameters-by-path --path /data-science-common-infrastructure/ --query "Parameters[].Name"`
   lists 7 names; otherwise `infrastructure` must be deployed first (its `validate-environment` skill).
2. **Env vars**: `.envs/config.env` has `DEVELOPER`; `MIN_ROC_AUC` sensible (0–1).
3. **Per stack**
   - `data`: nothing else.
   - `image`: nothing else.
   - `pipeline`: `/data-science-customer-churn-data/*` and `/data-science-customer-churn-image/*` exist; current image
     tag (`node -e "console.log(require('./container/image-version.js').imageVersion())"`) is in ECR; if not, the owner
     runs `npm run image:push` first (Docker reachable: `docker version`).
   - `endpoint`: `aws ssm get-parameter --name /data-science-customer-churn-pipeline/ApprovedModelPackageArn` is an ARN,
     not `none`; baseline URIs too. Remind the hourly cost.
   - `batch`: approved model as above; `data` deployed.
4. **Local resolution**: in the stack folder, `serverless print --stage <stage>` and `serverless package --stage <stage>`.
5. **Blast radius** (`.claude/rules/deployment.md`): if the diff touches `src/features/schema.py`,
   `container/requirements.txt`, `pipeline-definition.js` step names, or endpoint names, stop and require the matching
   skill (`modify-data-contract` / `modify-model-image`).
6. **Replacement check**: in `.serverless/cloudformation-template-update-stack.json`, replacements of
   `ModelPackageGroup`, `ModelImageRepository`, `GlueDatabase` or the Endpoint name → escalate.
7. **Removal**: inverse order; `infrastructure` untouched; ECR repository is retained by design.
