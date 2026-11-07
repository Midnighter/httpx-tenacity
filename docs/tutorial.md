## Overview

httpx-tenacity provides two transport classes that add automatic retry logic to
HTTPX:

-   [`TenaciousTransport`][httpx_tenacity.TenaciousTransport]: Synchronous
    transport for blocking requests
-   [`AsyncTenaciousTransport`][httpx_tenacity.AsyncTenaciousTransport]:
    Asynchronous transport for async/await requests

Both transports, when created with the default factory, automatically retry
requests when encountering server-side issues (HTTP 5xx errors and 429 Too Many
Requests responses) using exponential backoff with optional Retry-After header
support.

## Synchronous Usage

### Basic Setup

Create a client with automatic retry logic:

```python
import httpx
from httpx_tenacity import TenaciousTransport

transport = TenaciousTransport.create()
client = httpx.Client(transport=transport)

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

```python
import httpx
from httpx_tenacity import SmartRetryPolicy, TenaciousTransport

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

The same policy works for both the synchronous and the asynchronous transport.

### Passing Transport Configuration

Additional keyword arguments are passed to the underlying HTTPX transport:

```python
import httpx
from httpx_tenacity import SmartRetryPolicy, TenaciousTransport

transport = TenaciousTransport.create(
    policy=SmartRetryPolicy(max_attempts=5),
    verify=False,  # Disable SSL verification
    limits=httpx.Limits(max_connections=10),
)
client = httpx.Client(transport=transport)
```

### Monitoring Retries

Retries are logged at DEBUG level. Enable debug logging to see retry activity:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Custom Retry Policies

Any object with a `create()` method that matches the
[`RetryPolicy`][httpx_tenacity.RetryPolicy] protocol can replace the default
policy. The transport calls it with the tenacity retrying class it needs, its
HTTP client's request error, and its logger:

```python
import logging

import tenacity
from httpx_tenacity import RetryingT, TenaciousTransport


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
`Retrying` instance:

```python
import httpx
from tenacity import Retrying, stop_after_attempt, wait_fixed
from httpx_tenacity import TenaciousTransport

transport = TenaciousTransport(
    retry=Retrying(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
    ),
    transport=httpx.HTTPTransport(),
)
client = httpx.Client(transport=transport)
```

## Asynchronous Usage

The asynchronous transport works in an analogous manner and can be configured as
described above for the synchronous transport. Retrying also works with
concurrent requests over the same transport instance.

```python
import anyio
import httpx
from httpx_tenacity import AsyncTenaciousTransport


async def main():
    async with (
        httpx.AsyncClient(transport=AsyncTenaciousTransport.create()) as client,
        anyio.create_task_group() as tg,
    ):
        tg.start_soon(client.get, "https://api.example.com/data")
        tg.start_soon(client.post, "https://api.example.com/data")


anyio.run(main)
```
