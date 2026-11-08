# HTTPX Tenacity

|            |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Package    | [![Latest PyPI Version](https://img.shields.io/pypi/v/httpx-tenacity.svg)](https://pypi.org/project/httpx-tenacity/) [![Supported Python Versions](https://img.shields.io/pypi/pyversions/httpx-tenacity.svg)](https://pypi.org/project/httpx-tenacity/)                                                                                                                                                                                                                                                                                                                                              |
| Meta       | [![Apache-2.0](https://img.shields.io/pypi/l/httpx-tenacity.svg)](LICENSE) [![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg)](.github/CODE_OF_CONDUCT.md) [![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/) [![Code Style Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black) [![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) |
| Automation | [![CI](https://github.com/Midnighter/httpx-tenacity/actions/workflows/main.yml/badge.svg)](https://github.com/Midnighter/httpx-tenacity/actions/workflows/main.yml) [![codecov](https://codecov.io/github/Midnighter/httpx-tenacity/graph/badge.svg?token=H51KS4D6M4)](https://codecov.io/github/Midnighter/httpx-tenacity)                                                                                                                                                                                                                                                                           |

_A lightweight package that provides tenacious (retrying) httpx and httpx2 transports._

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
`httpx_tenacity.httpx` or from `httpx_tenacity.httpx2`.

### Migrating from <0.3

Two breaking changes land in 0.3.0.

First, the transports moved out of the package root and `httpx` is no longer a required
dependency. Install `httpx-tenacity[httpx]` instead of `httpx-tenacity` and change your
imports. `RetryPolicy`, `SmartRetryPolicy`, and `RetryingT` keep their import paths.

```diff
-from httpx_tenacity import AsyncTenaciousTransport, TenaciousTransport
+from httpx_tenacity.httpx import AsyncTenaciousTransport, TenaciousTransport
```

The same applies to `HTTPXHTTPTransportKeywordArguments`. For HTTPX2, import the
transports from `httpx_tenacity.httpx2` instead. The transports' loggers follow their
modules and are now named `httpx_tenacity.httpx.tenacious_transport` and
`httpx_tenacity.httpx.async_tenacious_transport`.

Second, `TenaciousTransport.create()` and `AsyncTenaciousTransport.create()` take a
`policy` instead of the `max_attempts`, `multiplier`, `max_wait_seconds`,
`min_wait_seconds`, and `exponent_base` arguments. Pass them to `SmartRetryPolicy`.

```diff
-transport = TenaciousTransport.create(max_attempts=3)
+transport = TenaciousTransport.create(policy=SmartRetryPolicy(max_attempts=3))
```

## Usage

Wrap the requests of an HTTPX client with a transport that retries server-side issues
(HTTP 5xx errors and 429 Too Many Requests responses) and request errors:

```python
import httpx
from httpx_tenacity import SmartRetryPolicy
from httpx_tenacity.httpx import TenaciousTransport

transport = TenaciousTransport.create(policy=SmartRetryPolicy(max_attempts=3))

with httpx.Client(transport=transport) as client:
    response = client.get("https://api.example.com/data")
```

For HTTPX2, import `httpx2` instead of `httpx` and import the transports from
`httpx_tenacity.httpx2` instead of `httpx_tenacity.httpx`; everything else stays the
same. The [documentation](https://midnighter.github.io/httpx-tenacity/) shows every
example for both clients, including the asynchronous `AsyncTenaciousTransport`.
Transports, clients, and responses must all come from the same client:
`httpx_tenacity.httpx` works with `httpx` and `httpx_tenacity.httpx2` works with
`httpx2`.

### Using Both Clients Together

You can install both extras, `httpx-tenacity[httpx,httpx2]`, and use both integrations
in the same process. The retry policies are independent of the HTTP client, so you may
even share one policy between them. The HTTP objects, however, are **not
interchangeable**: an `httpx_tenacity.httpx` transport cannot be used with an
`httpx2.Client`, and an `httpx_tenacity.httpx2` transport cannot be used with an
`httpx.Client`.

## Copyright

-   Copyright © 2026 Moritz E. Beber.
-   Free software distributed under the [Apache Software License 2.0](./LICENSE).
