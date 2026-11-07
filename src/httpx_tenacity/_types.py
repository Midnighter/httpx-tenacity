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


"""Provide types that do not depend on an HTTP client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Mapping


class Response(Protocol):
    """
    Describe the parts of an HTTP response that the retry helpers read.

    Responses of different HTTP clients are distinct classes. This protocol lets the
    client-independent code accept all of them.

    """

    @property
    def status_code(self) -> int:
        """The HTTP status code."""

    @property
    def headers(self) -> Mapping[str, str]:
        """The response headers."""
