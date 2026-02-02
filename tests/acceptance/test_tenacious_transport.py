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


"""Test the expected functionality of the synchronous tenacious transport."""

import httpx
from pytest_httpx import HTTPXMock

from httpx_tenacity.tenacious_transport import TenaciousTransport


def test_request_error_retrying():
    """Test that a request error is retried."""

    class FailingHTTPTransport(httpx.BaseTransport):
        """Define an HTTP transport that always raises a request exception."""

        def __init__(self) -> None:
            super().__init__()
            self.counter = 0

        def handle_request(self, request: httpx.Request) -> httpx.Response:
            """Raise a request exception upon handling any request."""
            self.counter += 1

            raise httpx.RequestError("Network exploded!", request=request)  # noqa: EM101, TRY003

    http_transport = FailingHTTPTransport()
    retry_transport = TenaciousTransport.create(
        max_attempts=3,
        max_wait_seconds=1e-3,
        transport=http_transport,
    )
    with httpx.Client(transport=retry_transport) as client:
        try:  # noqa: SIM105
            client.get("http://example.com")
        except httpx.RequestError:
            pass

    assert http_transport.counter == 3


def test_too_many_requests_retrying(
    httpx_mock: HTTPXMock,
):
    """Test that a too many requests response is retried."""
    after_seconds = 1e-3

    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.TOO_MANY_REQUESTS,
        headers={"Retry-After": str(after_seconds)},
    )
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.TOO_MANY_REQUESTS,
        headers={"Retry-After": str(after_seconds)},
    )
    httpx_mock.add_response(url="http://example.com", status_code=httpx.codes.OK)

    with httpx.Client(
        transport=TenaciousTransport.create(max_attempts=3),
    ) as client:
        client.get("http://example.com")


def test_server_error_retrying(
    httpx_mock: HTTPXMock,
):
    """Test that server error responses are retried."""
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.INTERNAL_SERVER_ERROR,
    )
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.NOT_IMPLEMENTED,
    )
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.BAD_GATEWAY,
    )
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.SERVICE_UNAVAILABLE,
    )
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.GATEWAY_TIMEOUT,
    )
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.HTTP_VERSION_NOT_SUPPORTED,
    )
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.VARIANT_ALSO_NEGOTIATES,
    )
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.INSUFFICIENT_STORAGE,
    )
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.LOOP_DETECTED,
    )
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.NOT_EXTENDED,
    )
    httpx_mock.add_response(
        url="http://example.com",
        status_code=httpx.codes.NETWORK_AUTHENTICATION_REQUIRED,
    )
    httpx_mock.add_response(url="http://example.com", status_code=httpx.codes.OK)

    with httpx.Client(
        transport=TenaciousTransport.create(
            max_attempts=12,
            max_wait_seconds=1e-3,
        ),
    ) as client:
        client.get("http://example.com")
