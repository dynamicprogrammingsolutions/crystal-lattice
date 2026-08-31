After upgrading Starlette, one of our custom `GZipResponder` subclasses stopped
working. Its constructor still calls `super().__init__(app, minimum_size)`, and
constructing it now fails with a `TypeError` saying that
`thread_minimum_size` is missing. Please inspect the gzip middleware and
existing tests, figure out what changed, and give me a focused plan for a
backwards-compatible fix and regression coverage. Don't change the code yet.