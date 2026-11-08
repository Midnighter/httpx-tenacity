## Retry policies

The following symbols are exposed to the user by the client-independent package
root:

* [`RetryPolicy`][httpx_tenacity.RetryPolicy]
* [`SmartRetryPolicy`][httpx_tenacity.SmartRetryPolicy]
* [`RetryingT`][httpx_tenacity.RetryingT]

::: httpx_tenacity
    options:
        members:
            - RetryPolicy
            - SmartRetryPolicy
            - RetryingT

## HTTPX

The following symbols are exposed to the user by `httpx_tenacity.httpx`, which
requires the `httpx` extra:

* [`TenaciousTransport`][httpx_tenacity.httpx.TenaciousTransport]
* [`AsyncTenaciousTransport`][httpx_tenacity.httpx.AsyncTenaciousTransport]
* [`HTTPXHTTPTransportKeywordArguments`][httpx_tenacity.httpx.HTTPXHTTPTransportKeywordArguments]

::: httpx_tenacity.httpx
    options:
        members:
            - TenaciousTransport
            - AsyncTenaciousTransport
            - HTTPXHTTPTransportKeywordArguments

## HTTPX2

The following symbols are exposed to the user by `httpx_tenacity.httpx2`, which
requires the `httpx2` extra:

* [`TenaciousTransport`][httpx_tenacity.httpx2.TenaciousTransport]
* [`AsyncTenaciousTransport`][httpx_tenacity.httpx2.AsyncTenaciousTransport]
* [`HTTPX2HTTPTransportKeywordArguments`][httpx_tenacity.httpx2.HTTPX2HTTPTransportKeywordArguments]

::: httpx_tenacity.httpx2
    options:
        members:
            - TenaciousTransport
            - AsyncTenaciousTransport
            - HTTPX2HTTPTransportKeywordArguments
