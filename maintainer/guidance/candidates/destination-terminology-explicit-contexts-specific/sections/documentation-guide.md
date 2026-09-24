## Write pages readers can use

Requests and conversations describe outcomes; tasks record approved work;
specifications, requirements, and decisions define intended behavior and
constraints; code, tests, and documentation maintain the system.

1. Carry required behavior between these contexts, but choose names and
   organization for the specification, requirement, decision, source file,
   test, or documentation page. Do not introduce wording merely because it
   appeared in an earlier context.

   *Example:* A request for “gentler backoff” may mean two delayed retries; it
   does not establish `gentle_retry`.

2. When writing a specification, requirement, decision, source file, test, or
   documentation page from a task, preserve approved behavior and constraints
   without copying task-only grouping, ordering, or progress terminology.

   *Example:* A task may group work under “Follow-up group: journal
   conversion.” The specification describes persisted record migration without
   adopting the group label.

3. Existing wording is separate scope. An unexplained release, phase, or
   progress label is not established merely because it is present. If cleanup
   is unauthorized, pause that file, explain the reader concern, recommend a
   replacement, and ask one focused confirmation question; do not silently
   remove or preserve it.

   *Example:* A user guide may contain an old “Launch packet” heading. A change
   to the page does not by itself authorize reorganizing that heading; raise
   the question before editing it.

4. Keep exact wording when it is required or established by the product,
   public interface, or relevant domain.

   *Example:* Documentation and tests retain an established `--dry-run` flag.

5. Otherwise explain or translate terminology into the behavior, component,
   condition, outcome, or relationship needed in that context.

   *Example:* Developer documentation may describe a write-ahead journal. User
   documentation says that queued work survives a restart unless the storage
   mechanism is itself part of the public interface.

### Apply the rules by context

| Context | Rule |
|---|---|
| Task | May retain conversational wording when it is defined and the task remains understandable without the conversation. Reference another task by descriptive title and full relative path. |
| Specification | Use product, interface, and domain terms rather than task grouping or progress labels. Reference a task by title and path without appending a local number, stage, or nickname. Other record references use description, stable ID when useful, and link. |
| Requirements | State observable outcomes or constraints. Task organization, examples, quality descriptions, and implementation steps become requirements only when their observable meaning is required. Cross-record references use description, stable ID, and link. |
| Decisions | Name the material choice and tradeoff. Task references use title and path; other record references use description, stable ID, and link. |
| Source code and tests | Names describe behavior, interfaces, or domain concepts. A requirement ID supports traceability only when nearby text explains the behavior. Preserve established public names. |
| Developer documentation | Define specification terms and explain current implementation without requiring linked records. Links add detail. Generally omit requirement IDs; when needed, include description, ID, and link. |
| User documentation | Explain supported behavior and limitations in self-contained language. Developer links add optional detail. Generally omit task and requirement IDs. Pause the affected file and ask before changing internal-looking wording when cleanup is unauthorized. |
| Names and delivery records | Filenames, headings, generated labels, identifiers, test names, commit messages, and pull-request titles name behavior or components meaningful in their context. |

Reference examples:

- A requirement reference combines
  `Expired entries are excluded (CACHE-004)` with
  `specifications/cache/requirements.md#cache-004`.
- `# CACHE-004: expired entries are excluded` explains the requirement traced
  by a test assertion.

Keep tracking in its owning records and translate current limitations when
users need them.