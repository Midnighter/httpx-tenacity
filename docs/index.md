# HTTPX Tenacity

A lightweight package that provides tenacious (retrying) httpx and httpx2 transports.

## Installation

The package is published on [PyPI](https://pypi.org/project/httpx-tenacity/). Plain
`pip install httpx-tenacity` installs only the shared core with the retry policies,
which contains no HTTP client. Select the HTTP client you use with an extra, `httpx` or
`httpx2`.

```sh
pip install 'httpx-tenacity[httpx]'
pip install 'httpx-tenacity[httpx2]'
```

To use both HTTP clients in the same process, install both extras.

```sh
pip install 'httpx-tenacity[httpx,httpx2]'
```

There is no automatic fallback: you choose the integration explicitly by importing from
`httpx_tenacity.httpx` or from `httpx_tenacity.httpx2`. The retry policies, such as
[`SmartRetryPolicy`][httpx_tenacity.SmartRetryPolicy], are independent of the HTTP
client and work with the transports of both integrations.

=== "HTTPX"

    ```python
    import httpx
    from httpx_tenacity import SmartRetryPolicy
    from httpx_tenacity.httpx import TenaciousTransport

    transport = TenaciousTransport.create(policy=SmartRetryPolicy(max_attempts=3))
    client = httpx.Client(transport=transport)

    response = client.get("https://api.example.com/data")
    ```

=== "HTTPX2"

    ```python
    import httpx2
    from httpx_tenacity import SmartRetryPolicy
    from httpx_tenacity.httpx2 import TenaciousTransport

    transport = TenaciousTransport.create(policy=SmartRetryPolicy(max_attempts=3))
    client = httpx2.Client(transport=transport)

    response = client.get("https://api.example.com/data")
    ```

The [tutorial](tutorial.md) shows more examples, including the asynchronous
transports.

### Migrating from <0.3

The transports moved out of the package root and `httpx` is no longer a required
dependency. Install `httpx-tenacity[httpx]` instead of `httpx-tenacity` and change your
imports. `RetryPolicy`, `SmartRetryPolicy`, and `RetryingT` keep their import paths.

```diff
-from httpx_tenacity import TenaciousTransport
+from httpx_tenacity.httpx import TenaciousTransport
```

The same applies to `AsyncTenaciousTransport` and
`HTTPXHTTPTransportKeywordArguments`. For HTTPX2, import them from
`httpx_tenacity.httpx2` instead.

Additionally, `create()` takes a `policy` instead of the `max_attempts`, `multiplier`,
`max_wait_seconds`, `min_wait_seconds`, and `exponent_base` arguments.

```diff
-transport = TenaciousTransport.create(max_attempts=3)
+transport = TenaciousTransport.create(policy=SmartRetryPolicy(max_attempts=3))
```

## Copyright

-   Copyright © 2026 Moritz E. Beber.
-   Free software distributed under the [Apache Software License
    2.0](https://www.apache.org/licenses/LICENSE-2.0.html).
