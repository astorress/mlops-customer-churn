# Deployment — customer-churn

Procedure (order, approval, removal): `README.md` → Deployment / Model approval / Remove. This file adds technology,
dependencies between stacks, blast radius and gotchas.

## Technology

Serverless Framework v4 (`^4.43.0`). Plugins in `package.json`: `serverless-deployment-bucket`,
`@serverless/safeguards-plugin`, `serverless-s3-sync` (data stack: Glue scripts). JS resolvers:
`serverless/pipeline/pipeline-definition.js` (pipeline JSON) and `container/image-version.js` (image tag + ECR
existence check). Model image: `container/build-push.sh` (`docker buildx build` on a `docker-container` builder, `linux/amd64`,
`--output type=image,push=true,oci-mediatypes=false`, no provenance/SBOM; skipped when the tag exists; fails if ECR
doesn't report a Docker v2 manifest).

## Stack dependencies (SSM unless noted)

```text
infrastructure/common ──► data ──► pipeline ──► (approval) ──► endpoint
                            │         ▲  ▲                 └─► batch
                  image ────┼─────────┘  │ (ECR tag must exist: npm run image:push)
                            └────────────┘ (Glue job name, tables, prefixes)
```

- `pipeline` reads `data` (`/data-science-customer-churn-data/*`) and `image` (`/data-science-customer-churn-image/*`).
- `endpoint`/`batch` read the deployment contract `/data-science-customer-churn-pipeline/Approved*` and
  `SageMakerExecutionRoleArn`; `batch` also reads `data`.

## Blast radius

- **`src/features/schema.py` (`FEATURES` order)** — changes the CSV contract of the endpoint, Batch Transform, the
  drift profile/`DataDrift` Lambda and `Predict`. Use the `modify-data-contract` skill.
- **`container/requirements.txt` (scikit-learn/pandas/numpy)** — a model pickled with other versions may not load in
  the new image; the endpoint keeps working (its package pins its own image tag) but anything retrained or re-served
  must be retrained and re-approved. Use the `modify-model-image` skill.
- **`pipeline-definition.js`** — changing step names breaks `PropertyFile`/`Get` references and the EventBridge/Studio
  history readability; changing `ModelPackageGroupName` orphans the registry and `OnModelApproved`'s filter.
- **`endpoint` names** — `custom.endpoint.name` is referenced by the alarms, the monitoring
  schedule and `PredictRole`; the 5XX alarm name is referenced by the endpoint's `AutoRollbackConfiguration`.
- **Glue curated table schema** — `CuratedTable` columns must match the Glue job output and `preprocess.py`
  validation; Athena reads Parquet by column name.
- **Removing `serverless/image`** — repository is `Retain`ed; deleting it by hand breaks every registered/deployed
  model that references its images.

## First-run gotchas

- `endpoint` can't be deployed while the contract is still `none` (no approved model):
  `serverless/endpoint/approved-model.js` stops the deploy with "No approved model yet" and the approval command
  (`npm run models -- --approve <version>`). Without that guard CloudFormation rejects the stack with a generic "Validation failed with 2 error(s)".
- `pipeline` deploy fails with "Image … is not in ECR" until `npm run image:push` runs (its own step,
  `README.md` → Deployment step 3). `SKIP_IMAGE_CHECK=true` only for offline `serverless print`.
- SageMaker **training/processing accept OCI image manifests but hosting (`CreateModel`) doesn't**: a plain `docker
push` from Docker Desktop's containerd store uploads OCI, so the pipeline succeeds and the endpoint deploy fails with
  `Unsupported manifest media type application/vnd.oci.image.manifest.v1+json`. `build-push.sh` exports Docker v2
  media types and checks it. Model packages pin the image **digest**, so versions trained with an OCI image can never
  be hosted: push a fixed image (new tag), redeploy the pipeline, retrain and approve the new version.
- `image:push` needs Docker reachable from the devcontainer (`/var/run/docker.sock`); on Apple Silicon the `amd64`
  build is emulated and slow.
- The endpoint runs one `ml.t2.medium` in every stage (cost). SageMaker doesn't autoscale burstable instances, so there
  is no autoscaling; a bigger or autoscaled endpoint needs a non-`t2` type that is also listed in
  `pipeline/serverless.yml` → `custom.registry.realtimeInstanceTypes` (versions registered before keep their own list).
- If `data` is deployed after `pipeline`, the first ingestion still starts training (rule lives in `pipeline`);
  without `pipeline`, curation runs and nothing trains until `npm run pipeline:start`.
- Spark on Glue (EMRFS) writes `<folder>_$folder$` marker objects for every ancestor of its output path on commit;
  `GlueRole` (`serverless/data/iam.yml`) lists them explicitly. Changing `custom.prefixes.curated`/`glueTemp` requires
  updating those marker ARNs, otherwise the job fails with `AccessDenied ... _$folder$` at the final write.
- Don't run `npm run pipeline:start` right after `npm run ingest`: the curated partition only exists once the Glue
  job succeeds (crawler + job take several minutes), and that success starts the pipeline by itself. Starting earlier
  makes `PrepareData` fail with `Data download failed ... matched no files` (the Athena query returns 0 rows).
- Approving a model doesn't deploy it: redeploy `endpoint`; `batch` picks it up on its next run.
- The endpoint bills hourly (the `DataDrift` Lambda only costs cents) — remove `endpoint` after dev sessions.
- Blue/green needs the same `VariantName` (`AllTraffic`) across configs.
