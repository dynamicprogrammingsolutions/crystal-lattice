# Shared Parser-Backed Code Comparison

Create a shared parser-backed code-comparison package under `evaluations/src/agent_evaluations/` so RepoQA and future code-oriented evaluations can compare code semantically using real language parsers instead of plain normalized text.

Parent Task: `tasks/20260508-agentic-evaluations-codex/000-main.md`

Depends On:

- `tasks/20260508-agentic-evaluations-codex/018-benchmark-owned-layout-and-run-profiles.md`

## Requirements checklist

- [x] Add a shared comparison package under `evaluations/src/agent_evaluations/` rather than keeping language comparison logic inside RepoQA code.
- [x] Keep Python semantic comparison based on the stdlib `ast` parser.
- [x] Add explicit parser-package dependencies for:
  - `tree-sitter`
  - `tree-sitter-cpp`
  - `tree-sitter-java`
  - `tree-sitter-go`
  - `tree-sitter-rust`
  - `tree-sitter-typescript`
- [x] Implement separate language-specific comparer modules for:
  - Python
  - C++
  - Java
  - Go
  - Rust
  - TypeScript
- [x] Use parser-backed extraction/normalization so comparison operates on the target function node rather than raw snippet text.
- [x] Switch RepoQA scoring to use the shared comparison package.
- [x] Return comparison metadata that helps explain match/mismatch decisions.
- [x] Add regression tests for the real near-match cases already observed in RepoQA prompted runs.

## Implementation plan

1. Create a shared `agent_evaluations.code_compare` package with:
   - dispatch entry point
   - comparer result type
   - shared tree-sitter utilities
   - language query definitions
2. Move current Python AST comparison into the shared package unchanged in behavior.
3. Add tree-sitter-backed comparers for C++, Java, Go, Rust, and TypeScript using explicit parser packages.
4. Normalize by:
   - parsing the snippet
   - extracting the function/method node
   - stripping comments/trivia
   - comparing canonical function representations
5. Update RepoQA shared scoring to call the new shared comparison API and include comparison metadata in results.
6. Add regression tests for:
   - true near-matches that should now compare equal
   - real wrong-function answers that should remain mismatches

## Notes

- Upstream RepoQA uses tree-sitter for extraction and comment removal, but BLEU for scoring. This task intentionally goes further by doing parser-backed semantic normalization for comparison.
- The shared comparison package should be reusable by future evaluations beyond RepoQA.