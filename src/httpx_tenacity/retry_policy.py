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


"""Provide retry policies that create the transports' tenacity retrying instances."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, NamedTuple, Protocol, TypeVar

import tenacity

from httpx_tenacity.retry_callback import is_server_side_issue
from httpx_tenacity.wait import smart_wait


if TYPE_CHECKING:  # pragma: no cover
    from datetime import timedelta


RetryingT = TypeVar("RetryingT", tenacity.Retrying, tenacity.AsyncRetrying)
"""The sync or async tenacity retrying class that a retry policy creates."""


class RetryPolicy(Protocol):
    """
    Define the interface of a retry policy.

    A tenacious transport's `create()` factory calls the policy's `create()` method
    with the tenacity retrying class it needs, its HTTP client's base exception for
    failed requests, and its logger.

    """

    def create(
        self,
        retrying_class: type[RetryingT],
        *,
        request_error: type[Exception],
        logger: logging.Logger,
    ) -> RetryingT:
        """
        Create a retrying instance for a transport.

        Args:
            retrying_class: Either `tenacity.Retrying` or `tenacity.AsyncRetrying`.
            request_error: The HTTP client's base exception for failed requests, such
                as `httpx.RequestError`.
            logger: The transport's logger.

        Returns:
            An instance of the given retrying class.

        """


class SmartRetryPolicy(NamedTuple):
    """
    Define the default retry policy.

    The policy retries request errors and server-side issues. Between attempts, it
    waits for the time given in a response header when the response has one of the
    expected status codes, and otherwise uses random exponential backoff.

    Attributes:
        max_attempts: Maximum number of attempts.
        multiplier: Multiplier for the exponential backoff between retries.
        max_wait_seconds: Maximum wait time between retries.
        min_wait_seconds: Minimum wait time between retries.
        exponent_base: The base for the exponential backoff.
        status_code: The response status code or codes whose header sets the wait.
        header: The response header that holds the wait time in seconds.

    """

    max_attempts: int = 5
    multiplier: float = 1
    max_wait_seconds: float | timedelta = 60
    min_wait_seconds: float | timedelta = 0.02
    exponent_base: float = 2
    status_code: int | tuple[int, ...] = HTTPStatus.TOO_MANY_REQUESTS
    header: str = "Retry-After"

    def create(
        self,
        retrying_class: type[RetryingT],
        *,
        request_error: type[Exception],
        logger: logging.Logger,
    ) -> RetryingT:
        """
        Create a retrying instance with this policy.

        Args:
            retrying_class: Either `tenacity.Retrying` or `tenacity.AsyncRetrying`.
            request_error: The HTTP client's base exception for failed requests, such
                as `httpx.RequestError`.
            logger: The logger that records each retry at DEBUG level.

        Returns:
            An instance of the given retrying class.

        """
        return retrying_class(
            retry=tenacity.retry_if_exception_type(request_error)
            | tenacity.retry_if_result(is_server_side_issue),
            stop=tenacity.stop_after_attempt(self.max_attempts),
            wait=smart_wait(
                multiplier=self.multiplier,
                max=self.max_wait_seconds,
                min=self.min_wait_seconds,
                exp_base=self.exponent_base,
                status_code=self.status_code,
                header=self.header,
            ),
            before_sleep=tenacity.before_sleep_log(logger, logging.DEBUG),  # type: ignore[invalid-argument-type]
            reraise=True,
        )
