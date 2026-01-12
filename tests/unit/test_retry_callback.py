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


"""Test the expected functionality of the custom retry callback functions."""

import httpx
import pytest

from httpx_tenacity.retry_callback import is_server_side_issue


@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        *[(code, False) for code in range(100, 400)],
        *[
            (code, False)
            for code in range(400, 500)
            if code != httpx.codes.TOO_MANY_REQUESTS
        ],
        (httpx.codes.TOO_MANY_REQUESTS, True),
        *[(code, True) for code in range(500, 600)],
    ],
)
def test_is_server_side_issue(status_code: int, expected: bool):
    """Test that the callback returns true for server side issues."""
    assert is_server_side_issue(httpx.Response(status_code=status_code)) is expected
