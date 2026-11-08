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


"""Test the expected functionality of the asynchronous tenacious transport."""

from __future__ import annotations

from collections import Counter, deque
from http import HTTPStatus
from typing import TYPE_CHECKING

import anyio
import pytest

from httpx_tenacity import SmartRetryPolicy


if TYPE_CHECKING:  # pragma: no cover
    from httpx_tenacity_test_types import (
        AsyncBaseTransport,
        AsyncClient,
        HTTPBackend,
        Request,
        Response,
    )

RETRY_LATER = (HTTPStatus.TOO_MANY_REQUESTS, {"Retry-After": "0.001"})
OK = (HTTPStatus.OK, {})
SERVER_ERRORS = [
    (code, {})
    for code in (
        HTTPStatus.INTERNAL_SERVER_ERROR,
        HTTPStatus.NOT_IMPLEMENTED,
        HTTPStatus.BAD_GATEWAY,
        HTTPStatus.SERVICE_UNAVAILABLE,
        HTTPStatus.GATEWAY_TIMEOUT,
        HTTPStatus.HTTP_VERSION_NOT_SUPPORTED,
        HTTPStatus.VARIANT_ALSO_NEGOTIATES,
        HTTPStatus.INSUFFICIENT_STORAGE,
        HTTPStatus.LOOP_DETECTED,
        HTTPStatus.NOT_EXTENDED,
        HTTPStatus.NETWORK_AUTHENTICATION_REQUIRED,
    )
]


def make_mock_transport(
    http: HTTPBackend,
    queues: dict[str, list[tuple[int, dict[str, str]]]],
) -> tuple[AsyncBaseTransport, list[Request]]:
    """
    Create a mock transport of the selected backend that answers from queues.

    Each request is answered with the next queued response of its URL. A request that
    has no queued response left fails the test.

    Args:
        http: The selected HTTP backend.
        queues: The status codes and headers of the responses to return per URL.

    Returns:
        The mock transport and the list that records every request that it received.

    """
    pending = {url: deque(queue) for url, queue in queues.items()}
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        queue = pending.get(str(request.url))
        assert queue, f"Unexpected request to {request.url}"
        status_code, headers = queue.popleft()
        return http.client.Response(status_code, headers=headers, request=request)

    return http.client.MockTransport(handler=handler), requests


@pytest.mark.anyio
async def test_request_error_retrying(http: HTTPBackend):
    """Test that a request error is retried."""
    requests = []

    def handler(request: Request) -> Response:
        requests.append(request)
        raise http.client.RequestError("Network exploded!", request=request)  # noqa: EM101, TRY003

    retry_transport = http.integration.AsyncTenaciousTransport.create(
        policy=SmartRetryPolicy(max_attempts=3, max_wait_seconds=1e-3),
        transport=http.client.MockTransport(handler=handler),
    )
    async with http.client.AsyncClient(transport=retry_transport) as client:
        with pytest.raises(http.client.RequestError):
            await client.get("http://example.com")

    assert len(requests) == 3


@pytest.mark.anyio
async def test_too_many_requests_retrying(http: HTTPBackend):
    """
    Test that a too many requests response is retried.

    Additionally, we ensure that more than one request can be retried concurrently.

    """
    transport, requests = make_mock_transport(
        http,
        {
            "http://example1.com": [RETRY_LATER, RETRY_LATER, OK],
            "http://example2.com": [RETRY_LATER, RETRY_LATER, OK],
        },
    )
    responses = {}

    async def get(client: AsyncClient, url: str) -> None:
        responses[url] = await client.get(url)

    async with (
        http.client.AsyncClient(
            transport=http.integration.AsyncTenaciousTransport.create(
                policy=SmartRetryPolicy(max_attempts=3),
                transport=transport,
            ),
        ) as client,
        anyio.create_task_group() as tg,
    ):
        tg.start_soon(get, client, "http://example1.com")
        tg.start_soon(get, client, "http://example2.com")

    assert all(
        isinstance(response, http.client.Response)
        and response.status_code == HTTPStatus.OK
        for response in responses.values()
    )
    assert Counter(str(request.url) for request in requests) == {
        "http://example1.com": 3,
        "http://example2.com": 3,
    }


@pytest.mark.anyio
async def test_server_error_retrying(http: HTTPBackend):
    """Test that server error responses are retried."""
    transport, requests = make_mock_transport(
        http,
        {"http://example1.com": [*SERVER_ERRORS, OK]},
    )

    async with http.client.AsyncClient(
        transport=http.integration.AsyncTenaciousTransport.create(
            policy=SmartRetryPolicy(max_attempts=12, max_wait_seconds=1e-3),
            transport=transport,
        ),
    ) as client:
        response = await client.get("http://example1.com")

    assert isinstance(response, http.client.Response)
    assert response.status_code == HTTPStatus.OK
    assert len(requests) == len(SERVER_ERRORS) + 1
