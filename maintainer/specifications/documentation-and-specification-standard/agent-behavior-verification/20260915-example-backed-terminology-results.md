# September 15 example-backed terminology results

This report compares the final concise terminology rewrite with the approved
Option A structure: input/destination definitions, four general rules with
marked portable examples, and a separate destination-application section.

## Exact inputs

- Pre–Option A guidance SHA-256:
  `0d68a1ac858c7ba1e8da9338bcb455c88abe14e000680732b7f68c2811ae58a0`
- Option A guidance SHA-256:
  `3a4c51039aa48823665334c73129e3ecb01aa299539639c57566b661ab549c4c`
- GLM model: `glm-5.3-flash:cloud`
- GPT model: GPT profile through OpenAI Responses
- Main comparison effort: high
- Sentinels: low and max
- Preserved scenarios:
  [Test 13](13-partial-major-change.md),
  [Test 30](30-source-terms-in-specification-records.md), and
  [Test 31](31-source-terms-in-code-and-tests.md)
- Established-term controls:
  [Test 04](04-package-owned-refinement.md) and
  [Test 14](14-portable-contract-owner.md)

Prompts, fixtures, model profiles, mutation boundaries, and behavioral
assertions were unchanged between the recorded pre–Option A and Option A model
runs. One Test 30 path assertion was calibrated before the Option A rewrite:
`offline-delivery` is valid domain terminology, so a package specification no
longer has to contain the literal substring `sync`.

## Guidance structure

Option A:

- defines input material and maintained destination before using either term;
- pairs each of four general rules with one marked portable example;
- uses example vocabulary different from held-out behavioral prompts;
- states that examples illustrate individual transfers rather than enumerate
  destinations or terms;
- separates six destination-specific instructions from the examples;
- includes one different compact example in root `AGENTS.md`.

The project-independent guide is 2,200 words, 145 words or 7.06% above the
2,055-word integrated baseline. The root documentation policy is 294 words.
The Crystal Lattice addendum is unchanged.

Thirty-five deterministic tests pass, including checks for definition order,
four marked guide examples, one root example, separation from destination
instructions, and lexical separation from held-out terms.

## High-effort comparison

| Scenario | Pre–Option A GLM | Pre–Option A GPT | Option A GLM | Option A GPT |
|---|---:|---:|---:|---:|
| Test 04 package-owned control | Pass | Mechanical status failure; established term preserved | Pass | Pass |
| Test 13 current user documentation | Fail | Pass | Fail | Fail |
| Test 14 portable-term control | Pass | Mechanical status failure; established term preserved | Pass | Mechanical status failure; established term preserved |
| Test 30 task-number wording | Pass | Pass | Fail | Fail |
| Test 30 sequence label | Fail | Fail | Fail | Pass |
| Test 30 evaluative wording | Pass | Pass | Pass | Pass |
| Test 31 task-number wording | Pass | Pass | Fail | Pass |
| Test 31 sequence label | Pass | Pass | Pass | Fail |
| Test 31 evaluative wording | Pass | Pass | Pass | Pass |

The Test 04/14 mechanical failures require a target requirement's documentation
state to remain `Pending`. The GPT outputs used `Documented` while keeping the
portable contract term and target boundary intact. They are not terminology
regressions.

## Low/max sentinels

| Profile and effort | Test 13 | Test 30 sequence label |
|---|---:|---:|
| Pre–Option A GLM low | Fail | Pass |
| Pre–Option A GLM max | Fail | Pass after path-assertion calibration |
| Pre–Option A GPT low | Fail | Fail |
| Pre–Option A GPT max | Fail | Pass |
| Option A GLM low | Fail | Fail |
| Option A GLM max | Fail | Pass |
| Option A GPT low | Fail | Fail |
| Option A GPT max | Pass | Pass |

No hosted provider failure invalidated an Option A result. Some GLM sessions
emitted a recoverable malformed shell-call error and continued to a completed
run; the recorded behavioral failures came from maintained outputs.

## Artifact findings

### General examples

The example structure itself is deterministic and portable. None of the guide
examples uses `Task 010`, `Stage A`, phase labels, `portable`, `useful`, or
`Track A/B`. Root guidance uses a separate example.

### Current user documentation

Option A did not make Test 13 robust. GLM low/high/max and GPT low/high retained
internal grouping or future-target wording. GPT max produced a clean
capability-based README. The difference is model/effort variance, not a stable
rewrite improvement.

### Specification records

Evaluative wording remained clean in both high-effort Option A runs. Sequence
labels improved only for GPT high/max and GLM max. Task-number wording
regressed in both high-effort samples: specifications or decisions referred to
the work by `Task 010` instead of only the descriptive task title and path.

### Source and tests

Source and test identifiers remained behavior-based. The two Option A failures
were requirement-traceability failures:

- GLM task-number used bare `# STATUS-002` comments.
- GPT sequence-label moved `STATUS-002` into test function names without
  explaining the asserted behavior.

The preceding concise rewrite included a concrete explanatory-comment example
inside the source/test application and passed all three Test 31 variants on
both models. Option A removed that application-specific example while
correctly separating generic examples from specific instructions.

## Interpretation

Option A improves the structure and readability of the guidance, defines its
abstract roles before use, and prevents lexical overfitting to the behavioral
prompts. The behavioral matrix does not show a general improvement over the
preceding concise rewrite.

The results suggest two different needs:

1. Generic rules benefit from clearly marked portable examples.
2. A specific instruction that requires a particular reference form may also
   need a small marked example. Separating examples from instructions should
   not mean removing the concrete form that makes an instruction actionable.

Any follow-up should preserve the four generic examples and add only narrowly
justified examples beside the affected task-reference and requirement-comment
instructions, using vocabulary different from held-out scenarios. It should
not add a comprehensive destination example catalog or literal word bans.

## Remaining work

- Human review of the Option A wording and this mixed behavioral result.
- Decide whether application-specific examples are part of the approved
  destination instructions.
- Apply the task-specific rule through
  `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`.
- Run task-guidance parity, documentation preparation, build, and link checks
  after the task-guidance synchronization boundary is implemented.
