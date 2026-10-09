---
name: modify-model-image
description: Safe procedure to change the customer-churn model image — container/Dockerfile, entrypoint, requirements (scikit-learn/pandas/numpy versions) or what gets copied into it. Use before bumping ML libraries, changing the serving server or the train/serve contract.
---

# Modify the model image

Facts: `.claude/rules/dependencies.md` → Model image runtime.

1. **Edit** `container/requirements.txt` / `container/Dockerfile` / `container/entrypoint.sh`. If you add a package
   folder to the image, update the Dockerfile `COPY`s, `.dockerignore` and `IMAGE_PACKAGES` in
   `container/image-version.js` together.
2. **Rebuild the devcontainer** (it installs the same requirements) and run `npm test`.
3. **Contract check locally**: `npm run image:build-local`, then emulate SageMaker (processing with
   `--entrypoint python3 … -m src.pipelines.training.preprocess`, `train` with `/opt/ml` mounted, `serve` + `curl
/ping` and `/invocations`) — commands in the `run-tests` skill → Image contract.
4. **Library bumps invalidate pickles**: models registered with the old image keep their old tag (still loadable);
   anything retrained uses the new one. Never point an old model package at a new image. Plan: push → retrain →
   approve → redeploy endpoint.
5. **Hand over**: `npm run image:push`, then `npm run deploy-pipeline:<stage>` (points the pipeline to the new tag), then
   the retrain / approve / `deploy-endpoint` sequence (`README.md` → Updates).
6. **Changelog**: `update-changelog` skill (mention the new library versions).
