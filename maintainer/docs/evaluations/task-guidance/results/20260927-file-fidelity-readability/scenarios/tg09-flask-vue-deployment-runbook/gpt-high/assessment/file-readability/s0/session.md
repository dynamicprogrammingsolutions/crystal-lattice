# Session — tg09-flask-vue-deployment-runbook · file-readability-assessment-gpt-high-s0 · glm max

- Run: `20260928T215203.424134Z-task-guidance-file-readability-tg09-flask-vue-deployment-runbook-gpt-high-s0-a6ce7fff`
- Model: glm-5.3-flash:cloud (effort max)
- Delivered instructions: [glm-assessor](../../../../../../shared/system-messages/glm-assessor-3d0be6dc03e9.md) — captured (original SHA-256 `f30728bc36ccc479…`)
- Config: [glm-assessor-max](../../../../../../shared/configs/glm-assessor-max.json)
- Activity: 3 messages · 0 tool calls · 0 tool results
- Usage: unknown — saved session contains no provider usage metadata

## Transcript

**User**

Assess how easily a human reader can work with the task files below.
You are that reader: a maintainer who must find, understand, and act on
what the files say. Judge every top-level section that is present; do
not invent sections that are absent, and do not grade files or sections
that do not appear.

Grade each present top-level section `readable`, `partial`, or
`unreadable`: can a reader take in that section's content with
reasonable effort — scan it, hold it, and use it? A section is
`unreadable` when a reader must re-read dense prose or wall-like list
items to extract what matters; `partial` when parts strain the reader.

Then grade the whole file's navigation `navigable`, `partial`, or
`confusing`: can a reader find the thing they are looking for — the
outcome, the constraint, the open question, the plan status — from the
file's structure alone?

Measured structure facts are provided per section; anchor on these
numbers rather than impressions. They are facts, not rules: no shape is
banned or required. Formatting elements — tables, ordered lists, code
snippets, short paragraphs — are tools among many; what is graded is
the reader's experience, never the presence of a specific element.

Every grade carries findings: concrete `{where, quote, why}` items. A
non-top grade with empty findings is invalid. Then hunt for
presentation mistakes explicitly — prose walls, list items that mix
several facts, buried load-bearing facts, headings that do not match
their content, walls of unchecked boxes — and list each as
`{where, quote, why}` in `mistakes`.

Depth must match impact: a short section is not a defect; a dense
section is not automatically one either. Verbosity is not rewarded;
brevity that loses nothing is not penalized.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "tg09-flask-vue-deployment-runbook",
  "assessment": {
    "sections": {
      "SECTION TITLE": {
        "grade": "readable|partial|unreadable",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      }
    },
    "navigation": {"grade": "navigable|partial|confusing", "findings": []},
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

`sections` contains exactly the top-level sections listed in the
measured facts, keyed by the exact Section values of that table
(`<file path> — <section title>`), so multi-file task sets stay
addressable.

What these files are for:

# Write the deployment procedure

Write the repeatable build, run, health-verify, and rollback deployment procedure for the books app, accepted by executing it end to end.

Category: kind
Task kind: operations

Measured structure facts (per file, per top-level section):

#### tasks/20260926-deployment-runbook.md

| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tasks/20260926-deployment-runbook.md — Requirements checklist | 272 | 0 | 0 | 7 | 11 | 0 | 0 | 0 | 1 |
| tasks/20260926-deployment-runbook.md — Research and supporting facts | 134 | 0 | 0 | 6 | 14 | 0 | 0 | 0 | 11 |
| tasks/20260926-deployment-runbook.md — Unresolved requirement questions | 114 | 0 | 0 | 4 | 13 | 0 | 0 | 0 | 2 |
| tasks/20260926-deployment-runbook.md — Execution plan | 618 | 2 | 82 | 20 | 13 | 5 | 0 | 0 | 1 |

The produced task files:

### tasks/20260926-deployment-runbook.md

````markdown
# Books demo deployment runbook

Create a repeatable deployment runbook for the Flask/Vue Books demo. The
runbook is for an operator starting from a clean checkout and must cover the
full deployment lifecycle, including verification and recovery. This task is
documentation-only: do not change product code, application routes, client
code, or deployment behavior while completing it.

## Requirements checklist

- [ ] The maintained documentation describes the prerequisites and exact
  commands for building the application from a clean checkout, including
  dependency installation, the build output or served artifact, and the
  expected working-directory assumptions.
- [ ] The maintained documentation explains how to start the deployed
  application with configuration supplied through environment variables. It
  names each required variable, its source/default where applicable, how the
  Flask API and Vue client receive their configuration, and which values must
  not be committed or printed.
- [ ] The maintained documentation defines deployment verification through an
  approved health endpoint: URL, request, expected response/status, timeout or
  retry behavior, and explicit pass/fail criteria are included.
- [ ] The maintained documentation defines rollback when verification fails,
  including how the previous deployment is identified and retained, how the
  active revision/artifact is switched back, how the service is restarted or
  traffic is restored, and how the rollback itself is verified with the
  health check.
- [ ] The procedure is repeatable from a clean checkout and includes an
  end-to-end acceptance record showing one successful execution of build,
  configuration, start, health verification, induced or observed failure
  handling as applicable, and rollback to the previous deployment. The record
  identifies the checkout/revision, commands, environment-variable
  conventions, and observed results without exposing secrets.
- [ ] The runbook states any prerequisite outside the repository, deployment
  target assumptions, data-persistence implications, and operator stop
  conditions needed to execute it safely. Unsupported behavior is marked
  `Not implemented` or called out as a blocker rather than invented.
- [ ] No product code, application configuration source, client source, or
  deployment runtime behavior is changed as part of this task.

## Research and supporting facts

- The repository root has a short `README.md` but no deployment guide or
  deployment manifest.
- The Flask application is `server.app:app`; `pyproject.toml` declares Flask
  as its only Python dependency.
- The API currently exposes `GET /books` and book mutation routes. There is no
  dedicated health route in `server/app.py`.
- `client/package.json` declares only a Vitest test script; it does not declare
  a production build script or a bundler, and the client HTTP base URL is
  currently hard-coded to `http://localhost:5000` in `client/src/http.js`.
- The current test suite verifies basic API responses and Vue rendering, but
  it does not verify a built artifact, a deployed process, environment
  configuration, health probing, or rollback.
- The repository ignores dependency/cache outputs such as `node_modules/`,
  `.pytest_cache/`, and `__pycache__/`; a clean-checkout acceptance should
  install dependencies explicitly and avoid relying on ignored state.

## Unresolved requirement questions

- Which deployment target and process manager are in scope for the runbook?
  The repository does not identify a hosting provider, container runtime,
  reverse proxy, or release directory convention.
- Which endpoint is approved as the deployment health endpoint? A dedicated
  `/health` endpoint is not present, and selecting `/books` as a health probe
  would be a contract decision that should be explicit.
- Where does the “previous deployment” live, and what rollback mechanism is
  available on the target (immutable release directories, image tags, package
  versions, or another mechanism)?
- Is the intended acceptance allowed to use a local deployment harness that
  represents the target process, or must it run against a particular hosted
  environment?

## Execution plan

Status: Draft

The runbook should be owned by the deployment/operator-facing documentation
area. It should present one linear procedure with explicit inputs and
decision points: prepare an exact revision, install dependencies, build the
deployable artifact, export environment configuration, start or promote the
release, probe the approved health endpoint, and either declare success or
restore the previous release. The procedure must distinguish facts supported
by this checkout from target-specific prerequisites and must not imply that
the missing client build or health route already exists.

The acceptance evidence should cross the real deployment boundary selected for
the task. A unit test or mocked HTTP request is not sufficient. The operator
should execute the documented commands once from a fresh checkout, capture
the revision and non-secret configuration inputs, confirm the health response
against the running deployment, and demonstrate the rollback path or record
the exact blocker if the selected target cannot safely exercise it. The final
documentation should preserve the command transcript/result summary as
evidence without storing credentials.

### Implementation decisions and open questions

- Keep this change documentation-only; no missing build script, environment
  adapter, health route, or deployment automation may be added under this
  task.
- Resolve the deployment target, health probe, and previous-release mechanism
  before writing target-specific commands. If they remain unspecified, write
  the supported local procedure and visibly mark target-dependent sections
  `Not implemented` rather than selecting an unapproved contract.
- Treat the absence of a declared Vue production build and dedicated health
  endpoint as a release-blocking fact for any procedure that claims to deploy
  those components. Do not substitute a mock or test-only shortcut.

### Documentation

- Update or add the smallest maintained operator-facing documentation page
  that owns deployment guidance; do not create placeholder documentation
  structures.
- Include prerequisites, clean-checkout build steps, environment-variable
  table, start/promote steps, health verification, rollback, failure
  handling, and the dated end-to-end acceptance record.
- Link the runbook from the nearest maintained documentation index if one
  exists and the link is appropriate for its audience.

### Task checklist

- [ ] Confirm the deployment target, process manager, approved health endpoint,
  and previous-release/rollback mechanism.
- [ ] Inspect the selected target's supported build and runtime commands
  without changing product code.
- [ ] Draft the operator runbook with explicit variables, artifacts,
  verification criteria, rollback steps, and stop conditions.
- [ ] Execute the documented procedure once from a clean checkout and record
  the revision, non-secret inputs, commands, and results.
- [ ] Review the runbook against the actual execution and correct unsupported
  or ambiguous instructions.
- [ ] Run documentation/link checks applicable to the selected documentation
  location and confirm no product files changed.

### Requirement verification

- The build requirement is verified by following the documented build commands
  from a fresh checkout and confirming the stated artifact or serving
  behavior; inspection alone is insufficient.
- The environment-configuration requirement is verified by starting the real
  deployment process with the documented environment variables and observing
  that it binds to and calls the configured components without hard-coded
  local-only assumptions.
- The health-verification requirement is verified by sending the documented
  probe to the running deployment and checking the documented status/body and
  failure criteria.
- The rollback requirement is verified by switching from the deployed
  revision to the retained previous revision after a failed verification (or
  an explicitly documented safe failure simulation), then rerunning the
  health probe against the restored deployment.
- The no-product-code-change constraint is verified with version-control
  inspection showing only the intended documentation/task changes.

### Additional implementation verification

- Check that secrets are absent from the runbook and acceptance transcript.
- Check that the instructions work with a clean dependency state rather than
  relying on ignored local caches or pre-existing processes.
- Check that rollback leaves a clearly identified previous release and that
  the runbook explains what happens to persistent book data, if the selected
  target has any.
````


**Assistant** *(reasoning present)*

{
  "schema_version": 1,
  "scenario_id": "tg09-flask-vue-deployment-runbook",
  "assessment": {
    "sections": {
      "tasks/20260926-deployment-runbook.md — Requirements checklist": {
        "grade": "partial",
        "findings": [
          {
            "where": "Requirements checklist, box 2",
            "quote": "It names each required variable, its source/default where applicable, how the Flask API and Vue client receive their configuration, and which values must not be committed or printed.",
            "why": "One unchecked box fuses four distinct requirements (variable list, sourcing, per-component wiring, secret handling) into a single ~40-word sentence; it cannot be taken in or ticked as one unit, and the specifics sit mid-sentence."
          },
          {
            "where": "Requirements checklist, box 5",
            "quote": "includes an end-to-end acceptance record showing one successful execution of build, configuration, start, health verification, induced or observed failure handling as applicable, and rollback to the previous deployment",
            "why": "The longest box chains six acceptance phases inline, so recovering the phase list means re-reading. Parallel lead-ins ('describes / explains / defines') keep each box's topic identifiable, which is what holds this at partial rather than unreadable."
          }
        ]
      },
      "tasks/20260926-deployment-runbook.md — Research and supporting facts": {
        "grade": "readable",
        "findings": [
          {
            "where": "Research and supporting facts, bullet 4",
            "quote": "it does not declare a production build script or a bundler, and the client HTTP base URL is currently hard-coded to `http://localhost:5000` in `client/src/http.js`.",
            "why": "Representative of the section's shape: one fact per bullet, short items, and code spans pinning each claim to a file — scannable and directly usable at 134 words."
          }
        ]
      },
      "tasks/20260926-deployment-runbook.md — Unresolved requirement questions": {
        "grade": "readable",
        "findings": [
          {
            "where": "Unresolved requirement questions, bullet 4",
            "quote": "Is the intended acceptance allowed to use a local deployment harness that represents the target process, or must it run against a particular hosted environment?",
            "why": "Each of the four items poses exactly one decision question with its rationale attached; nothing needs unpacking across the 114-word section."
          }
        ]
      },
      "tasks/20260926-deployment-runbook.md — Execution plan": {
        "grade": "partial",
        "findings": [
          {
            "where": "Execution plan, opening paragraph 1",
            "quote": "It should present one linear procedure with explicit inputs and decision points: prepare an exact revision, install dependencies, build the deployable artifact, export environment configuration, start or promote the release, probe the approved health endpoint, and either declare success or restore the previous release.",
            "why": "The plan's core artifact — the seven-step procedure sequence — is an inline colon enumeration inside an 82-word paragraph, so recovering the order of operations requires re-reading prose."
          },
          {
            "where": "Execution plan → Requirement verification, bullet 2",
            "quote": "The environment-configuration requirement is verified by starting the real deployment process with the documented environment variables and observing that it binds to and calls the configured components without hard-coded local-only assumptions.",
            "why": "A ~32-word single-sentence item stacking method, observation, and a negative constraint; several Requirement-verification items read this way and strain a single pass."
          },
          {
            "where": "Execution plan, subsection structure",
            "quote": "### Implementation decisions and open questions … ### Documentation … ### Task checklist … ### Requirement verification … ### Additional implementation verification",
            "why": "Splitting 20 items into five small labeled groups is what keeps the 618-word section workable; the strain is localized in the two opening paragraphs and the longer items, not section-wide."
          }
        ]
      }
    },
    "navigation": {
      "grade": "navigable",
      "findings": [
        {
          "where": "Execution plan, first line under the heading",
          "quote": "Status: Draft",
          "why": "Plan status is answered directly at the head of the plan section, exactly where a reader looking for it would search."
        },
        {
          "where": "Unresolved requirement questions vs Execution plan → Implementation decisions and open questions / Task checklist",
          "quote": "Which deployment target and process manager are in scope for the runbook? … Resolve the deployment target, health probe, and previous-release mechanism … Confirm the deployment target, process manager, approved health endpoint, and previous-release/rollback mechanism.",
          "why": "The open-question state lives in three places with drifting subsets, so 'what is still undecided' requires cross-checking three locations; section titles otherwise map cleanly onto reader goals."
        }
      ]
    },
    "mistakes": [
      {
        "where": "Requirements checklist, box 2",
        "quote": "It names each required variable, its source/default where applicable, how the Flask API and Vue client receive their configuration, and which values must not be committed or printed.",
        "why": "List item mixing several facts: four separable requirements share one checkbox, so the checklist cannot be scanned or ticked one requirement at a time."
      },
      {
        "where": "Requirements checklist, box 6",
        "quote": "Unsupported behavior is marked `Not implemented` or called out as a blocker rather than invented.",
        "why": "A runbook-wide load-bearing rule is buried at the tail of an unrelated requirements box instead of standing as its own item."
      },
      {
        "where": "Execution plan, opening paragraph 1",
        "quote": "prepare an exact revision, install dependencies, build the deployable artifact, export environment configuration, start or promote the release, probe the approved health endpoint, and either declare success or restore the previous release.",
        "why": "Prose wall: the canonical step order is locked inside a paragraph rather than shown as a list, forcing re-reading to extract the sequence."
      },
      {
        "where": "Execution plan, opening paragraph 2",
        "quote": "A unit test or mocked HTTP request is not sufficient.",
        "why": "The acceptance-sufficiency prohibition is sandwiched mid-paragraph inside a ~75-word block that also packs operator actions and evidence-retention rules; the load-bearing fact is easy to lose on a single pass."
      },
      {
        "where": "Execution plan → '### Implementation decisions and open questions'",
        "quote": "### Implementation decisions and open questions",
        "why": "Heading does not match its content: the three items are a constraint, a decision with fallback, and a framing fact — no open questions appear (they live in a separate top-level section)."
      },
      {
        "where": "Unresolved requirement questions / Execution plan → Implementation decisions and open questions / Execution plan → Task checklist",
        "quote": "Confirm the deployment target, process manager, approved health endpoint, and previous-release/rollback mechanism.",
        "why": "The same cluster of unknowns is restated in three places with drifting subsets (the harness question appears only in one, process manager drops out of the Implementation-decisions version), so the reader must reconcile three lists to know the true open-question state."
      }
    ],
    "summary": "A short, well-partitioned task file. Research facts (six single-fact bullets pinned by code spans) and open questions (four one-decision items) take in cleanly, and section titles map directly onto what a reader looks for, with 'Status: Draft' visible at the plan's head — navigation holds. Strain concentrates in two places: the 7-box requirements checklist, whose boxes average ~39 words and fuse multiple requirements per box, and the Execution plan's two opening paragraphs (75–82 words) that bury the seven-step sequence and the acceptance-sufficiency rule in prose. A heading promising open questions it does not contain, plus the same four unknowns restated in three places with drifting subsets, add cross-checking work. The defects are localized — unpack the boxes, lift the procedure sentence into a list, and reconcile the duplicated unknowns — not structural."
  }
}
