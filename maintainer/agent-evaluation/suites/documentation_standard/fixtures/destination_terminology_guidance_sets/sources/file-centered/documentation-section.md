## Write pages readers can use

Every file has its own purpose, readers, and interfaces. Requests,
conversations, tasks, specifications, existing files, and review comments help
determine the behavior required from a change.

Marked examples illustrate individual transfers, not a complete list.

1. In every file you create or change, choose names and organization that fit
   that file. Do not reuse wording merely because it appeared in another
   context.

   *Example:* A request for “calmer retries” may mean two delayed attempts; it
   does not establish `calm_retry`.

2. In a new specification, requirement, decision, source file, test, or
   documentation page, preserve approved behavior and constraints without
   copying task-only grouping, ordering, or progress terminology.

   *Example:* A task may group work under “Follow-up workstream: storage
   migration.” The specification describes “Persisted record migration”
   without adopting the workstream label.

3. In an existing file being changed, review terminology and organization
   already present. Replace wording inherited from planning, tracking, or
   another file when it does not fit the file's readers or interfaces.

   *Example:* A user guide may contain an old “Release checkpoint” heading
   copied from progress tracking. When the page is updated, organize it around
   the supported capability instead.

4. Keep exact wording when it is required or established by the product,
   public interface, or relevant domain.

   *Example:* Documentation and tests retain an established `--dry-run` flag.

5. Otherwise explain or translate terminology into the behavior, component,
   condition, outcome, or relationship the file's reader needs.

   *Example:* Developer documentation may describe a write-ahead journal. User
   documentation says that queued work survives a restart unless the storage
   mechanism is itself part of the public interface.

<!-- SPECIFIC_RULES -->

Use verified examples when showing input and result clarifies installation,
configuration, an API, or recovery. Check them against current implementation
or tests.

Keep tracking in its owning records and translate current limitations when
users need them.
