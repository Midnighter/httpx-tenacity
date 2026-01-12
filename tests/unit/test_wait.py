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


"""Test the expected functionality of the custom wait strategies."""

import httpx
import tenacity

from httpx_tenacity.wait import smart_wait


def test_smart_wait_with_retry_after_header():
    """Test that the smart wait strategy returns the value from the response header."""
    state = tenacity.RetryCallState(
        tenacity.Retrying(),
        fn=None,
        args=None,
        kwargs=None,
    )
    state.set_result(
        httpx.Response(
            status_code=httpx.codes.TOO_MANY_REQUESTS,
            headers={"Retry-After": "104"},
        ),
    )
    strategy = smart_wait()

    assert strategy(state) == 104.0


def test_smart_wait_without_retry_after_header():
    """Test that the smart wait strategy returns a random exponential value."""
    state = tenacity.RetryCallState(
        tenacity.Retrying(),
        fn=None,
        args=None,
        kwargs=None,
    )
    state.set_result(httpx.Response(status_code=httpx.codes.OK))
    strategy = smart_wait(min=0, max=60)
    result = [strategy(state) for _ in range(100)]

    assert min(result) >= 0
    assert max(result) <= 60
