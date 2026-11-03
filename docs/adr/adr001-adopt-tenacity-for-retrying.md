# ADR001 - Adopt tenacity for retrying

- Date: 2026-01-11
- Status: ACCEPTED
- Author: Moritz E. Beber

## Decision

Implement retry behaviour for httpx transports on top of the tenacity library instead of writing custom retry logic. The sync and async transports delegate stop, wait, and retry conditions to tenacity.

## Context

httpx has no built-in retry mechanism beyond connection-level retries on its `HTTPTransport`. The httpx issue requesting retries ([encode/httpx#108](https://github.com/encode/httpx/issues/108)) has drawn requests and workarounds from users since 2019, which shows a clear need among httpx users. Applications need retries for transient server-side failures, such as 5xx responses or 429 rate limiting. This has to work identically for sync and async clients. Writing and maintaining that logic by hand is error-prone and duplicates mature existing solutions.

## Options

1. (SELECTED) tenacity
2. backoff
3. urllib3 `Retry`
4. httpx-retries
5. stamina

### Option 1 (SELECTED): tenacity

A general-purpose retrying library with composable stop, wait, and retry strategies, used inside custom httpx transports.

#### Consequences

- Adopted because: it is a mature, widely used library with composable stop, wait, and retry strategies and native support for both sync and async code.
- Adopted because: it can be wrapped at the transport level, so retries apply to every request made through an httpx client.
- Adopted despite: it adds a runtime dependency, and its general-purpose API needs adapting to httpx (custom retry callback and `Retry-After`-aware wait).
- Adopted despite: its API is large and somewhat complex, so the transports wrap it in `create()` factories with sensible defaults.

### Option 2: backoff

A decorator-based library for retrying with exponential backoff.

#### Consequences

- Rejected because: it is built around function decorators, offering limited customisation and no natural fit at the httpx transport level.
- Rejected despite: it is lightweight and supports both sync and async code.

### Option 3: urllib3 `Retry`

urllib3's retry configuration, as used by requests through a mounted `HTTPAdapter`.

#### Consequences

- Rejected because: it is tied to requests and urllib3, does not carry over to httpx transports, and offers limited customisation.
- Rejected despite: it is well known, battle-tested, and handles `Retry-After` out of the box.

### Option 4: httpx-retries

A retrying transport package for httpx.

#### Consequences

- Rejected because: its retry and wait strategies offered too little customisation for the desired behaviour.
- Rejected despite: it is purpose-built for httpx and already works at the transport level.

### Option 5: stamina

An opinionated wrapper around tenacity with production-ready defaults.

#### Consequences

- Rejected because: it deliberately hides most of tenacity's configuration, making it less flexible than using tenacity directly.
- Rejected despite: it provides safe defaults and builds on the same proven retry engine.

## Supporting Material

- httpx issue requesting retries (encode/httpx#108) <https://github.com/encode/httpx/issues/108>
- tenacity documentation <https://tenacity.readthedocs.io/en/latest/>
- httpx transports documentation <https://www.python-httpx.org/advanced/transports/>
- backoff <https://github.com/litl/backoff>
- urllib3 `Retry` reference <https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html#urllib3.util.Retry>
- httpx-retries <https://github.com/will-ockmore/httpx-retries>
- stamina <https://github.com/hynek/stamina>
