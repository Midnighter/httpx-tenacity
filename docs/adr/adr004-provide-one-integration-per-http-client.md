# ADR004 - Provide one integration per HTTP client

- Date: 2026-11-08
- Status: ACCEPTED
- Author: Moritz E. Beber

## Decision

HTTPX becomes an optional dependency. The transports (`TenaciousTransport`, `AsyncTenaciousTransport`) and their keyword-argument `TypedDict` live in one sub-package per HTTP client, `httpx_tenacity.httpx` and `httpx_tenacity.httpx2`. Users select an integration explicitly by import, and each one is installed with the extra of the same name and guarded by an import error that names the extra. The client-independent core keeps its import paths: `RetryPolicy`, `SmartRetryPolicy` and `RetryingT` in the package root, and `smart_wait` and `is_server_side_issue` in `httpx_tenacity.wait` and `httpx_tenacity.retry_callback`. There is neither automatic client selection nor a compatibility alias for the old root imports.

## Context

HTTPX2 is a separate package that keeps the HTTPX API but defines its own classes. `Request`, `Response`, `Limits`, `Proxy`, the transports and `RequestError` of one client are distinct types from those of the other. The two clients do not interoperate: an `httpx.Client` with an HTTPX2 transport, and the reverse, fails with an `AssertionError`. Users should be able to install the library with either client, or both, without pulling in the one they do not use. The retrying logic itself does not depend on any HTTP client. `RetryPolicy` and `SmartRetryPolicy` (ADR003) only build tenacity retrying instances, and `smart_wait` and `is_server_side_issue` only read the `status_code` and `headers` of a response, which a private structural `Response` protocol describes. Each transport passes its own client's `RequestError` to the policy, which is required because `httpx2.RequestError` is not a subclass of `httpx.RequestError`, so one policy can configure the transports of both clients. The transports follow ADR002 and subclass only their client's abstract base transport, so each integration needs its own sync and async classes. The package is still in pre-alpha, and the release that introduces the integrations already contains the breaking change to `create()` (ADR003), so a breaking change to the import paths is acceptable. The same decision was made for httpx-limiter, which this ADR adapts.

## Options

1. (SELECTED) One integration package per HTTP client
2. Select the HTTP client automatically
3. One generic transport parametrized over the client
4. Import aliasing so the same names come from either client
5. Keep HTTPX required and add HTTPX2 only as an extra
6. One integration package per HTTP client with compatibility aliases at the root

### Option 1 (SELECTED): One integration package per HTTP client

Move the transports and `HTTPXHTTPTransportKeywordArguments` into `httpx_tenacity.httpx` and add `httpx_tenacity.httpx2` with `TenaciousTransport`, `AsyncTenaciousTransport` and `HTTPX2HTTPTransportKeywordArguments`. Each package imports only its own client and never the other integration, annotates with that client's types, and raises a `ModuleNotFoundError` that names the extra to install when the client is missing. Other import errors are re-raised so that a missing transitive dependency is not hidden. The core in the package root imports no HTTP client.

#### Consequences

- Adopted because: users install only the client they use, and `tenacity` is the only required dependency.
- Adopted because: each integration is typed with its own client's classes, so type checkers reject mixing a transport, `Limits` or `Proxy` of one client with the other.
- Adopted because: both integrations can be used in the same process, and one `SmartRetryPolicy` or custom `RetryPolicy` configures the transports of both.
- Adopted because: both clients are treated symmetrically, so adding or dropping a client later does not move the other one.
- Adopted because: the logger of each transport follows its module and therefore tells the retry logs of the two clients apart.
- Adopted despite: the transport code exists twice, once per client, in sync and async variants, and every HTTP-facing change has to land in both.
- Adopted despite: it is a breaking change. Every user must change the imports of the transports and the keyword-argument `TypedDict` and select an extra when installing.
- Adopted despite: `Limits` and `Proxy` are client-specific types. The keyword-argument `TypedDict` and the `create()` signature therefore have to be defined per client, because mypy and ty reject a client-neutral protocol where `create()` forwards `**kwargs` to the client's transport.
- Adopted despite: the loggers are renamed, for example from `httpx_tenacity.tenacious_transport` to `httpx_tenacity.httpx.tenacious_transport`. Logging configuration that targets the old names stops matching.
- Adopted despite: the public classes exist twice under the same names, once per sub-package.

### Option 2: Select the HTTP client automatically

Expose one set of transports in the root that use whichever client is installed, falling back from one to the other.

#### Consequences

- Rejected because: the choice is ambiguous when both clients are installed, and the result depends on the environment instead of the code.
- Rejected because: the transports cannot be annotated with one client's types, so mix-ups would only fail at runtime with an `AssertionError`.
- Rejected despite: users would not need to choose an import path.

### Option 3: One generic transport parametrized over the client

Write the transport once and bind it to a client with class factories or generics, for example `make_transport(httpx2)`.

#### Consequences

- Rejected because: the base transports, `RequestError`, `Limits` and `Proxy` are different classes in each client, so the class would have to be created at runtime and could not subclass the client's base transport in a way static checkers understand.
- Rejected because: `create()` forwards the client's constructor arguments, whose `Limits` and `Proxy` types cannot be expressed without either client-specific code or a loss of type safety.
- Rejected despite: the transport logic would exist only once.

### Option 4: Import aliasing so the same names come from either client

Use one set of module-level names and rebind them to the other client's classes, for example with a conditional import.

#### Consequences

- Rejected because: names that mean different classes depending on the environment hide which client is in use and defeat static typing.
- Rejected because: it cannot serve both clients in the same process.
- Rejected despite: the transport code would not be duplicated, and the call sites would look the same for both clients.

### Option 5: Keep HTTPX required and add HTTPX2 only as an extra

Keep `httpx` as a required dependency and the transports in the package root, and add only `httpx_tenacity.httpx2` behind a `httpx2` extra.

#### Consequences

- Rejected because: HTTPX2 users would still have to install HTTPX.
- Rejected because: the two clients would be exposed asymmetrically, with one at the root and one in a sub-package.
- Rejected despite: existing imports and installations would keep working without changes.

### Option 6: One integration package per HTTP client with compatibility aliases at the root

Use the sub-packages from option 1, but keep the old root imports of the HTTPX transports as aliases.

#### Consequences

- Rejected because: the root aliases must import HTTPX, so the root would no longer be client-independent, unless a lazy module `__getattr__` is added, which complicates the core.
- Rejected because: the package is in pre-alpha and the release already contains a breaking change, so a clean break is simpler for users and maintainers than a transition period.
- Rejected despite: existing code would keep working for a transition period.

## Supporting Material

- Pull request introducing the integrations in httpx-limiter <https://github.com/Midnighter/httpx-limiter/pull/417>
- httpx-limiter ADR002 <https://github.com/Midnighter/httpx-limiter/blob/main/docs/adr/adr002-provide-one-integration-per-http-client.md>
- HTTPX2 on PyPI <https://pypi.org/project/httpx2/>
