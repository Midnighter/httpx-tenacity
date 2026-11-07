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

import logging

import httpx
import pytest
import tenacity

from httpx_tenacity import (
    AsyncTenaciousTransport,
    RetryingT,
    SmartRetryPolicy,
    TenaciousTransport,
)


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


def fail_to_connect(request: httpx.Request) -> httpx.Response:
    """Raise a connection error for every request."""
    raise httpx.ConnectError("Network exploded!", request=request)  # noqa: EM101, TRY003


def test_sync_transport_uses_custom_policy():
    """Test that the sync transport creates its retrying from a custom policy."""
    policy = RecordingRetryPolicy()
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return fail_to_connect(request)

    transport = TenaciousTransport.create(
        policy=policy,
        transport=httpx.MockTransport(handler=handler),
    )
    with httpx.Client(transport=transport) as client, pytest.raises(httpx.ConnectError):
        client.get("http://example.com")

    assert policy.calls == [
        (
            tenacity.Retrying,
            httpx.RequestError,
            logging.getLogger("httpx_tenacity.httpx.tenacious_transport"),
        ),
    ]
    assert len(requests) == 2


@pytest.mark.anyio
async def test_async_transport_uses_custom_policy():
    """Test that the async transport creates its retrying from a custom policy."""
    policy = RecordingRetryPolicy()
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return fail_to_connect(request)

    transport = AsyncTenaciousTransport.create(
        policy=policy,
        transport=httpx.MockTransport(handler=handler),
    )
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(httpx.ConnectError):
            await client.get("http://example.com")

    assert policy.calls == [
        (
            tenacity.AsyncRetrying,
            httpx.RequestError,
            logging.getLogger("httpx_tenacity.httpx.async_tenacious_transport"),
        ),
    ]
    assert len(requests) == 2


def test_create_waits_for_custom_status_code_and_header():
    """Test that the policy's status code and header determine the wait time."""
    retrying = SmartRetryPolicy(
        status_code=httpx.codes.SERVICE_UNAVAILABLE,
        header="X-Wait",
    ).create(tenacity.Retrying, request_error=httpx.RequestError, logger=logger)
    state = tenacity.RetryCallState(retrying, fn=None, args=None, kwargs=None)
    state.set_result(
        httpx.Response(
            status_code=httpx.codes.SERVICE_UNAVAILABLE,
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
    with pytest.raises(httpx.ConnectError):
        retrying(fail, httpx.ConnectError("Network exploded!"))
    assert len(attempts) == 1
