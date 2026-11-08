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
Provide typing examples that the type checkers must reject.

Each HTTP integration only accepts the objects of its own HTTP client. Every line that
ends in an `# expect: <code>` comment is a mixed-client combination or a wrongly
shaped policy, and the comment names the mypy error code it must produce.
`tests/unit/test_typing.py` fails if mypy reports any other error or misses an
expected one.

"""

from __future__ import annotations

import httpx
import httpx2
import tenacity

from httpx_tenacity import SmartRetryPolicy
from httpx_tenacity.httpx import (
    AsyncTenaciousTransport as HTTPXAsyncTransport,
)
from httpx_tenacity.httpx import (
    HTTPXHTTPTransportKeywordArguments as HTTPXKeywordArguments,
)
from httpx_tenacity.httpx import (
    TenaciousTransport as HTTPXTransport,
)
from httpx_tenacity.httpx2 import (
    AsyncTenaciousTransport as HTTPX2AsyncTransport,
)
from httpx_tenacity.httpx2 import (
    HTTPX2HTTPTransportKeywordArguments as HTTPX2KeywordArguments,
)
from httpx_tenacity.httpx2 import (
    TenaciousTransport as HTTPX2Transport,
)


class PolicyWithoutKeywords:
    """A policy whose `create` method lacks the keyword-only parameters."""

    def create(self, retrying_class: type[tenacity.Retrying]) -> tenacity.Retrying:
        """Create a retrying instance."""
        return retrying_class()


class PolicyWithWrongReturn:
    """A policy whose `create` method returns something other than a retrying."""

    def create(
        self,
        retrying_class: type[tenacity.Retrying],  # noqa: ARG002
        *,
        request_error: type[Exception],  # noqa: ARG002
        logger: object,  # noqa: ARG002
    ) -> str:
        """Return a string."""
        return "retrying"


HTTPXTransport(
    retry=tenacity.Retrying(),
    transport=httpx2.HTTPTransport(),  # expect: arg-type
)
HTTPX2Transport(
    retry=tenacity.Retrying(),
    transport=httpx.HTTPTransport(),  # expect: arg-type
)
HTTPXAsyncTransport(
    retry=tenacity.AsyncRetrying(),
    transport=httpx2.AsyncHTTPTransport(),  # expect: arg-type
)
HTTPX2AsyncTransport(
    retry=tenacity.AsyncRetrying(),
    transport=httpx.AsyncHTTPTransport(),  # expect: arg-type
)

HTTPXTransport.create(limits=httpx2.Limits())  # expect: arg-type
HTTPX2Transport.create(limits=httpx.Limits())  # expect: arg-type
HTTPXAsyncTransport.create(limits=httpx2.Limits())  # expect: arg-type
HTTPX2AsyncTransport.create(limits=httpx.Limits())  # expect: arg-type
HTTPXTransport.create(proxy=httpx2.Proxy("http://localhost"))  # expect: arg-type
HTTPX2Transport.create(proxy=httpx.Proxy("http://localhost"))  # expect: arg-type
HTTPXAsyncTransport.create(proxy=httpx2.URL("http://localhost"))  # expect: arg-type
HTTPX2AsyncTransport.create(proxy=httpx.URL("http://localhost"))  # expect: arg-type

HTTPX_ARGUMENTS: HTTPXKeywordArguments = {
    "limits": httpx2.Limits(),  # expect: typeddict-item
}
HTTPX2_ARGUMENTS: HTTPX2KeywordArguments = {
    "limits": httpx.Limits(),  # expect: typeddict-item
}

httpx.Client(transport=HTTPX2Transport.create())  # expect: arg-type
httpx2.Client(transport=HTTPXTransport.create())  # expect: arg-type
httpx.AsyncClient(transport=HTTPX2AsyncTransport.create())  # expect: arg-type
httpx2.AsyncClient(transport=HTTPXAsyncTransport.create())  # expect: arg-type

HTTPXTransport(
    retry=tenacity.AsyncRetrying(),  # expect: arg-type
    transport=httpx.HTTPTransport(),
)
HTTPX2Transport(
    retry=tenacity.AsyncRetrying(),  # expect: arg-type
    transport=httpx2.HTTPTransport(),
)
HTTPXAsyncTransport(
    retry=tenacity.Retrying(),  # expect: arg-type
    transport=httpx.AsyncHTTPTransport(),
)
HTTPX2AsyncTransport(
    retry=tenacity.Retrying(),  # expect: arg-type
    transport=httpx2.AsyncHTTPTransport(),
)
HTTPXTransport(
    retry=tenacity.Retrying(),
    transport=httpx.AsyncHTTPTransport(),  # expect: arg-type
)
HTTPX2AsyncTransport(
    retry=tenacity.AsyncRetrying(),
    transport=httpx2.HTTPTransport(),  # expect: arg-type
)

HTTPXTransport.create(policy=PolicyWithoutKeywords())  # expect: arg-type
HTTPX2AsyncTransport.create(policy=PolicyWithoutKeywords())  # expect: arg-type
HTTPXAsyncTransport.create(policy=PolicyWithWrongReturn())  # expect: arg-type
HTTPX2Transport.create(policy=SmartRetryPolicy().create)  # expect: arg-type
