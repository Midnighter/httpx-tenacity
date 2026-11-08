# Copyright (c) 2026 Moritz E. Beber
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.


"""
Provide typing examples for the HTTPX2 integration.

These examples are never run. `tests/unit/test_typing.py` checks them with mypy and
fails if mypy reports any error, so a regression in the public typing is caught.

"""

from __future__ import annotations

import logging
import ssl

import httpx2
import tenacity

from httpx_tenacity import RetryPolicy, RetryingT, SmartRetryPolicy
from httpx_tenacity.httpx2 import (
    AsyncTenaciousTransport,
    HTTPX2HTTPTransportKeywordArguments,
    TenaciousTransport,
)


class CustomPolicy:
    """A custom retry policy that is not derived from `RetryPolicy`."""

    def create(
        self,
        retrying_class: type[RetryingT],
        *,
        request_error: type[Exception],
        logger: logging.Logger,
    ) -> RetryingT:
        """Create a retrying instance that retries request errors twice."""
        return retrying_class(
            retry=tenacity.retry_if_exception_type(request_error),
            stop=tenacity.stop_after_attempt(2),
            before_sleep=tenacity.before_sleep_log(logger, logging.DEBUG),
        )


class CustomTransport(httpx2.BaseTransport):
    """A custom synchronous transport that can be wrapped."""

    def handle_request(self, request: httpx2.Request) -> httpx2.Response:
        """Return an empty response."""
        return httpx2.Response(200, request=request)


class CustomAsyncTransport(httpx2.AsyncBaseTransport):
    """A custom asynchronous transport that can be wrapped."""

    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        """Return an empty response."""
        return httpx2.Response(200, request=request)


def create_sync() -> httpx2.Client:
    """Create synchronous transports through the factory and use them in a client."""
    TenaciousTransport.create()
    TenaciousTransport.create(policy=SmartRetryPolicy(max_attempts=3))
    TenaciousTransport.create(CustomPolicy(), CustomTransport())
    TenaciousTransport.create(
        policy=SmartRetryPolicy(),
        verify=ssl.create_default_context(),
        cert=("cert.pem", "key.pem"),
        trust_env=False,
        http1=True,
        http2=False,
        limits=httpx2.Limits(max_connections=10),
        proxy=httpx2.Proxy("http://localhost:8080"),
        local_address="0.0.0.0",  # noqa: S104
        retries=2,
    )
    TenaciousTransport.create(proxy=httpx2.URL("http://localhost:8080"))
    TenaciousTransport.create(proxy="http://localhost:8080", uds="/tmp/http.sock")  # noqa: S108
    transport = TenaciousTransport.create(policy=SmartRetryPolicy())
    return httpx2.Client(transport=transport)


def create_async() -> httpx2.AsyncClient:
    """Create asynchronous transports through the factory and use them in a client."""
    AsyncTenaciousTransport.create()
    AsyncTenaciousTransport.create(policy=SmartRetryPolicy(max_attempts=3))
    AsyncTenaciousTransport.create(CustomPolicy(), CustomAsyncTransport())
    AsyncTenaciousTransport.create(
        policy=SmartRetryPolicy(),
        verify="ca.pem",
        cert="cert.pem",
        trust_env=True,
        http1=False,
        http2=True,
        limits=httpx2.Limits(max_connections=10),
        proxy=httpx2.Proxy("http://localhost:8080"),
        local_address="0.0.0.0",  # noqa: S104
        retries=2,
    )
    AsyncTenaciousTransport.create(proxy=httpx2.URL("http://localhost:8080"))
    AsyncTenaciousTransport.create(proxy="http://localhost:8080", verify=False)
    transport = AsyncTenaciousTransport.create(policy=SmartRetryPolicy())
    return httpx2.AsyncClient(transport=transport)


def construct() -> None:
    """Construct the transports from a retrying instance and a transport."""
    TenaciousTransport(
        retry=tenacity.Retrying(stop=tenacity.stop_after_attempt(2)),
        transport=CustomTransport(),
    )
    TenaciousTransport(
        retry=tenacity.Retrying(),
        transport=httpx2.HTTPTransport(),
    )
    TenaciousTransport(
        retry=tenacity.Retrying(),
        transport=httpx2.MockTransport(
            lambda request: httpx2.Response(200, request=request),
        ),
    )
    TenaciousTransport(
        retry=tenacity.Retrying(),
        transport=TenaciousTransport.create(),
    )
    AsyncTenaciousTransport(
        retry=tenacity.AsyncRetrying(stop=tenacity.stop_after_attempt(2)),
        transport=CustomAsyncTransport(),
    )
    AsyncTenaciousTransport(
        retry=tenacity.AsyncRetrying(),
        transport=httpx2.AsyncHTTPTransport(),
    )
    AsyncTenaciousTransport(
        retry=tenacity.AsyncRetrying(),
        transport=httpx2.MockTransport(
            lambda request: httpx2.Response(200, request=request),
        ),
    )
    AsyncTenaciousTransport(
        retry=tenacity.AsyncRetrying(),
        transport=AsyncTenaciousTransport.create(),
    )


def use_keyword_arguments() -> None:
    """Pass a dictionary of keyword arguments to the factories."""
    configuration: HTTPX2HTTPTransportKeywordArguments = {
        "verify": ssl.create_default_context(),
        "cert": "cert.pem",
        "trust_env": False,
        "http1": True,
        "http2": False,
        "limits": httpx2.Limits(max_connections=10),
        "proxy": httpx2.Proxy("http://localhost:8080"),
        "uds": None,
        "local_address": None,
        "retries": 2,
        "socket_options": None,
    }
    TenaciousTransport.create(**configuration)
    AsyncTenaciousTransport.create(SmartRetryPolicy(), **configuration)
    empty: HTTPX2HTTPTransportKeywordArguments = {}
    TenaciousTransport.create(CustomPolicy(), **empty)


def use_policies() -> None:
    """Use the policies with both kinds of transports."""
    policies: list[RetryPolicy] = [SmartRetryPolicy(), CustomPolicy()]
    for policy in policies:
        TenaciousTransport.create(policy)
        AsyncTenaciousTransport.create(policy)
    TenaciousTransport(
        retry=CustomPolicy().create(
            tenacity.Retrying,
            request_error=httpx2.RequestError,
            logger=logging.getLogger(__name__),
        ),
        transport=CustomTransport(),
    )


def use_context_managers() -> None:
    """Use the transports as context managers."""
    with TenaciousTransport.create() as transport:
        transport.handle_request(httpx2.Request("GET", "http://localhost"))
    with httpx2.Client(transport=TenaciousTransport.create()) as client:
        client.get("http://localhost")


async def use_async_context_managers() -> None:
    """Use the asynchronous transports as asynchronous context managers."""
    async with AsyncTenaciousTransport.create() as transport:
        await transport.handle_async_request(httpx2.Request("GET", "http://localhost"))
    async with httpx2.AsyncClient(transport=AsyncTenaciousTransport.create()) as client:
        await client.get("http://localhost")


def mount_transports() -> None:
    """Mount the transports for URL patterns."""
    httpx2.Client(mounts={"https://": TenaciousTransport.create()})
    httpx2.AsyncClient(mounts={"https://": AsyncTenaciousTransport.create()})
