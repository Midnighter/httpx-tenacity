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


"""Provide custom retry callback functions."""

import httpx


HTTP_SERVER_ERROR_UPPER_LIMIT = 599


def is_server_side_issue(response: httpx.Response) -> bool:
    """
    Return whether the response indicates a server side issue.

    A server side issue is defined as either an HTTP server error code (500 - 599) or
    too many requests (429).

    """
    if (
        httpx.codes.INTERNAL_SERVER_ERROR
        <= response.status_code
        <= HTTP_SERVER_ERROR_UPPER_LIMIT
    ):
        return True

    return response.status_code == httpx.codes.TOO_MANY_REQUESTS
