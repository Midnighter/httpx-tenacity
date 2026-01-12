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


"""Provide custom wait functions."""

import httpx
import tenacity
from tenacity.wait import wait_random_exponential


# We follow tenacity's convention here to use lower snake-case class names for the wait
# strategies.
class smart_wait(wait_random_exponential):  # noqa: N801
    """
    Wait strategy that smartly backs-off.

    This strategy first checks the Retry-After response header for a wait time
    indication and uses random exponential backoff if that is not the case.

    """

    def __call__(self, retry_state: tenacity.RetryCallState) -> float:  # noqa: D102
        # When we have a successful outcome, i.e., we received an HTTP response without
        # encountering a Python exception, check if the response headers indicate a wait
        # time; otherwise use the random exponential strategy to determine the wait
        # time.
        if retry_state.outcome and not retry_state.outcome.failed:
            response: httpx.Response = retry_state.outcome.result()
            if (
                response.status_code == httpx.codes.TOO_MANY_REQUESTS
                and (wait := response.headers.get("Retry-After")) is not None
            ):
                return float(wait)

        return super().__call__(retry_state=retry_state)
