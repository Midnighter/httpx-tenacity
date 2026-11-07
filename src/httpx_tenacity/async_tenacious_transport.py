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
from typing import TYPE_CHECKING, Unpack

import httpx
import tenacity

from httpx_tenacity.retry_policy import RetryPolicy, SmartRetryPolicy


if TYPE_CHECKING:  # pragma: no cover
    from .types import HTTPXHTTPTransportKeywordArguments

logger = logging.getLogger(__name__)


class AsyncTenaciousTransport(httpx.AsyncBaseTransport):
    """
    Define the asynchronous tenacious (retrying) transport.

    This transport consists of a composed transport for handling requests and an
    appropriately configured tenacity retrying instance.

    """

    def __init__(
        self,
        *,
        retry: tenacity.AsyncRetrying,
        transport: httpx.AsyncBaseTransport,
        **kwargs: dict[str, object],
    ) -> None:
        super().__init__(**kwargs)
        self._retry = retry
        self._transport = transport

    @classmethod
    def create(
        cls,
        policy: RetryPolicy | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        **kwargs: Unpack[HTTPXHTTPTransportKeywordArguments],
    ) -> AsyncTenaciousTransport:
        """
        Create an instance of an asynchronous tenacious (retrying) transport.

        This factory method constructs the instance with an underlying
        `httpx.AsyncHTTPTransport`.
        That transport is passed any additional keyword arguments.

        The retry policy creates the tenacity retrying instance. The default
        `SmartRetryPolicy` retries requests when there are server-side issues
        and will either wait the time set in a Retry-After response header or use a
        random exponential backoff.

        Args:
            policy: The retry policy. Defaults to `SmartRetryPolicy()`.
            transport: Pass an asynchronous transport instance to handle requests
                instead of the default one.
            **kwargs: Additional keyword arguments are used in the construction of an
                `httpx.AsyncHTTPTransport`.

        Returns:
            A default instance of the class created from the given arguments.

        """
        if policy is None:
            policy = SmartRetryPolicy()
        return cls(
            retry=policy.create(
                tenacity.AsyncRetrying,
                request_error=httpx.RequestError,
                logger=logger,
            ),
            transport=httpx.AsyncHTTPTransport(**kwargs)
            if transport is None
            else transport,
        )

    async def handle_async_request(
        self,
        request: httpx.Request,
    ) -> httpx.Response:
        """Handle an asynchronous request with retrying."""
        fresh_retry = self._retry.copy()
        async for attempt in fresh_retry:
            with attempt:
                response = await self._transport.handle_async_request(request)
            if attempt.retry_state.outcome and not attempt.retry_state.outcome.failed:
                attempt.retry_state.set_result(response)
        return response
