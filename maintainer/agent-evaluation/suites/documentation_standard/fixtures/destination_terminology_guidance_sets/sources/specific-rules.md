### Apply the rules by context

| Context | Rule |
|---|---|
| Task | May retain conversational wording when defined and the task stands alone. Reference another task by title and full relative path. |
| Specification | Use product, interface, and domain terms, not task grouping or progress labels. Task references use title and path; other record references use description, ID, and link. |
| Requirements | State observable outcomes or constraints. Task organization, examples, quality descriptions, and implementation steps become requirements only when their observable meaning is required. Cross-record references use description, ID, and link. |
| Decisions | Name the material choice and tradeoff. Task references use title and path; other record references use description, ID, and link. |
| Source code and tests | Names describe behavior, interfaces, or domain concepts. A requirement ID supports traceability only when nearby text explains the behavior. Preserve established public names. |
| Developer documentation | Define specification terms and explain current implementation without requiring linked records. Links add detail. Generally omit requirement IDs; when needed, include description, ID, and link. |
| User documentation | Explain supported behavior and limitations in self-contained language. Developer links add detail. Remove inherited internal terms unless established for users. Generally omit task and requirement IDs. |
| Names and delivery records | Filenames, headings, generated labels, identifiers, test names, commit messages, and pull-request titles name behavior or components meaningful in their context. |

Reference examples:

- A task reference combines the descriptive title `Cache eviction` with the
  full relative path `../../tasks/cache-eviction.md`.
- A requirement reference combines
  `Expired entries are excluded (CACHE-004)` with
  `specifications/cache/requirements.md#cache-004`.
- `# CACHE-004: expired entries are excluded` explains the requirement traced
  by a test assertion.
