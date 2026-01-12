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
import sys
from typing import TYPE_CHECKING


if sys.version_info < (3, 11):
    from typing_extensions import Unpack
else:
    from typing import Unpack

import httpx
import tenacity

from httpx_tenacity.retry_callback import is_server_side_issue
from httpx_tenacity.wait import smart_wait


if TYPE_CHECKING:  # pragma: no cover
    from datetime import timedelta

    from .types import HTTPXAsyncHTTPTransportKeywordArguments


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
        max_attempts: int = 5,
        multiplier: float = 1,
        max_wait_seconds: float | timedelta = 60,
        min_wait_seconds: float | timedelta = 0.02,
        exponent_base: float = 2,
        **kwargs: Unpack[HTTPXAsyncHTTPTransportKeywordArguments],
    ) -> AsyncTenaciousTransport:
        """
        Create an instance of an asynchronous tenacious (retrying) transport.

        This factory method constructs the instance with an underlying
        `httpx.AsyncHTTPTransport`.
        That transport is passed any additional keyword arguments.

        The constructed transport retries requests when there are server-side issues
        and will either wait the time set in a Retry-After response header or use a
        random exponential backoff.

        Args:
            max_attempts: Maximum number of attempts.
            multiplier: Multiplier for the exponential backoff between retries.
            max_wait_seconds: Maximum wait time between retries.
            min_wait_seconds: Minimum wait time between retries.
            exponent_base: The base for the exponential backoff.
            **kwargs: Additional keyword arguments are used in the construction of an
                `httpx.AsyncHTTPTransport`.

        Returns:
            A default instance of the class created from the given arguments.

        """
        return cls(
            retry=tenacity.AsyncRetrying(
                retry=tenacity.retry_if_result(is_server_side_issue),
                stop=tenacity.stop_after_attempt(max_attempts),
                wait=smart_wait(
                    multiplier=multiplier,
                    max=max_wait_seconds,
                    min=min_wait_seconds,
                    exp_base=exponent_base,
                ),
                before_sleep=tenacity.before_sleep_log(logger, logging.DEBUG),
                reraise=True,
            ),
            transport=httpx.AsyncHTTPTransport(**kwargs),
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
