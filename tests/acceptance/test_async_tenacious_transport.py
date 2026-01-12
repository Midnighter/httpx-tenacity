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

import anyio
import httpx
import pytest
import tenacity
from pytest_httpx import HTTPXMock

from httpx_tenacity import AsyncTenaciousTransport
from httpx_tenacity.retry_callback import is_server_side_issue


@pytest.mark.anyio
async def test_too_many_requests_retrying(
    httpx_mock: HTTPXMock,
):
    """
    Test that a too many requests response is retried.

    Additionally, we ensure that more than one request can be retried concurrently.

    """
    after_seconds = 1e-3

    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.TOO_MANY_REQUESTS,
        headers={"Retry-After": str(after_seconds)},
    )
    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.TOO_MANY_REQUESTS,
        headers={"Retry-After": str(after_seconds)},
    )
    httpx_mock.add_response(url="http://example1.com", status_code=httpx.codes.OK)

    httpx_mock.add_response(
        url="http://example2.com",
        status_code=httpx.codes.TOO_MANY_REQUESTS,
        headers={"Retry-After": str(after_seconds)},
    )
    httpx_mock.add_response(
        url="http://example2.com",
        status_code=httpx.codes.TOO_MANY_REQUESTS,
        headers={"Retry-After": str(after_seconds)},
    )
    httpx_mock.add_response(url="http://example2.com", status_code=httpx.codes.OK)

    async with (
        httpx.AsyncClient(
            transport=AsyncTenaciousTransport.create(max_attempts=3),
        ) as client,
        anyio.create_task_group() as tg,
    ):
        tg.start_soon(client.get, "http://example1.com")
        tg.start_soon(client.get, "http://example2.com")


@pytest.mark.anyio
async def test_server_error_retrying(
    httpx_mock: HTTPXMock,
):
    """Test that server error responses are retried."""
    after_seconds = 1e-3

    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.INTERNAL_SERVER_ERROR,
    )
    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.NOT_IMPLEMENTED,
    )
    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.BAD_GATEWAY,
    )
    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.SERVICE_UNAVAILABLE,
    )
    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.GATEWAY_TIMEOUT,
    )
    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.HTTP_VERSION_NOT_SUPPORTED,
    )
    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.VARIANT_ALSO_NEGOTIATES,
    )
    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.INSUFFICIENT_STORAGE,
    )
    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.LOOP_DETECTED,
    )
    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.NOT_EXTENDED,
    )
    httpx_mock.add_response(
        url="http://example1.com",
        status_code=httpx.codes.NETWORK_AUTHENTICATION_REQUIRED,
    )
    httpx_mock.add_response(url="http://example1.com", status_code=httpx.codes.OK)

    async with (
        httpx.AsyncClient(
            transport=AsyncTenaciousTransport(
                retry=tenacity.AsyncRetrying(
                    retry=tenacity.retry_if_result(is_server_side_issue),
                    stop=tenacity.stop_after_attempt(12),
                    wait=tenacity.wait_fixed(after_seconds),
                    reraise=True,
                ),
                transport=httpx.AsyncHTTPTransport(),
            ),
        ) as client,
        anyio.create_task_group() as tg,
    ):
        tg.start_soon(client.get, "http://example1.com")
