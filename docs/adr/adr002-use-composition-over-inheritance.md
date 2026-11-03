# ADR002 - Use composition over inheritance

- Date: 2026-01-11
- Status: ACCEPTED
- Author: Moritz E. Beber

## Decision

The tenacious transports subclass only the abstract `httpx.BaseTransport` / `httpx.AsyncBaseTransport` and wrap an injected transport and a tenacity retrying instance, instead of subclassing `httpx.HTTPTransport`. Each request is delegated to the wrapped transport inside a fresh copy of the retrying loop.

## Context

httpx separates clients from transports, and any object implementing `httpx.BaseTransport` or `httpx.AsyncBaseTransport` can be plugged into a client. Retrying is cross-cutting behaviour that should apply regardless of which transport sends the request: the default `HTTPTransport`, a `MockTransport` in tests, or third-party transports such as caching layers. It should also be possible to layer retrying with other wrapping transports in whatever order an application needs.

## Options

1. (SELECTED) Composition
2. Subclass the HTTP transports

### Option 1 (SELECTED): Composition

Subclass only the abstract base transports and wrap an injected transport, delegating each request to it inside the retrying loop.

#### Consequences

- Adopted because: it works with any transport implementing the base interface.
- Adopted because: it can be stacked with other wrapping transports in any order.
- Adopted because: the wrapper stays small and easy to test by injecting a `MockTransport` and a retrying instance.
- Adopted despite: `HTTPTransport`'s constructor options are not inherited, so `create(**kwargs)` has to forward them and type them separately (`HTTPXHTTPTransportKeywordArguments`).
- Adopted despite: the wrapper must forward lifecycle methods such as `close()` / `aclose()` to the wrapped transport.

### Option 2: Subclass the HTTP transports

Subclass `httpx.HTTPTransport` / `httpx.AsyncHTTPTransport` and override `handle_request` / `handle_async_request` to retry around the parent implementation.

#### Consequences

- Rejected because: retrying would be tied to the HTTP transports and unavailable for other transport types, such as `MockTransport` or third-party transports.
- Rejected because: it cannot be layered with other wrapping transports through composition.
- Rejected despite: it inherits the constructor options and the `close()` / `aclose()` lifecycle for free, leaving one object to configure.

## Supporting Material

- httpx transports documentation <https://www.python-httpx.org/advanced/transports/>
