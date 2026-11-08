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

from typing import TYPE_CHECKING, Protocol, TypeAlias


if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Mapping

# Fallback for Pyodide HTTPX. See: https://github.com/Midnighter/httpx-tenacity/pull/10#issuecomment-3241566927
SocketOption: TypeAlias = (
    tuple[int, int, int]
    | tuple[int, int, bytes | bytearray]
    | tuple[int, int, None, int]
)

# We redefine the following type from the private `_types` modules of HTTPX and
# HTTPX2 to avoid a dependency on them. It is identical for both clients. It would
# be better if they exposed it publicly, but it is unlikely to change often. Thus we
# consider it acceptable to redefine it here for type hinting purposes.
CertTypes: TypeAlias = str | tuple[str, str] | tuple[str, str, str]


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
