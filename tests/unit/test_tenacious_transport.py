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

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import pytest
import tenacity


if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

    from httpx_tenacity_test_types import (
        BaseTransport,
        HTTPBackend,
        Request,
        Response,
        TenaciousTransport,
    )


def make_recording_transport(http: HTTPBackend, calls: list[object]) -> BaseTransport:
    """
    Create a transport of the selected backend that records into the given list.

    The transport records the lifecycle calls and the requests that it receives.

    """

    class RecordingTransport(http.client.BaseTransport):
        """Record the lifecycle calls and requests that the transport receives."""

        def __enter__(self) -> Self:
            """Record entering the transport."""
            calls.append("enter")
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None = None,
            exc_value: BaseException | None = None,
            traceback: TracebackType | None = None,
        ) -> None:
            """Record exiting the transport with exception details."""
            calls.append(("exit", exc_type, exc_value, traceback))

        def handle_request(self, request: Request) -> Response:
            """Record the request and return a successful response."""
            calls.append(("request", request.url.path))
            return http.client.Response(200, request=request)

        def close(self) -> None:
            """Record closing the transport."""
            calls.append("close")

    return RecordingTransport()


def make_transport(http: HTTPBackend) -> tuple[TenaciousTransport, list[object]]:
    """Create a tenacious transport that wraps a recording transport."""
    calls: list[object] = []
    transport = http.integration.TenaciousTransport(
        retry=tenacity.Retrying(),
        transport=make_recording_transport(http, calls),
    )
    return transport, calls


def test_init(http: HTTPBackend):
    """Test that a synchronous tenacious transport can be initialized."""
    inner = http.client.HTTPTransport()

    result = http.integration.TenaciousTransport(
        retry=tenacity.Retrying(),
        transport=inner,
    )

    assert isinstance(result, http.integration.TenaciousTransport)
    assert isinstance(result, http.client.BaseTransport)
    result.close()


def test_create(http: HTTPBackend):
    """Test that a synchronous tenacious transport can be created."""
    result = http.integration.TenaciousTransport.create()

    assert isinstance(result, http.integration.TenaciousTransport)
    assert isinstance(result, http.client.BaseTransport)
    result.close()


def test_context_manager_enters_and_exits_inner_transport(http: HTTPBackend):
    """Test that the context manager returns the wrapper and drives the inner one."""
    transport, calls = make_transport(http)

    with transport as entered:
        assert entered is transport
        assert calls == ["enter"]

    assert calls == ["enter", ("exit", None, None, None)]


def test_context_manager_passes_exception_details_to_inner_transport(
    http: HTTPBackend,
):
    """Test that exception details reach the inner transport's exit."""
    transport, calls = make_transport(http)
    error = ValueError("boom")

    with pytest.raises(ValueError, match="boom"), transport:
        raise error

    assert calls[0] == "enter"
    name, exc_type, exc_value, traceback = calls[1]
    assert name == "exit"
    assert exc_type is ValueError
    assert exc_value is error
    assert traceback is error.__traceback__


def test_close_closes_inner_transport(http: HTTPBackend):
    """Test that closing the wrapper closes the inner transport."""
    transport, calls = make_transport(http)

    transport.close()

    assert calls == ["close"]


def test_client_lifecycle_reaches_inner_transport(http: HTTPBackend):
    """Test that a client enters the inner transport, sends the request, and exits."""
    transport, calls = make_transport(http)

    with http.client.Client(transport=transport) as client:
        response = client.get("https://example.com/path")

    assert isinstance(response, http.client.Response)
    assert response.status_code == 200
    assert calls == [
        "enter",
        ("request", "/path"),
        ("exit", None, None, None),
    ]
