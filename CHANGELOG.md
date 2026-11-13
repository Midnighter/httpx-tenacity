# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-11-13

### Added

- Added support for Python 3.15.
- Added the `RetryPolicy` protocol and its default implementation
  `SmartRetryPolicy`, which configures retries for both transports and also
  sets the status codes and header that `smart_wait` reads. Custom policies
  can use the exported `RetryingT` type variable in their `create()` signature.
- Added the HTTPX2 integration `httpx_tenacity.httpx2` with its own
  `TenaciousTransport`, `AsyncTenaciousTransport` and
  `HTTPX2HTTPTransportKeywordArguments`, installable with the new `httpx2`
  extra, `pip install 'httpx-tenacity[httpx2]'`. Both integrations can be used
  in the same process, and a single `RetryPolicy` serves the transports of both
  clients.
- Added the `httpx` extra for the HTTPX integration `httpx_tenacity.httpx`.

### Changed

- **Breaking:** `TenaciousTransport.create()` and
  `AsyncTenaciousTransport.create()` take a `policy` instead of the
  `max_attempts`, `multiplier`, `max_wait_seconds`, `min_wait_seconds` and
  `exponent_base` arguments. Replace
  `TenaciousTransport.create(max_attempts=3)` with
  `TenaciousTransport.create(policy=SmartRetryPolicy(max_attempts=3))`.
- **Breaking:** `TenaciousTransport`, `AsyncTenaciousTransport` and
  `HTTPXHTTPTransportKeywordArguments` moved from the package root to
  `httpx_tenacity.httpx`. The package root keeps only `RetryPolicy`,
  `SmartRetryPolicy` and `RetryingT`, which import no HTTP client. The old
  root-level and module-level imports are removed without compatibility
  aliases. Change the imports as follows:

  ```diff
  -from httpx_tenacity import SmartRetryPolicy, TenaciousTransport
  +from httpx_tenacity import SmartRetryPolicy
  +from httpx_tenacity.httpx import TenaciousTransport
  ```

  For HTTPX2, import from `httpx_tenacity.httpx2` instead. A transport only
  works with the client it was written for: an `httpx_tenacity.httpx` transport
  does not work with `httpx2` and vice versa.
- **Breaking:** `httpx` is no longer a required dependency, and `tenacity` is
  the only one. Select the HTTP client with an extra. Replace
  `pip install httpx-tenacity` with `pip install 'httpx-tenacity[httpx]'`, or
  use `'httpx-tenacity[httpx2]'` or `'httpx-tenacity[httpx,httpx2]'`.
- The loggers of the transports now follow their modules. They are named
  `httpx_tenacity.httpx.tenacious_transport` and
  `httpx_tenacity.httpx.async_tenacious_transport` for HTTPX, and
  `httpx_tenacity.httpx2.tenacious_transport` and
  `httpx_tenacity.httpx2.async_tenacious_transport` for HTTPX2. Previously, the
  transports logged to `httpx_tenacity.tenacious_transport` and
  `httpx_tenacity.async_tenacious_transport`. Update logging configuration that
  refers to the old names.
- `smart_wait` and `is_server_side_issue` no longer depend on `httpx`. They only
  read the `status_code` and `headers` of the response, and accept the
  responses of either client.
- Pyodide compatibility tests now run against Pyodide 314.0.7 (Python 3.14) and
  cover both the `httpx` and `httpx2` integrations.

### Fixed

- `TenaciousTransport` and `AsyncTenaciousTransport` now enter, exit and close
  the transport they wrap. Previously, using them as context managers, via a
  client, or calling `close()` / `aclose()` never reached the inner transport,
  so the connection pool of the default `httpx.HTTPTransport` /
  `httpx.AsyncHTTPTransport` was never closed. The wrapper owns the inner
  transport, including one passed to `create(transport=...)`.

### Removed

- Dropped support for Python 3.10.

## [0.2.0] - 2026-03-22

### Added

- Made the default `smart_wait` strategy more configurable with custom response
  status codes and header
  ([#19](https://github.com/Midnighter/httpx-tenacity/pull/19)).

## [0.1.0] - 2026-01-12

### Added

- Released initial version of `httpx-tenacity` with support for automatic
  retry logic in HTTPX clients.
- Implemented `TenaciousTransport` for synchronous HTTPX clients.
- Implemented `AsyncTenaciousTransport` for asynchronous HTTPX clients.
