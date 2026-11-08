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

The following helpers, which the default policy is built from, are client-independent
as well. They are not exported by the package root, so import them from their own
modules:

* [`smart_wait`][httpx_tenacity.wait.smart_wait] from `httpx_tenacity.wait`
* [`is_server_side_issue`][httpx_tenacity.retry_callback.is_server_side_issue] from
  `httpx_tenacity.retry_callback`

::: httpx_tenacity.wait
    options:
        members:
            - smart_wait

::: httpx_tenacity.retry_callback
    options:
        members:
            - is_server_side_issue

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
