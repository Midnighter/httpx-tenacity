## Overview

httpx-tenacity adds automatic retry logic to HTTPX and HTTPX2. For each of the two
HTTP clients, it provides two transport classes:

-   `TenaciousTransport`: Synchronous transport for blocking requests
-   `AsyncTenaciousTransport`: Asynchronous transport for async/await requests

You choose the integration explicitly by importing the transports from
[`httpx_tenacity.httpx`][httpx_tenacity.httpx] for HTTPX or from
[`httpx_tenacity.httpx2`][httpx_tenacity.httpx2] for HTTPX2. Each of them requires the
matching extra, `httpx` or `httpx2`.

Every example below is shown for both HTTP clients. Pick the tab that matches the
client you installed. Transports, clients, and responses must all come from the same
client: `httpx_tenacity.httpx` works with `httpx` and `httpx_tenacity.httpx2` works
with `httpx2`. Mixing them fails.

Both transports, when created with the default factory, automatically retry
requests when encountering server-side issues (HTTP 5xx errors and 429 Too Many
Requests responses) using exponential backoff with optional Retry-After header
support.

## Synchronous Usage

### Basic Setup

Create a client with automatic retry logic:

=== "HTTPX"

    ```python
    import httpx
    from httpx_tenacity.httpx import TenaciousTransport

    transport = TenaciousTransport.create()
    client = httpx.Client(transport=transport)

    response = client.get("https://api.example.com/data")
    ```

=== "HTTPX2"

    ```python
    import httpx2
    from httpx_tenacity.httpx2 import TenaciousTransport

    transport = TenaciousTransport.create()
    client = httpx2.Client(transport=transport)

    response = client.get("https://api.example.com/data")
    ```

The `create()` method uses the default
[`SmartRetryPolicy`][httpx_tenacity.SmartRetryPolicy], which has sensible
defaults:

-   Maximum 5 retry attempts
-   Exponential backoff with base 2
-   Minimum wait of 0.02 seconds between retries
-   Maximum wait of 60 seconds between retries
-   The wait time from the Retry-After header of 429 Too Many Requests responses

### Configuring Retry Behavior

Pass a configured policy when creating the transport:

=== "HTTPX"

    ```python
    import httpx
    from httpx_tenacity import SmartRetryPolicy
    from httpx_tenacity.httpx import TenaciousTransport

    transport = TenaciousTransport.create(
        policy=SmartRetryPolicy(
            max_attempts=10,  # Try up to 10 times
            multiplier=2,  # Exponential backoff multiplier
            min_wait_seconds=0.1,  # Minimum 0.1 second between retries
            max_wait_seconds=120,  # Maximum 2 minutes between retries
            exponent_base=2,  # Base for exponential calculation
            status_code=(429, 503),  # Responses whose header sets the wait time
            header="Retry-After",  # Header that holds the wait time in seconds
        ),
    )
    client = httpx.Client(transport=transport)
    ```

=== "HTTPX2"

    ```python
    import httpx2
    from httpx_tenacity import SmartRetryPolicy
    from httpx_tenacity.httpx2 import TenaciousTransport

    transport = TenaciousTransport.create(
        policy=SmartRetryPolicy(
            max_attempts=10,  # Try up to 10 times
            multiplier=2,  # Exponential backoff multiplier
            min_wait_seconds=0.1,  # Minimum 0.1 second between retries
            max_wait_seconds=120,  # Maximum 2 minutes between retries
            exponent_base=2,  # Base for exponential calculation
            status_code=(429, 503),  # Responses whose header sets the wait time
            header="Retry-After",  # Header that holds the wait time in seconds
        ),
    )
    client = httpx2.Client(transport=transport)
    ```

A policy does not depend on the HTTP client. The same
[`SmartRetryPolicy`][httpx_tenacity.SmartRetryPolicy] works with the synchronous and the
asynchronous transport of both HTTPX and HTTPX2.

### Passing Transport Configuration

Additional keyword arguments are passed to the underlying transport of the selected
client. The accepted keywords are described by
[`HTTPXHTTPTransportKeywordArguments`][httpx_tenacity.httpx.HTTPXHTTPTransportKeywordArguments]
and
[`HTTPX2HTTPTransportKeywordArguments`][httpx_tenacity.httpx2.HTTPX2HTTPTransportKeywordArguments].
Types such as `Limits` and `Proxy` must come from the selected client.

=== "HTTPX"

    ```python
    import httpx
    from httpx_tenacity import SmartRetryPolicy
    from httpx_tenacity.httpx import TenaciousTransport

    transport = TenaciousTransport.create(
        policy=SmartRetryPolicy(max_attempts=5),
        verify=False,  # Disable SSL verification
        limits=httpx.Limits(max_connections=10),
    )
    client = httpx.Client(transport=transport)
    ```

=== "HTTPX2"

    ```python
    import httpx2
    from httpx_tenacity import SmartRetryPolicy
    from httpx_tenacity.httpx2 import TenaciousTransport

    transport = TenaciousTransport.create(
        policy=SmartRetryPolicy(max_attempts=5),
        verify=False,  # Disable SSL verification
        limits=httpx2.Limits(max_connections=10),
    )
    client = httpx2.Client(transport=transport)
    ```

### Monitoring Retries

Retries are logged at DEBUG level. Enable debug logging to see retry activity:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

The transports log to loggers named after their modules, for example
`httpx_tenacity.httpx.tenacious_transport` and
`httpx_tenacity.httpx2.tenacious_transport`.

### Custom Retry Policies

Any object with a `create()` method that matches the
[`RetryPolicy`][httpx_tenacity.RetryPolicy] protocol can replace the default
policy. The transport calls it with the tenacity retrying class it needs, its
HTTP client's request error, and its logger. Because the transport passes its own
client's `RequestError`, one policy serves the transports of both clients:

=== "HTTPX"

    ```python
    import logging

    import tenacity
    from httpx_tenacity import RetryingT
    from httpx_tenacity.httpx import TenaciousTransport


    class FixedRetryPolicy:
        def create(
            self,
            retrying_class: type[RetryingT],
            *,
            request_error: type[Exception],
            logger: logging.Logger,
        ) -> RetryingT:
            return retrying_class(
                retry=tenacity.retry_if_exception_type(request_error),
                stop=tenacity.stop_after_attempt(3),
                wait=tenacity.wait_fixed(1),
                before_sleep=tenacity.before_sleep_log(logger, logging.DEBUG),
                reraise=True,
            )


    transport = TenaciousTransport.create(policy=FixedRetryPolicy())
    ```

=== "HTTPX2"

    ```python
    import logging

    import tenacity
    from httpx_tenacity import RetryingT
    from httpx_tenacity.httpx2 import TenaciousTransport


    class FixedRetryPolicy:
        def create(
            self,
            retrying_class: type[RetryingT],
            *,
            request_error: type[Exception],
            logger: logging.Logger,
        ) -> RetryingT:
            return retrying_class(
                retry=tenacity.retry_if_exception_type(request_error),
                stop=tenacity.stop_after_attempt(3),
                wait=tenacity.wait_fixed(1),
                before_sleep=tenacity.before_sleep_log(logger, logging.DEBUG),
                reraise=True,
            )


    transport = TenaciousTransport.create(policy=FixedRetryPolicy())
    ```

### Completely Custom Retry Logic

For full control over retry behavior, provide a custom tenacity
`Retrying` instance together with the transport that handles the requests. In that
case, you decide what to retry, so use the `RequestError` of the selected client:
`httpx.RequestError` is not a subclass of `httpx2.RequestError`, and the other way
around.

=== "HTTPX"

    ```python
    import httpx
    from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed
    from httpx_tenacity.httpx import TenaciousTransport

    transport = TenaciousTransport(
        retry=Retrying(
            retry=retry_if_exception_type(httpx.RequestError),
            stop=stop_after_attempt(3),
            wait=wait_fixed(1),
        ),
        transport=httpx.HTTPTransport(),
    )
    client = httpx.Client(transport=transport)
    ```

=== "HTTPX2"

    ```python
    import httpx2
    from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_fixed
    from httpx_tenacity.httpx2 import TenaciousTransport

    transport = TenaciousTransport(
        retry=Retrying(
            retry=retry_if_exception_type(httpx2.RequestError),
            stop=stop_after_attempt(3),
            wait=wait_fixed(1),
        ),
        transport=httpx2.HTTPTransport(),
    )
    client = httpx2.Client(transport=transport)
    ```

## Asynchronous Usage

The asynchronous transport works in an analogous manner and can be configured as
described above for the synchronous transport. Retrying also works with
concurrent requests over the same transport instance.

=== "HTTPX"

    ```python
    import anyio
    import httpx
    from httpx_tenacity.httpx import AsyncTenaciousTransport


    async def main():
        async with (
            httpx.AsyncClient(transport=AsyncTenaciousTransport.create()) as client,
            anyio.create_task_group() as tg,
        ):
            tg.start_soon(client.get, "https://api.example.com/data")
            tg.start_soon(client.post, "https://api.example.com/data")


    anyio.run(main)
    ```

=== "HTTPX2"

    ```python
    import anyio
    import httpx2
    from httpx_tenacity.httpx2 import AsyncTenaciousTransport


    async def main():
        async with (
            httpx2.AsyncClient(transport=AsyncTenaciousTransport.create()) as client,
            anyio.create_task_group() as tg,
        ):
            tg.start_soon(client.get, "https://api.example.com/data")
            tg.start_soon(client.post, "https://api.example.com/data")


    anyio.run(main)
    ```

## Using Both Clients Together

You can install both extras, `httpx-tenacity[httpx,httpx2]`, and use both integrations
in the same process. The policy is independent of the HTTP client, so you may even share
one policy between them. The HTTP objects, however, are **not interchangeable**: an
`httpx_tenacity.httpx` transport cannot be used with an `httpx2.Client`, and an
`httpx_tenacity.httpx2` transport cannot be used with an `httpx.Client`.

```python
import httpx
import httpx2
from httpx_tenacity import SmartRetryPolicy
from httpx_tenacity.httpx import TenaciousTransport as HTTPXTransport
from httpx_tenacity.httpx2 import TenaciousTransport as HTTPX2Transport

policy = SmartRetryPolicy(max_attempts=3)

with (
    httpx.Client(transport=HTTPXTransport.create(policy=policy)) as old,
    httpx2.Client(transport=HTTPX2Transport.create(policy=policy)) as new,
):
    first = old.get("https://api.example.com/data")  # an httpx.Response
    second = new.get("https://api.example.com/data")  # an httpx2.Response
```
