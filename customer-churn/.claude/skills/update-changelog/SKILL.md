---
name: update-changelog
description: Writes or updates the changelog entry for a change in the customer-churn sub-service. Use when the user asks to update the changelog or document a change about to be committed.
---

# Update the changelog (customer-churn)

## Inputs

- **Description of what was done** — mandatory. Ask for it if missing; never infer it from commit messages alone.
- **Commit ID of the previous stable version** — optional, only for extra context:
  `git log --oneline <commit>..HEAD -- customer-churn/`, `git diff <commit> -- customer-churn/`.

## Which file

The monorepo has a **single root `changelog.md`** (`../changelog.md`); this sub-service has no changelog of its own.
Entries go there under the `` `Customer Churn` module: `` bullet. Cross-cutting changes (shared `.docker/`, root
`.envs/`, `.gitlab-ci.yml`) also go to root. If a sub-service changelog is ever created and later frozen with a "no
longer maintained, see root changelog" note, keep writing to root.

## Conventions in use (re-read `../changelog.md` first)

- `# Changelog` + Keep a Changelog / Semantic Versioning statement.
- `## Unreleased` on top, newest first; releases as `## [x.y.z] - YYYY-MM-DD`.
- One bullet per module with nested bullets, one per change, sentence case, no trailing period; planned work as
  `Pending: ...` (remove the `Pending` bullet when the work lands).
- No `Added/Changed/Fixed` subsections today — don't introduce them unless asked.

## Version bump (when releasing `Unreleased`)

- **Major**: model interface break (`FEATURES` change, `/predict` request/response change), renamed SSM contract,
  model package group/endpoint/ECR repository renamed.
- **Minor**: new flow or stack, new pipeline step, new API capability, library bump with retraining.
- **Patch**: fixes, thresholds, retention, docs.

## References to other repositories

Plain text only (e.g. "see `services/public-utilities` changelog"), never a relative Markdown link.

## Verify

Re-read `../changelog.md`: exactly one entry per change under `Customer Churn`, no duplicates, every bullet traceable
to the user's description or the diff actually read.
