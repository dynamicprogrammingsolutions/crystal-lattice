# Guidance compiler quickstart

Check the current Crystal Lattice output:

```bash
python -m maintainer.guidance check \
  --bundle "$PWD/maintainer/guidance/current" \
  --target "$PWD/maintainer/guidance/targets/crystal-lattice" \
  --destination "$PWD"
```

Preview a candidate in a temporary destination:

```bash
python -m maintainer.guidance compile \
  --bundle /absolute/path/to/candidate \
  --target /absolute/path/to/project-owned/target \
  --destination /absolute/path/to/preview \
  --lock /absolute/path/to/preview.lock.json
```

Use `write` only after the candidate and affected project outputs have been
reviewed and approved.
