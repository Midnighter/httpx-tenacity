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
import tenacity

from httpx_tenacity.tenacious_transport import TenaciousTransport


class RecordingTransport(httpx.BaseTransport):
    """Record the lifecycle calls that the transport receives."""

    def __init__(self) -> None:
        self.calls: list[object] = []

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


def test_close_closes_inner_transport():
    """Test that closing the wrapper closes the inner transport."""
    transport, inner = make_transport()

    transport.close()

    assert inner.calls == ["close"]
