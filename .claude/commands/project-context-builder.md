---
name: project-context-builder-monorepo
description: >
  Generates a complete Claude Code context system (CLAUDE.md + .claude/rules/ + .claude/agents/ + .claude/skills/)
  for any repository — standalone or sub-service inside a monorepo. Analyzes project structure, reads config and
  source files, extracts architecture from draw.io HTML diagrams, interviews the user, and produces project-specific
  (never generic) documentation. ALWAYS trigger when the user says: "generate context for Claude Code",
  "create CLAUDE.md", "build claude context", "set up .claude/", "onboard Claude to my repo",
  "document this service for Claude Code", "create rules for Claude Code", or wants agent/skill files for
  a service. Mandatory for monorepos with multiple sub-services — never attempt ad-hoc context generation.
---

# Project Context Builder — Monorepo & Standalone

Generates a production-grade Claude Code context system by combining automated file analysis with a
targeted user interview. Output is always project-specific: real resource names, real file paths, real
commands — never generic boilerplate.

---

## Step 1 — Detect repository type

Ask this single question before doing anything else:

> "Is this a standalone repository, or is this a sub-service inside a monorepo?
> If monorepo: what is the name of this sub-service and what does it do within the overall system?"

Wait for the answer. Store:

- `repo_type`: `standalone` | `monorepo`
- If monorepo: sub-service name, stated purpose, path to monorepo root (default: one level up from CWD)

---

## Step 2 — Explore structure

**Standalone:** recursively list all files from CWD, excluding `node_modules`, `.git`, `dist`, `build`, `coverage`.

**Monorepo:** run two listings in parallel:

1. Current sub-service directory — full recursive listing
2. Monorepo root (one level up) — top-level only, no recursion

From the root listing identify: other sub-services, shared config files, CI/CD files, `docs/` folder.

---

## Step 3 — Read key files

**Always read from the sub-service directory:**

- `README.md` if present — note every operational procedure it already documents (setup, deployment
  steps, migration/rollback commands, troubleshooting scripts). These become citation targets in
  Steps 5–8, see "Single source of truth" below.
- All config files: `package.json`, `serverless.yml`, `pyproject.toml`, `Dockerfile`, etc.
- Up to 5 representative files from `test/`, `tests/`, or `integration/` — identify what is tested,
  what is mocked, and which external dependencies appear
- At least one source file per top-level folder under `src/` or equivalent — understand the domain model

**If monorepo, additionally read from root:**

- `README.md` — overall architecture and service relationships
- `changelog.md` if present
- `.gitlab-ci.yml` or any CI/CD file — pipeline stages, which sub-services deploy together
- `docs/` folder — list all files. For any `.html` file: read and extract text to identify system
  components, data flows, integration points, and sub-service relationships. These are likely draw.io
  architecture diagrams exported as HTML — treat them as the authoritative architecture source.
- `.docker/` or `.devcontainer.json` at root — shared development environment constraints

---

## Step 4 — User interview

Ask all of the following in a **single message**:

1. What is the responsibility of this sub-service within the overall system?
   *(Skip if standalone and README is self-explanatory)*
2. What other sub-services or external systems does this one **consume or call**?
3. What other sub-services or external systems **consume or call** this one?
4. What environments exist (dev, test, prod) and what are the key differences for this sub-service?
5. Are there deployment order dependencies — does this sub-service require another sub-service or
   infrastructure stack to exist first?
6. Any non-obvious constraints, past incidents, or gotchas a new developer should know?
7. Is there a first-run procedure or anything that must be done manually before automated setup works?

---

## Single source of truth policy (governs Steps 5–8)

This context system is generated across four layers (`CLAUDE.md`, `.claude/rules/`, `.claude/agents/`,
`.claude/skills/`), plus whatever `README.md` already exists. Left unchecked, the same fact (a secret
path, an instance size, a deploy command) gets restated in three or four of these files, and the first
time the project changes, only some of the copies get updated — the rest silently go stale. Assign every
fact to exactly one owning file and have everything else reference it instead of restating it.

- **`.claude/rules/*.md` owns structural/architectural facts** (resource names, paths, per-environment
  specs, credential/secret locations, integration details). `CLAUDE.md`, `.claude/agents/*.md`, and
  `.claude/skills/*.md` must not reproduce a fact that a rules file already owns — reference the file
  and section instead (e.g. "see `environments.md` for the per-stage instance sizes"), don't copy the
  table.
- **`README.md` owns operational procedures, if it already documents them** (setup steps, deployment
  order, migration/rollback commands, troubleshooting scripts, first-run gotchas with exact commands).
  If `README.md` already has a step-by-step procedure, every generated file must **cite** it (e.g. "see
  README.md → Deployment") instead of reproducing the steps. This citation is **one-directional**:
  generated files may point to `README.md`, but never edit `README.md` to point back at `.claude/` or
  `CLAUDE.md` — it must stay usable on its own by a human with no Claude Code context.
  - Only restate part of a README procedure when the generated file is adding something the README
    doesn't have — e.g. a debugging skill mapping a specific error string to root cause, or an agent
    noting a Claude-specific gotcha. Restate the minimum needed for that added value, and still link
    back to the README for the full procedure.
  - If `README.md` does **not** document an operational procedure yet, generate it as owned by the
    relevant `.claude/rules/` or `.claude/skills/` file as usual — the citation rule only applies to
    procedures that already have a home in the README.
- **`CLAUDE.md` is a thin index, not a restatement.** Give just enough inline content for fast
  orientation (folder structure, which env vars exist, the deploy command to run), and point to the
  owning rules file or README section for everything else. If a section in `CLAUDE.md` would just be a
  copy of a table that also lives in `.claude/rules/`, cut the table down to names/pointers only.
- **Before writing `.claude/agents/*.md`, check what `.claude/rules/*.md` already covers** and reference
  those files by name for the facts (e.g. "read `.claude/rules/database.md` before answering migration
  questions") instead of re-deriving a parallel "key facts" table. Agent files should carry judgment and
  gotchas that rules files don't (when to escalate, what order to check things in), not duplicate specs.
- **When re-running this builder on a project that changed structurally** (a stack renamed, a dependency
  removed, a migration completed): the fact that most files needed the same fix in the same run is the
  signal this policy is working — if the same fact only needed fixing in one place, you've already
  avoided the duplication problem this section exists to prevent.

---

## Step 5 — Generate CLAUDE.md

Write `CLAUDE.md` inside the current sub-service directory containing (per the single source of truth
policy above — this file indexes, it does not restate):

- **If monorepo:** open with a "Monorepo context" paragraph — name the overall service, list other
  sub-services at root, and state how this sub-service fits in. Reference root README and `docs/`.
- One-paragraph description of what this sub-service does
- Folder structure as a text diagram (current directory only)
- Local development setup: required tools, how to start dev environment, dependency on shared
  root `.docker/` or `.devcontainer.json`
- Environment variable **names** grouped by file, one line each noting required/optional. If
  `README.md` already documents what each variable means, link to that section instead of repeating
  the description; only write descriptions here for variables the README doesn't cover.
- Deployment: the exact command(s) to run, plus a pointer to `.claude/rules/deployment.md` and/or
  `README.md` for order dependencies and first-run gotchas — do not reproduce the full step list here.
- A short environment-differences summary (2-3 defining traits per stage), pointing to
  `.claude/rules/environments.md` for the full table.
- End with: `See .claude/rules/ for detailed operational context.`

---

## Step 6 — Generate .claude/rules/

Create one focused Markdown file per topic inside `.claude/rules/`. Generate each file listed below
if applicable to this project. Every file must contain project-specific details: real resource names,
real file paths, real command examples.

### `architecture.md`

- **Standalone:** describe service role and data flow.
- **Monorepo:** describe where this sub-service sits in the overall architecture derived from `docs/`.
  Include which other sub-services it connects to, what triggers it, and what it produces.
  Reference the draw.io diagram by filename if one was found.

### `environments.md`

Per-environment differences for this sub-service specifically. Note if some environments share
infrastructure from the monorepo root.

### `deployment.md`

Deployment technology, key files, required order relative to other sub-services or infrastructure
stacks, known risks, and first-run gotchas from Step 4.

### `integrations.md`

Every external service, sub-service, or cloud resource this sub-service calls or is called by.
For each integration include: protocol, direction (inbound/outbound), auth method, and what breaks
if the integration is unavailable. Derived from source code analysis + Step 4 answers.

### `database.md` *(only if sub-service owns a database or migrations)*

Engine, per-env configuration, migration approach, safety constraints.

### `testing.md` *(only if `test/` or `tests/` directory exists)*

What is covered, what is mocked vs real, how to run tests locally, environment variables or
infrastructure required for integration tests.

### `dependencies.md` *(only if non-obvious external dependencies exist)*

Internal shared libraries, required infrastructure stacks that must exist first, SSM parameters
published by other sub-services, shared secrets.

---

## Step 7 — Generate .claude/agents/

Each agent file must include YAML frontmatter with `name` and `description` fields.

**Always create:**

**`<service-name>-expert.md`** — domain expert agent named after the sub-service. Per the single source
of truth policy above: reference `.claude/rules/*.md` by filename for resources, files, and
per-environment specs rather than restating them in a parallel table — the agent's value is judgment
(what order to check things in, when to escalate, gotchas from Step 4) on top of those files, not a
second copy of their content. State clearly which rules file to consult for which kind of question.

**Create if applicable:**

**`deploy-validator.md`** — if deployment has environment-specific pre-conditions or depends on
other sub-services being deployed first.

**`test-advisor.md`** — if the test suite has non-obvious patterns, requires real infrastructure,
or integration tests have known flaky behavior.

**If monorepo:** every agent must explicitly know which other sub-services exist, what they produce,
and how this sub-service depends on them — to prevent suggesting changes that break inter-service
contracts.

---

## Step 8 — Generate .claude/skills/

Create one skill per recurring developer task. Each skill is a folder with a `SKILL.md` inside. Skills
are allowed to restate exact commands (that's what makes them directly actionable), but per the single
source of truth policy above: if a skill's procedure is already fully documented in `README.md`, cite
that section instead of copying the whole thing — only inline the extra, skill-specific value (e.g. a
debug skill's error-to-cause mapping, or a modify skill's blast-radius warnings).

**Always create if applicable:**

**`understand-service/SKILL.md`** — explains this sub-service to someone new, including its place
in the monorepo. Maps components, integrations, and explicit scope boundaries (what this
sub-service does NOT own).

**`debug-<main-failure-mode>/SKILL.md`** — maps known error patterns to source files and probable
causes, derived from code analysis and Step 4 answers.

**`modify-<main-resource>/SKILL.md`** — safe step-by-step procedure for modifying the most critical
or risky resource in this sub-service.

**Always create:**

**`update-changelog/SKILL.md`** — procedure for writing/updating a `changelog.md` entry for this
sub-service (and the root monorepo changelog, if one exists). Requirements:

- Inputs: a description of what was done (**mandatory** — the skill must ask for it if missing
  and must not fabricate it from commit messages alone) and the commit ID of the previous stable
  version (**optional** — used only to pull extra context via `git log`/`git diff`/`git show`
  against that commit, never as a substitute for the description).
- Discover the actual conventions already in use in this repo's `changelog.md` file(s) before
  writing anything: title format, version header format, date format, category headers used
  (`Added`/`Changed`/`Fixed`/etc.), and whether entries are newest-first. If no changelog exists
  yet, default to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) +
  [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
- If this is a monorepo with a root changelog and per-sub-service changelogs: document the rule
  for which file receives new entries — a sub-service's changelog is frozen (new entries go to
  root instead) once it carries a "no longer maintained, see root changelog" note; otherwise new
  entries stay in the sub-service's own changelog. Cross-cutting, monorepo-wide changes always go
  to root.
- Guidance for picking a version bump (major/minor/patch) based on the actual impact of the change,
  and for referencing another repository's changelog as plain text (never a relative Markdown link,
  since it would cross a git repository boundary and break).
- A verification step: re-read the edited file, confirm there is exactly one entry for the new
  version with no duplicates, and confirm every bullet traces back to the user's description or
  something actually read in the diff/commits.

**`code-review/SKILL.md`** — rigorous checklist-driven review of the container setup, package
dependencies, and devcontainer configuration. This skill must be thorough, not a surface scan.
Requirements:

- **Read every relevant file completely** before drawing conclusions. Many bugs only appear when
  comparing two files against each other — never diagnose from a single file.
- **Trace every path end-to-end.** For each tool path in `devcontainer.json`: find the exact
  Dockerfile line that installs it, confirm the install method places the binary at that exact path,
  and confirm no other install creates a conflicting binary that shadows it.
- **Tag every finding by severity:** BUG (broken at runtime), SILENT FAILURE (works but produces
  wrong results with no visible error), CONFLICT (two installs of the same thing coexist),
  WASTE (unnecessary layer or package), RISK (correct today but fragile).
- **Check parity in both directions.** When two files must agree (e.g. `package.json` ↔
  `serverless.yml` plugins): verify A→B and B→A independently. A one-way check always misses half
  the bugs.
- **Never skip an item because it looks unchanged.** Bugs introduced by one change often only
  manifest in a file that was not part of that change.
- **Report findings even with no immediate impact.** A [WASTE] item is worth documenting — it adds
  build time, confuses future developers, or masks real issues during debugging.
- **If a finding cannot be fully verified from static analysis, say so explicitly** rather than
  assuming it is fine.
- **End with a severity summary table and an explicit statement** of whether all checklist items
  were verified or which ones required a running container to confirm.

Checklist must cover at minimum:

- Dockerfile: no duplicate runtime installation (e.g. language interpreter via multi-stage COPY
  AND via apt); all tools referenced in `devcontainer.json` settings are installed; no standalone
  `apt-get update` layers; all CLI tools called by scripts (`jq`, `git`, `aws`, etc.) are present;
  architecture-aware install blocks handle all supported arches.
- devcontainer.json: every `*Path` setting resolved against the exact binary path the Dockerfile
  install method produces (pip → `/usr/local/bin/`, apt → `/usr/bin/`); every extension has a
  corresponding setting or tool; every setting has a corresponding extension.
- package.json: every `devDependency` used in at least one stack config; every plugin in any
  `serverless.yml` declared in `devDependencies`; deploy scripts reference paths that exist on disk.
- entrypoint.sh: working directory is correct before each operation; `STEP_COUNT` matches actual
  steps; each customlib clone block calls `dist.sh`; credential tools available before first use.
- docker-compose.yml: all required `env_file` entries present; secret names match Dockerfile
  symlink targets exactly; named volumes match Dockerfile mount points.
- Cross-file: Python interpreter uniqueness (grep for any apt python3 install); SLS plugin parity
  both directions across all stacks; migration toolchain completeness, if the project owns
  database migrations (every tool present in the correct image stage); secret name consistency Dockerfile ↔ compose.

**Create if applicable:**

**`validate-environment/SKILL.md`** — if deployment requires checking pre-conditions in this
sub-service or in dependencies.

**`run-tests/SKILL.md`** — if running tests requires non-obvious steps, environment variables, or
infrastructure that must be started first.

**If monorepo:** every skill must include a note on which other sub-services or root-level stacks
must be running or deployed for the steps to work.

---

## Step 9 — Verify and report

After writing all files, produce a final report containing:

1. **Files created** — every file with a one-line description
2. **Information sources** — which facts came from `docs/` diagrams vs source code vs Step 4 answers
3. **Unanswered questions** — any Step 4 question left unanswered and which output files were affected
4. **Coverage gaps** — areas that could not be analyzed (no `docs/` at root, no test directory,
   no env files, etc.)
5. **If monorepo:** confirm which other sub-services were identified at root and whether any appear
   as dependencies in the generated context
6. **Duplication check:** for every fact that appears in more than one generated file (or in
   `README.md`), confirm exactly one file owns it and the rest cite it, per the single source of truth
   policy. List any fact still duplicated across files and fix it before finishing.

---

## Quality constraints (apply throughout)

- **Never write generic advice.** Every sentence must be grounded in the actual project: real names,
  real paths, real commands.
- **Monorepo awareness is mandatory.** If `repo_type` is `monorepo`, every generated file must
  reference the broader service ecosystem where relevant.
- **Architecture diagrams are authoritative.** If draw.io HTML files are found in `docs/`, treat
  their extracted content as the primary source for inter-service relationships — it supersedes
  assumptions from README alone.
- **Step 4 gaps degrade output quality.** If the user skips questions, note the gap explicitly in
  affected files rather than filling with assumptions.
- **File count scales with project complexity.** Do not create files that have nothing to say. Do
  not omit files that are applicable.
