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
import tenacity

from httpx_tenacity import AsyncTenaciousTransport


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
