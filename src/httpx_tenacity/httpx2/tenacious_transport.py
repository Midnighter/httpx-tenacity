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


"""Provide a synchronous tenacious (retrying) transport."""

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


class TenaciousTransport(httpx2.BaseTransport):
    """
    Define the synchronous tenacious (retrying) transport.

    This transport consists of a composed transport for handling requests and an
    appropriately configured tenacity retrying instance.

    The transport owns the composed transport, including one that you pass in
    yourself. Entering, exiting, or closing this transport does the same to the
    composed transport, in the same way that `httpx2.Client` treats its transport.

    """

    def __init__(
        self,
        *,
        retry: tenacity.Retrying,
        transport: httpx2.BaseTransport,
        **kwargs: dict[str, object],
    ) -> None:
        super().__init__(**kwargs)
        self._retry = retry
        self._transport = transport

    @classmethod
    def create(
        cls,
        policy: RetryPolicy | None = None,
        transport: httpx2.BaseTransport | None = None,
        **kwargs: Unpack[HTTPX2HTTPTransportKeywordArguments],
    ) -> TenaciousTransport:
        """
        Create an instance of a synchronous tenacious (retrying) transport.

        This factory method constructs the instance with an underlying
        `httpx2.HTTPTransport`.
        That transport is passed any additional keyword arguments.

        The retry policy creates the tenacity retrying instance. The default
        `SmartRetryPolicy` retries requests when there are server-side issues
        and will either wait the time set in a Retry-After response header or use a
        random exponential backoff.

        The returned transport owns the underlying transport, including one passed in
        as `transport`, and closes it when it is closed.

        Args:
            policy: The retry policy. Defaults to `SmartRetryPolicy()`.
            transport: Pass a transport instance to handle requests instead of the
                default one.
            **kwargs: Additional keyword arguments are used in the construction of an
                `httpx2.HTTPTransport`.

        Returns:
            A default instance of the class created from the given arguments.

        """
        if policy is None:
            policy = SmartRetryPolicy()
        return cls(
            retry=policy.create(
                tenacity.Retrying,
                request_error=httpx2.RequestError,
                logger=logger,
            ),
            transport=httpx2.HTTPTransport(**kwargs)
            if transport is None
            else transport,
        )

    def handle_request(
        self,
        request: httpx2.Request,
    ) -> httpx2.Response:
        """Handle a synchronous request with retrying."""
        fresh_retry = self._retry.copy()
        for attempt in fresh_retry:
            with attempt:
                response = self._transport.handle_request(request)
            if attempt.retry_state.outcome and not attempt.retry_state.outcome.failed:
                attempt.retry_state.set_result(response)
        return response  # pyrefly: ignore[unbound-name]

    def __enter__(self) -> Self:
        """Enter the composed transport and return this transport."""
        self._transport.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        """Exit the composed transport, passing on any exception details."""
        self._transport.__exit__(exc_type, exc_value, traceback)

    def close(self) -> None:
        """Close the composed transport."""
        self._transport.close()
