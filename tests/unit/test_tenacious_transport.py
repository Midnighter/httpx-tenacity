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

from types import TracebackType
from typing import Self

import httpx
import pytest
import tenacity

from httpx_tenacity.httpx.tenacious_transport import TenaciousTransport


class RecordingTransport(httpx.BaseTransport):
    """Record the lifecycle calls and requests that the transport receives."""

    def __init__(self) -> None:
        self.calls: list[object] = []

    def __enter__(self) -> Self:
        """Record entering the transport."""
        self.calls.append("enter")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        """Record exiting the transport with exception details."""
        self.calls.append(("exit", exc_type, exc_value, traceback))

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Record the request and return a successful response."""
        self.calls.append(("request", request.url.path))
        return httpx.Response(200, request=request)

    def close(self) -> None:
        """Record closing the transport."""
        self.calls.append("close")


def make_transport() -> tuple[TenaciousTransport, RecordingTransport]:
    """Create a tenacious transport that wraps a recording transport."""
    inner = RecordingTransport()
    return TenaciousTransport(retry=tenacity.Retrying(), transport=inner), inner


def test_init():
    """Test that a synchronous tenacious transport can be initialized."""
    result = TenaciousTransport(
        retry=tenacity.Retrying(),
        transport=httpx.HTTPTransport(),
    )

    assert isinstance(result, TenaciousTransport)


def test_create():
    """Test that a synchronous tenacious transport can be created."""
    result = TenaciousTransport.create()

    assert isinstance(result, TenaciousTransport)


def test_context_manager_enters_and_exits_inner_transport():
    """Test that the context manager returns the wrapper and drives the inner one."""
    transport, inner = make_transport()

    with transport as entered:
        assert entered is transport
        assert inner.calls == ["enter"]

    assert inner.calls == ["enter", ("exit", None, None, None)]


def test_context_manager_passes_exception_details_to_inner_transport():
    """Test that exception details reach the inner transport's exit."""
    transport, inner = make_transport()
    error = ValueError("boom")

    with pytest.raises(ValueError, match="boom"), transport:
        raise error

    assert inner.calls[0] == "enter"
    name, exc_type, exc_value, traceback = inner.calls[1]
    assert name == "exit"
    assert exc_type is ValueError
    assert exc_value is error
    assert traceback is error.__traceback__


def test_close_closes_inner_transport():
    """Test that closing the wrapper closes the inner transport."""
    transport, inner = make_transport()

    transport.close()

    assert inner.calls == ["close"]


def test_client_lifecycle_reaches_inner_transport():
    """Test that a client enters the inner transport, sends the request, and exits."""
    transport, inner = make_transport()

    with httpx.Client(transport=transport) as client:
        response = client.get("https://example.com/path")

    assert response.status_code == 200
    assert inner.calls == [
        "enter",
        ("request", "/path"),
        ("exit", None, None, None),
    ]
