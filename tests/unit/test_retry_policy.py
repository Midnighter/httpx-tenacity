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


"""Test the expected functionality of the retry policies."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
import tenacity

from httpx_tenacity import RetryingT, SmartRetryPolicy
from httpx_tenacity_test_types import HTTPBackend


if TYPE_CHECKING:  # pragma: no cover
    from httpx_tenacity_test_types import Request, Response


logger = logging.getLogger(__name__)


class CustomRequestError(Exception):
    """Define a request error of another HTTP client."""


class RecordingRetryPolicy:
    """Define a custom retry policy that records how a transport calls it."""

    def __init__(self) -> None:
        self.calls: list[tuple[type, type[Exception], logging.Logger]] = []

    def create(
        self,
        retrying_class: type[RetryingT],
        *,
        request_error: type[Exception],
        logger: logging.Logger,
    ) -> RetryingT:
        """Record the arguments and retry request errors for two attempts."""
        self.calls.append((retrying_class, request_error, logger))
        return retrying_class(
            retry=tenacity.retry_if_exception_type(request_error),
            stop=tenacity.stop_after_attempt(2),
            reraise=True,
        )


def make_failing_transport(
    http: HTTPBackend,
    requests: list[Request],
) -> object:
    """Create a mock transport that records requests and fails to connect."""

    def handler(request: Request) -> Response:
        requests.append(request)
        raise http.client.ConnectError("Network exploded!", request=request)  # noqa: EM101, TRY003

    return http.client.MockTransport(handler=handler)


def test_sync_transport_uses_custom_policy(http: HTTPBackend):
    """Test that the sync transport creates its retrying from a custom policy."""
    policy = RecordingRetryPolicy()
    requests = []

    transport = http.integration.TenaciousTransport.create(
        policy=policy,
        transport=make_failing_transport(http, requests),
    )
    with (
        http.client.Client(transport=transport) as client,
        pytest.raises(http.client.ConnectError),
    ):
        client.get("http://example.com")

    assert policy.calls == [
        (
            tenacity.Retrying,
            http.client.RequestError,
            logging.getLogger(f"httpx_tenacity.{http.name}.tenacious_transport"),
        ),
    ]
    assert len(requests) == 2


@pytest.mark.anyio
async def test_async_transport_uses_custom_policy(http: HTTPBackend):
    """Test that the async transport creates its retrying from a custom policy."""
    policy = RecordingRetryPolicy()
    requests = []

    transport = http.integration.AsyncTenaciousTransport.create(
        policy=policy,
        transport=make_failing_transport(http, requests),
    )
    async with http.client.AsyncClient(transport=transport) as client:
        with pytest.raises(http.client.ConnectError):
            await client.get("http://example.com")

    assert policy.calls == [
        (
            tenacity.AsyncRetrying,
            http.client.RequestError,
            logging.getLogger(f"httpx_tenacity.{http.name}.async_tenacious_transport"),
        ),
    ]
    assert len(requests) == 2


def test_create_waits_for_custom_status_code_and_header(http: HTTPBackend):
    """Test that the policy's status code and header determine the wait time."""
    retrying = SmartRetryPolicy(
        status_code=http.client.codes.SERVICE_UNAVAILABLE,
        header="X-Wait",
    ).create(tenacity.Retrying, request_error=http.client.RequestError, logger=logger)
    state = tenacity.RetryCallState(retrying, fn=None, args=None, kwargs=None)
    state.set_result(
        http.client.Response(
            status_code=http.client.codes.SERVICE_UNAVAILABLE,
            headers={"X-Wait": "7", "Retry-After": "3"},
        ),
    )

    assert retrying.wait(state) == 7.0


def test_create_retries_given_request_error():
    """Test that the policy retries the given request error and no other."""
    policy = SmartRetryPolicy(max_attempts=3, max_wait_seconds=0, min_wait_seconds=0)
    retrying = policy.create(
        tenacity.Retrying,
        request_error=CustomRequestError,
        logger=logger,
    )
    attempts = []

    def fail(error: Exception) -> None:
        attempts.append(error)
        raise error

    with pytest.raises(CustomRequestError):
        retrying(fail, CustomRequestError())
    assert len(attempts) == 3

    attempts.clear()
    with pytest.raises(ValueError, match="Not a request error"):
        retrying(fail, ValueError("Not a request error"))
    assert len(attempts) == 1


def test_create_retries_only_the_request_error_of_its_own_client(http: HTTPBackend):
    """Test that a request error of one HTTP client is not one of the other client."""
    other = HTTPBackend.create("httpx2" if http.name == "httpx" else "httpx")
    policy = SmartRetryPolicy(max_attempts=3, max_wait_seconds=0, min_wait_seconds=0)
    retrying = policy.create(
        tenacity.Retrying,
        request_error=http.client.RequestError,
        logger=logger,
    )
    attempts = []

    def fail(error: Exception) -> None:
        attempts.append(error)
        raise error

    with pytest.raises(http.client.ConnectError):
        retrying(fail, http.client.ConnectError("Network exploded!"))
    assert len(attempts) == 3

    attempts.clear()
    with pytest.raises(other.client.ConnectError):
        retrying(fail, other.client.ConnectError("Network exploded!"))
    assert len(attempts) == 1
