# Evaluation result package requirements

These requirements define optional reusable support for preserving and
presenting completed evaluations. The generic evaluation kernel, environment
integrations, and consuming suites have separate requirements.

| ID | Requirement | Implementation | Verification | Documentation | Primary evidence |
|---|---|---|---|---|---|
| ERPKG-001 | Completed evaluations can be preserved as compact, self-contained result packages useful to both human reviewers and machine consumers. | Implemented | Automated collect/render/check round trip on synthetic data; both task-guidance packages collected and checked | Documented | `agent_eval.result_packages`; `test_result_packages.py`; `suites/task_guidance/test_result_package.py`; task 095 |
| ERPKG-002 | Human-readable views can be regenerated deterministically from committed result data without rerunning models. | Implemented | Automated byte-for-byte regeneration (framework and suite tests; committed packages) | Documented | `render`/`check` commands; manifest generated-view registry; task 095 |
| ERPKG-003 | Result packages can represent different suites' inputs, stages, outputs, and assessments without imposing domain-specific concepts on those suites. | Implemented | Automated; generic schema exercised with synthetic suite-specific stage shapes | Documented | Opaque named records, suite-owned view builders; framework tests; task 095 |
| ERPKG-004 | Result packages preserve enough provenance to understand how included results were produced and clearly identify unavailable or reconstructed information. | Implemented | Automated; captured/reconstructed/inherited/unavailable states exercised | Documented | Availability states in `agent_eval.result_packages`; manifest source hashes; task 095 |
| ERPKG-005 | Result packages remain safe and proportionate by excluding secrets and unnecessary diagnostic volume while retaining information needed to understand significant execution or evaluation problems. | Implemented | Automated redaction tests; secret scan over committed packages and exports found no credential values | Documented | Sensitive-key redaction, lean session projection, path normalization; task 095 |
| ERPKG-006 | Reviewers can compare available usage and estimated cost across evaluation runs, while incomplete usage or pricing remains visibly incomplete. | Implemented | Automated; pinned-table estimates match provider-reported costs exactly; unknown usage stays visible | Documented | One row per run in `costs.md`/`costs.csv`; pinned price table per package; task 095 |

Implementation, verification, and shared delivery references were recorded as
task 095 completed.
