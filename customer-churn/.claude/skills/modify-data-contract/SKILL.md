---
name: modify-data-contract
description: Safe procedure to add, remove, rename or reorder a feature/column in customer-churn (Glue curation, curated table, src/features/schema.py, model, endpoint/batch/DataDrift consumers). Use before touching columns, FEATURES order, categories normalization or the target.
---

# Modify the data contract

`src/features/schema.py` (`FEATURES` order) is consumed by the model, the endpoint CSV, Batch Transform filters, the
drift profile (`src/monitoring/drift.py` via the `Baseline` step) and `Predict` (`.claude/rules/deployment.md` → Blast radius). A change ships as a **new model
version plus coordinated redeploys**.

1. **Raw → curated** (if the column comes from the source): update `RAW_TO_CURATED` and casts in
   `src/jobs/glue/curate_customers.py` **and** `src/features/curation.py` (same rules), plus `CuratedTable` columns in
   `serverless/data/glue.yml` and, if needed, the DQDL ruleset.
2. **Contract**: edit `NUMERIC_FEATURES` / `CATEGORICAL_FEATURES` in `src/features/schema.py`. Append new features at
   the end when possible.
3. **Validation**: adjust `validate()` in `src/pipelines/training/preprocess.py` if the column needs checks.
4. **Tests**: extend `tests/conftest.py` `make_raw()` and the affected tests; `npm test`.
5. **Image**: the change alters the image hash → `npm run image:push` before `deploy-pipeline`.
6. **Order to hand over** (`README.md` → Deployment): `deploy-data` → `image:push` →
   `deploy-pipeline` → ingest/curate (`npm run ingest`) → execution → approve → `deploy-endpoint` → batch picks it up. The old endpoint keeps working
   until redeployed (its package pins the old image and baseline).
7. **Watch**: `BatchScoring` UNLOAD columns come from `FEATURES` automatically; `Predict` validates required
   features — announce the API change to any consumer (none confirmed yet).
8. **Changelog**: `update-changelog` skill — this is a breaking change of the model interface.
