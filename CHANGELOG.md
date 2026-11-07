# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added support for Python 3.15.
- Added the `RetryPolicy` protocol and its default implementation
  `SmartRetryPolicy`, which configures retries for both transports and also
  sets the status codes and header that `smart_wait` reads. Custom policies
  can use the exported `RetryingT` type variable in their `create()` signature.

### Changed

- **Breaking:** `TenaciousTransport.create()` and
  `AsyncTenaciousTransport.create()` take a `policy` instead of the
  `max_attempts`, `multiplier`, `max_wait_seconds`, `min_wait_seconds` and
  `exponent_base` arguments. Replace
  `TenaciousTransport.create(max_attempts=3)` with
  `TenaciousTransport.create(policy=SmartRetryPolicy(max_attempts=3))`.

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
