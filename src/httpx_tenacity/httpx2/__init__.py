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
Provide the HTTPX2 integration.

Importing this package requires the `httpx2` extra, for example
`pip install "httpx-tenacity[httpx2]"`.

"""

try:
    import httpx2
except ModuleNotFoundError as error:
    if error.name != "httpx2":
        raise
    msg = (
        "The HTTPX2 integration requires the 'httpx2' package. Install it with "
        "`pip install 'httpx-tenacity[httpx2]'`."
    )
    raise ModuleNotFoundError(msg, name="httpx2") from error

from .types import HTTPX2HTTPTransportKeywordArguments
from .async_tenacious_transport import AsyncTenaciousTransport
from .tenacious_transport import TenaciousTransport
