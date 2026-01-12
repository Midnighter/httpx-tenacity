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

The `create()` method constructs a transport with sensible defaults:

-   Maximum 5 retry attempts
-   Exponential backoff with base 2
-   Minimum wait of 0.02 seconds between retries
-   Maximum wait of 60 seconds between retries

### Configuring Retry Behavior

Adjust retry parameters when creating the transport:

```python
transport = TenaciousTransport.create(
    max_attempts=10,           # Try up to 10 times
    multiplier=2,              # Exponential backoff multiplier
    min_wait_seconds=0.1,      # Minimum 0.1 second between retries
    max_wait_seconds=120,      # Maximum 2 minutes between retries
    exponent_base=2,           # Base for exponential calculation
)
client = httpx.Client(transport=transport)
```

### Passing Transport Configuration

Additional keyword arguments are passed to the underlying HTTPX transport:

```python
transport = TenaciousTransport.create(
    max_attempts=5,
    verify=False,              # Disable SSL verification
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

### Completely Custom Retry Logic

For full control over retry behavior, provide a custom tenacity
`Retrying` instance:

```python
from tenacity import Retrying, stop_after_attempt, wait_fixed
from httpx_tenacity import TenaciousTransport

transport = TenaciousTransport(retry=Retrying(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
))
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


async def fetch_data():
    async with (
        httpx.AsyncClient(transport=AsyncTenaciousTransport.create()) as client,
        anyio.create_task_group() as tg,
    ):
        tg.start_soon(client.get, "https://api.example.com/data")
        tg.start_soon(client.post, "https://api.example.com/data")
```
