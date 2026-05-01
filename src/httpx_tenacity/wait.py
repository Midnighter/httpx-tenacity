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

from datetime import timedelta

import httpx
import tenacity
from tenacity.wait import wait_random_exponential


# We follow tenacity's convention here to use lower snake-case class names for the wait
# strategies.
class smart_wait(wait_random_exponential):  # noqa: N801
    """
    Define a wait strategy that smartly backs-off.

    This strategy first checks HTTP responses for an expected status code (by
    default 429) that indicates that the server is busy. If the status code
    matches, it checks the response header (by default  'Retry-After') for a
    wait time indication. Otherwise, it uses random exponential backoff.

    """

    def __init__(
        self,
        multiplier: float = 1,
        max: timedelta | float = 60,  # noqa: A002
        exp_base: float = 2,
        min: timedelta | float = 0,  # noqa: A002
        status_code: int | tuple[int, ...] = httpx.codes.TOO_MANY_REQUESTS,
        header: str = "Retry-After",
    ) -> None:
        super().__init__(
            multiplier=multiplier,
            max=max,
            exp_base=exp_base,
            min=min,
        )
        self._status_code = status_code
        if isinstance(self._status_code, tuple):
            self._check = self._check_one_of
        else:
            self._check = self._check_singular
        self._header = header

    def _check_singular(self, code: int) -> bool:
        """Check whether the given status code is an expected one."""
        return code == self._status_code

    def _check_one_of(self, code: int) -> bool:
        """Check whether the given status code is one of the expected ones."""
        # The assertion is needed for type checking.
        assert isinstance(self._status_code, tuple)  # noqa: S101
        return code in self._status_code

    def __call__(self, retry_state: tenacity.RetryCallState) -> float:
        """
        Return a wait time in seconds based on response headers or retry state.

        When we have a successful outcome, i.e., we received an HTTP response
        without encountering an exception, and the HTTP status code of the
        response matches the specified status code, check if the response header
        indicates a wait time; otherwise use the random exponential strategy to
        determine the wait time.

        """
        if retry_state.outcome and not retry_state.outcome.failed:
            response: httpx.Response = retry_state.outcome.result()
            if (
                self._check(response.status_code)
                and (wait := response.headers.get(self._header)) is not None
            ):
                return float(wait)

        return super().__call__(retry_state=retry_state)
