# ADR003 - Configure retries with a retry policy protocol

- Date: 2026-11-07
- Status: ACCEPTED
- Author: Moritz E. Beber

## Decision

The transports' `create()` factories take a `policy` that implements the `RetryPolicy` protocol instead of individual retry arguments. The transport calls the policy's `create()` method with the tenacity retrying class it needs, its HTTP client's request error and its own logger. The default policy, `SmartRetryPolicy`, is a `NamedTuple` that holds the retry settings, including the status codes and header that `smart_wait` reads.

## Context

`TenaciousTransport.create()` and `AsyncTenaciousTransport.create()` each took five retry arguments and repeated the same tenacity configuration. Settings added later, such as `smart_wait`'s status codes and header, could only be reached through `create()` by adding them to both factories. The planned httpx2 integration doubles the number of factories. It also needs each transport to retry its own client's request error, because `httpx2.RequestError` is not a subclass of `httpx.RequestError`. Passing the wrong exception does not fail; connection errors are simply no longer retried. Users who need full control can already pass a tenacity retrying instance to a transport's constructor, so `create()` remains the place where sensible defaults are applied, as in ADR001.

## Options

1. (SELECTED) A retry policy protocol with a default `NamedTuple` policy
2. Retry arguments on `create()` with a shared private helper
3. A policy value consumed by the transport constructor
4. A retry strategy with separate sync and async builders

### Option 1 (SELECTED): A retry policy protocol with a default `NamedTuple` policy

`RetryPolicy` is a `Protocol` with one method, `create(retrying_class, *, request_error, logger)`, which returns an instance of the given `tenacity.Retrying` or `tenacity.AsyncRetrying` class. `SmartRetryPolicy` implements it with the previous defaults. Each transport's `create()` accepts a policy, defaults to `SmartRetryPolicy()`, and passes its own retrying class, request error and module logger.

#### Consequences

- Adopted because: one policy object configures both the sync and the async transport, and will configure the transports of both HTTP clients.
- Adopted because: the transport supplies the retrying class and request error it knows, so users cannot pair a policy with the wrong mode or client.
- Adopted because: retry logs keep each transport's logger name, because the transport passes its own logger.
- Adopted because: new settings become policy fields with defaults instead of new arguments on every `create()`.
- Adopted because: a custom policy only needs a matching `create()` method, which mypy and ty check structurally.
- Adopted because: `SmartRetryPolicy` is a `NamedTuple`, the lightest-weight, truly immutable value object that Python provides.
- Adopted despite: it is a breaking change to the signature of `create()`.
- Adopted despite: the protocol is a public contract, so changing the parameters of its `create()` breaks third-party policies.
- Adopted despite: custom policies need the `RetryingT` type variable to annotate `create()`, so it becomes public API.
- Adopted despite: a `NamedTuple` accepts positional arguments and compares equal to a plain tuple, so the documentation uses keyword arguments.

### Option 2: Retry arguments on `create()` with a shared private helper

Keep the retry arguments on each `create()` and move the shared tenacity configuration into one private function.

#### Consequences

- Rejected because: every new setting has to be added to the signature of each `create()`, four of them once httpx2 is supported.
- Rejected because: the only way to customise retrying beyond those arguments is a complete tenacity retrying instance.
- Rejected despite: it adds no public API and does not break callers.

### Option 3: A policy value consumed by the transport constructor

Drop `create()`. The transport's `__init__` accepts either a frozen, keyword-only dataclass of retry settings or a tenacity retrying instance, and builds the retrying instance and the default inner transport itself.

#### Consequences

- Rejected because: the constructor would build objects as a side effect instead of only storing what it is given.
- Rejected despite: a keyword-only dataclass rejects positional arguments.
- Rejected despite: users would configure the inner transport with the HTTP client's own constructor, so `create()` would no longer need to forward and type its keyword arguments.

### Option 4: A retry strategy with separate sync and async builders

A `RetryStrategy` protocol with `build_sync_retrying()` and `build_async_retrying()` methods, and a default strategy that holds the retry settings, the retry predicate and the logging hook.

#### Consequences

- Rejected because: every implementation has to provide both builders, even when it only serves one mode.
- Rejected because: the strategy would choose the request error and the logger, although only the transport knows its HTTP client and logger.
- Rejected despite: the method names make the mode explicit.
