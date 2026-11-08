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


"""
Provide the HTTPX integration.

Importing this package requires the `httpx` extra, for example
`pip install "httpx-tenacity[httpx]"`.

"""

try:
    import httpx
except ModuleNotFoundError as error:
    if error.name != "httpx":
        raise
    msg = (
        "The HTTPX integration requires the 'httpx' package. Install it with "
        "`pip install 'httpx-tenacity[httpx]'`."
    )
    raise ModuleNotFoundError(msg, name="httpx") from error

from .types import HTTPXHTTPTransportKeywordArguments
from .async_tenacious_transport import AsyncTenaciousTransport
from .tenacious_transport import TenaciousTransport
