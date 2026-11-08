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


"""Test that both HTTP integrations work together in the same process."""

from __future__ import annotations

from http import HTTPStatus

import httpx
import httpx2
import pytest

import httpx_tenacity.httpx
import httpx_tenacity.httpx2
from httpx_tenacity import SmartRetryPolicy


@pytest.mark.anyio
async def test_both_integrations_share_a_policy():
    """Test that one policy retries the requests of an HTTPX and an HTTPX2 client."""
    policy = SmartRetryPolicy(max_attempts=3, max_wait_seconds=1e-3)
    httpx_requests = []
    httpx2_requests = []

    def httpx_handler(request: httpx.Request) -> httpx.Response:
        httpx_requests.append(request)
        if len(httpx_requests) < 2:
            return httpx.Response(HTTPStatus.SERVICE_UNAVAILABLE, request=request)
        return httpx.Response(HTTPStatus.OK, text="from httpx", request=request)

    def httpx2_handler(request: httpx2.Request) -> httpx2.Response:
        httpx2_requests.append(request)
        if len(httpx2_requests) < 3:
            return httpx2.Response(HTTPStatus.BAD_GATEWAY, request=request)
        return httpx2.Response(HTTPStatus.CREATED, text="from httpx2", request=request)

    httpx_transport = httpx_tenacity.httpx.AsyncTenaciousTransport.create(
        policy=policy,
        transport=httpx.MockTransport(httpx_handler),
    )
    httpx2_transport = httpx_tenacity.httpx2.AsyncTenaciousTransport.create(
        policy=policy,
        transport=httpx2.MockTransport(httpx2_handler),
    )
    async with (
        httpx.AsyncClient(transport=httpx_transport) as httpx_client,
        httpx2.AsyncClient(transport=httpx2_transport) as httpx2_client,
    ):
        httpx_response = await httpx_client.get("http://example.com")
        httpx2_response = await httpx2_client.get("http://example.com")

    assert isinstance(httpx_response, httpx.Response)
    assert (httpx_response.status_code, httpx_response.text) == (200, "from httpx")
    assert len(httpx_requests) == 2
    assert isinstance(httpx2_response, httpx2.Response)
    assert (httpx2_response.status_code, httpx2_response.text) == (201, "from httpx2")
    assert len(httpx2_requests) == 3
