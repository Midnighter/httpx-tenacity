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


"""Provide an asynchronous tenacious (retrying) transport."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self, Unpack

import httpx2
import tenacity

from httpx_tenacity.retry_policy import RetryPolicy, SmartRetryPolicy


if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

    from .types import HTTPX2HTTPTransportKeywordArguments

logger = logging.getLogger(__name__)


class AsyncTenaciousTransport(httpx2.AsyncBaseTransport):
    """
    Define the asynchronous tenacious (retrying) transport.

    This transport consists of a composed transport for handling requests and an
    appropriately configured tenacity retrying instance.

    The transport owns the composed transport, including one that you pass in
    yourself. Entering, exiting, or closing this transport does the same to the
    composed transport, in the same way that `httpx2.AsyncClient` treats its transport.

    """

    def __init__(
        self,
        *,
        retry: tenacity.AsyncRetrying,
        transport: httpx2.AsyncBaseTransport,
        **kwargs: dict[str, object],
    ) -> None:
        super().__init__(**kwargs)
        self._retry = retry
        self._transport = transport

    @classmethod
    def create(
        cls,
        policy: RetryPolicy | None = None,
        transport: httpx2.AsyncBaseTransport | None = None,
        **kwargs: Unpack[HTTPX2HTTPTransportKeywordArguments],
    ) -> AsyncTenaciousTransport:
        """
        Create an instance of an asynchronous tenacious (retrying) transport.

        This factory method constructs the instance with an underlying
        `httpx2.AsyncHTTPTransport`.
        That transport is passed any additional keyword arguments.

        The retry policy creates the tenacity retrying instance. The default
        `SmartRetryPolicy` retries requests when there are server-side issues
        and will either wait the time set in a Retry-After response header or use a
        random exponential backoff.

        The returned transport owns the underlying transport, including one passed in
        as `transport`, and closes it when it is closed.

        Args:
            policy: The retry policy. Defaults to `SmartRetryPolicy()`.
            transport: Pass an asynchronous transport instance to handle requests
                instead of the default one.
            **kwargs: Additional keyword arguments are used in the construction of an
                `httpx2.AsyncHTTPTransport`.

        Returns:
            A default instance of the class created from the given arguments.

        """
        if policy is None:
            policy = SmartRetryPolicy()
        return cls(
            retry=policy.create(
                tenacity.AsyncRetrying,
                request_error=httpx2.RequestError,
                logger=logger,
            ),
            transport=httpx2.AsyncHTTPTransport(**kwargs)
            if transport is None
            else transport,
        )

    async def handle_async_request(
        self,
        request: httpx2.Request,
    ) -> httpx2.Response:
        """Handle an asynchronous request with retrying."""
        fresh_retry = self._retry.copy()
        async for attempt in fresh_retry:
            with attempt:
                response = await self._transport.handle_async_request(request)
            if attempt.retry_state.outcome and not attempt.retry_state.outcome.failed:
                attempt.retry_state.set_result(response)
        return response  # pyrefly: ignore[unbound-name]

    async def __aenter__(self) -> Self:
        """Enter the composed transport and return this transport."""
        await self._transport.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        """Exit the composed transport, passing on any exception details."""
        await self._transport.__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        """Close the composed transport."""
        await self._transport.aclose()
