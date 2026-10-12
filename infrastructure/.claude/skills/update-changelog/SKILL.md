---
name: update-changelog
description: Writes or updates the changelog entry for a change in the infrastructure sub-service. Use when the user asks to update the changelog or document a change that is about to be committed.
---

# Update the changelog (infrastructure)

## Inputs

- **Description of what was done** — mandatory. If the user didn't give it, ask. Never infer it from commit messages
  alone.
- **Commit ID of the previous stable version** — optional; only for extra context:
  `git log --oneline <commit>..HEAD -- infrastructure/`, `git diff <commit> -- infrastructure/`.

## Which file

The repository has a **single root `changelog.md`** (`../changelog.md`); sub-services have no changelog of their own.
Entries for this sub-service go there, under the `` `Infrastructure` module: `` bullet. Cross-cutting changes
(shared `.docker/`, root `.envs/`, CI) also go to root, under their own bullet or the affected modules. If a
sub-service changelog is ever created and later frozen with a "no longer maintained, see root changelog" note, keep
writing to root.

## Conventions in use (re-check `../changelog.md` before writing)

- Header: `# Changelog` + Keep a Changelog / Semantic Versioning statement.
- Sections: `## Unreleased` on top (newest first); released versions would follow as `## [x.y.z] - YYYY-MM-DD`.
- Inside a version: one bullet per module (``- `Infrastructure` module:``) with nested bullets, one per change,
  sentence case, no trailing period. Planned work is written as `Pending: ...`.
- No `Added/Changed/Fixed` subsections are used today — don't introduce them unless the user asks.

## Version bump (when releasing `Unreleased`)

- **Major**: a consumer-visible break — renamed/removed SSM parameter, bucket replaced, topic replaced.
- **Minor**: new shared resource, parameter or stack.
- **Patch**: retention tweaks, policy fixes, docs.

## References to external repositories

Mention them as plain text (e.g. the name of an external library), never as a relative Markdown link —
it would cross a git repository boundary.

## Verify

Re-read `../changelog.md`: exactly one entry per change under the right module, no duplicates, and every bullet traces
back to the user's description or something actually read in the diff.
