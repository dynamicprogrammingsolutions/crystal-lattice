# Continuation and Cache

## Parent continuation

```python
child = evaluation.run(
    "child",
    child_program,
    continue_from=parent,
)
```

Continuation requires:

- a parent snapshot;
- the same compatible environment fingerprint;
- successful snapshot serialization;
- a compatible workspace.

The parent `Run` and its snapshot remain unchanged.

When the parent used a reusable workspace factory, the child receives a fresh
workspace from that factory. Existing `Path` workspaces are not assumed to be
safe for automatic reuse; pass `workspace=` explicitly.

Crystal Lattice snapshots restore the immutable session and default request
overrides. Strings inside session data have occurrences of the old workspace
root replaced with the new root.

## Explicit cache keys

```python
run = evaluation.run(
    "investigation",
    investigate,
    workspace=repository,
    cache_key="investigation-v2",
)
```

The effective cache identity combines:

- the caller key;
- environment fingerprint;
- workspace fingerprint;
- parent snapshot hash;
- cache schema.

Program source is not inspected. Increment the caller key when program
semantics change.

## Cache-hit behavior

A cache hit does not open the run environment or execute the program. It
restores:

- program value;
- environment snapshot;
- environment observation;
- original evidence;
- program-created record artifacts;
- tracked Git changes;
- untracked files;
- cache source provenance.

Each invocation still gets its own canonical result artifact and, when a
workspace factory is used, its own clean workspace.

## Atomicity and corruption

Cache publication:

- holds a process-level file lock;
- writes a temporary entry;
- publishes only after a completion marker is present;
- does not expose partial entries.

Incomplete, unsupported, and corrupt entries produce an inspectable failed
`Run`; they are not silently treated as cache misses.

## Serialization boundary

The generic cache uses Python pickle for arbitrary program values and
environment observations. Environment snapshots may provide custom
serialization; `CrystalLatticeEnvironment` uses JSON.

Cache roots are trusted local artifacts. Never load a cache directory supplied
by an untrusted party.

An unpicklable value is valid for a normal run. Raw diagnostics fall back to a
text representation. If explicit caching requires serializing that value,
cache publication fails with an inspectable `cache.publish` error.

## Git workspaces

```python
repository = git_workspace(
    source="/path/to/repository",
    revision="abc123",
)
```

The helper:

- creates a detached worktree at the exact revision;
- records status, changed paths, and binary diff;
- retains untracked changed files for cache restoration;
- removes worktrees when `AgentEval.close()` runs.

Repository URLs use a reusable local clone cache. Pass `cache_root=` to control
its location; otherwise the helper uses the system temporary directory.