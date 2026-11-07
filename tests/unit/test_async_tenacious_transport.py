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

import httpx
import pytest
import tenacity

from httpx_tenacity import AsyncTenaciousTransport


class RecordingTransport(httpx.AsyncBaseTransport):
    """Record the lifecycle calls that the transport receives."""

    def __init__(self) -> None:
        self.calls: list[object] = []

    async def aclose(self) -> None:
        """Record closing the transport."""
        self.calls.append("aclose")


def make_transport() -> tuple[AsyncTenaciousTransport, RecordingTransport]:
    """Create a tenacious transport that wraps a recording transport."""
    inner = RecordingTransport()
    return AsyncTenaciousTransport(
        retry=tenacity.AsyncRetrying(),
        transport=inner,
    ), inner


def test_init():
    """Test that an asynchronous tenacious transport can be initialized."""
    result = AsyncTenaciousTransport(
        retry=tenacity.AsyncRetrying(),
        transport=httpx.AsyncHTTPTransport(),
    )

    assert isinstance(result, AsyncTenaciousTransport)


def test_create():
    """Test that an asynchronous rate-limited transport can be created."""
    result = AsyncTenaciousTransport.create()

    assert isinstance(result, AsyncTenaciousTransport)


@pytest.mark.anyio
async def test_aclose_closes_inner_transport():
    """Test that closing the wrapper closes the inner transport."""
    transport, inner = make_transport()

    await transport.aclose()

    assert inner.calls == ["aclose"]
