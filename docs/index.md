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

### Verifying a release

Each release attests that its wheel and source distribution were built by this
repository's release workflow from a commit on `main`. Download a distribution from
PyPI and check it with the [GitHub CLI](https://cli.github.com/), with `VERSION` set to
the release you want to check:

```sh
pip download --no-deps --only-binary :all: "httpx-tenacity==${VERSION}"
gh attestation verify "httpx_tenacity-${VERSION}-py3-none-any.whl" \
  --repo Midnighter/httpx-tenacity \
  --signer-workflow Midnighter/httpx-tenacity/.github/workflows/release.yml
```

The command exits with status 0 when the file verifies. Add `--format json` to see the
tag and commit it was built from. Releases up to 0.3.0 have no such attestation.

## Copyright

-   Copyright © 2026 Moritz E. Beber.
-   Free software distributed under the [Apache Software License
    2.0](https://www.apache.org/licenses/LICENSE-2.0.html).
