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
Test code examples in documentation.

We assume that examples in the documentation are at a similar level as acceptance tests.
Every Python code block of `README.md` and `docs/**/*.md` runs on its own as a complete
script in a fresh namespace, so each block has to restate its imports. Asynchronous
examples run themselves with `anyio.run(main)`, which is why the test is synchronous.

The `HTTPTransport` and `AsyncHTTPTransport` of HTTPX and HTTPX2 are replaced by
factories that return that client's `MockTransport` answering 200, so that no example
touches the network. The factories bind their arguments to the signature of the real
transport, so that documented options which the real transport does not accept fail the
test.

Which HTTP client an example uses is explicit in its imports. Running the examples
already catches one that mixes the clients, and `test_examples_exist_for_both_backends`
additionally requires that the documents keep showing both clients.

"""

from __future__ import annotations

import inspect
import re
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import httpx2
import pytest
from mktestdocs import grab_code_blocks


if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable
    from types import ModuleType


ROOT_DIR = Path(__file__).parents[2]
DOCS = sorted([*(ROOT_DIR / "docs").glob("**/*.md"), ROOT_DIR / "README.md"])
EXAMPLES = [
    pytest.param(
        block,
        id=f"{document.relative_to(ROOT_DIR).as_posix()}::{index}",
    )
    for document in DOCS
    for index, block in enumerate(grab_code_blocks(document.read_text()))
]
# The clients whose examples each document must show. `README.md` is rendered by GitHub
# without tabs, so it deliberately has only an HTTPX example and describes HTTPX2 in
# prose.
BACKENDS_PER_DOCUMENT = {
    "README.md": {"httpx"},
    "docs/index.md": {"httpx", "httpx2"},
    "docs/tutorial.md": {"httpx", "httpx2"},
}
# `httpx2?` followed by a word boundary matches `httpx2` whole, so that an `httpx2`
# import is never mistaken for `httpx`, and `httpx_tenacity` itself does not match.
CLIENT_IMPORT = re.compile(
    r"^\s*(?:import|from)\s+(?:httpx_tenacity\.)?(httpx2?)\b",
    re.MULTILINE,
)


def _backends_used(block: str) -> set[str]:
    """Return the HTTP clients that a code block imports."""
    return set(CLIENT_IMPORT.findall(block))


def _mock_transport_factory(
    client: ModuleType,
    transport_class: type[object],
) -> Callable[..., object]:
    """Create a replacement for a network transport of a client that answers 200."""
    signature = inspect.signature(transport_class)

    def factory(*args: object, **kwargs: object) -> object:
        # Binding the arguments rejects those that the real transport does not take.
        signature.bind(*args, **kwargs)
        return client.MockTransport(
            lambda request: client.Response(200, request=request),
        )

    return factory


@pytest.fixture
def mock_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the network transports of HTTPX and HTTPX2 with mock transports."""
    for client in (httpx, httpx2):
        for name in ("HTTPTransport", "AsyncHTTPTransport"):
            monkeypatch.setattr(
                client,
                name,
                _mock_transport_factory(client, getattr(client, name)),
            )


@pytest.mark.usefixtures("mock_network")
@pytest.mark.parametrize("block", EXAMPLES)
def test_document_examples_independently(block: str):
    """
    Run an individual code example from a document.

    Each code block must be completely independent of each other, for example, imports
    must be restated within each block. Asynchronous examples run themselves.

    """
    exec(block, {"__name__": "__main__"})  # noqa: S102


@pytest.mark.parametrize(
    ("document", "expected"),
    BACKENDS_PER_DOCUMENT.items(),
    ids=BACKENDS_PER_DOCUMENT,
)
def test_examples_exist_for_both_backends(document: str, expected: set[str]):
    """
    Require examples for each HTTP client in the listed documents.

    Only blocks that import a single client count, so that an example which shows both
    clients together cannot stand in for the missing example of either.

    """
    shown: set[str] = set()

    for block in grab_code_blocks((ROOT_DIR / document).read_text()):
        used = _backends_used(block)
        if len(used) == 1:
            shown |= used

    assert shown == expected
